"""
Agente AI - Servicio que procesa texto libre y gestiona el flujo de contratos
Puerto: 8082
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from typing import Dict, Any
from dotenv import load_dotenv
from openai_provider import OpenAIProvider
from ollama_provider import OllamaProvider
from llm_provider import LLMProvider

# Cargar variables de entorno desde archivo .env
load_dotenv()

app = Flask(__name__)
CORS(app)

# URL del servidor MCP
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8081")

# Inicializar proveedor LLM (por defecto OpenAI)
llm_provider: LLMProvider = None


def init_llm_provider():
    """Inicializa el proveedor LLM según configuración"""
    global llm_provider
    
    provider_type = os.getenv("LLM_PROVIDER", "openai").lower()
    
    if provider_type == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY no está configurada. Configúrala como variable de entorno.")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        llm_provider = OpenAIProvider(api_key=api_key, model=model)
    elif provider_type == "ollama":
        api_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "mistral")
        llm_provider = OllamaProvider(api_url=api_url, model=model)
    else:
        raise ValueError(f"Proveedor LLM no soportado: {provider_type}. Opciones: 'openai' o 'ollama'")


@app.route('/process_contract', methods=['POST'])
def process_contract():
    """
    Endpoint principal que procesa texto libre, valida y genera el contrato.
    Flujo 1: Extracción → Validación → Generación de documento
    
    Request body:
    {
        "text": "Texto libre con la información del contrato"
    }
    
    Response:
    {
        "status": "success|validation_error|error",
        "message": "...",
        "data": {...},
        "document": "...", (solo si status es success)
        "question": "..." (solo si hay errores de validación)
    }
    """
    try:
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({
                "status": "error",
                "message": "No se proporcionó el texto del contrato",
                "data": None
            }), 400
        
        text = data.get("text", "").strip()
        if not text:
            return jsonify({
                "status": "error",
                "message": "El texto del contrato está vacío",
                "data": None
            }), 400
        
        # Paso 1: Extraer datos usando LLM
        print(f"[AGENT] Extrayendo datos del texto: {text[:100]}...")
        try:
            extracted_data = llm_provider.extract_contract_data(text)
            print(f"[AGENT] Datos extraídos: {extracted_data}")
        except Exception as e:
            print(f"[AGENT] Error al extraer datos: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Error al extraer datos del texto: {str(e)}",
                "data": None
            }), 500
        
        # Paso 2: Validar contra el servidor MCP
        print(f"[AGENT] Validando datos con MCP...")
        try:
            validation_response = requests.post(
                f"{MCP_SERVER_URL}/validate_request",
                json=extracted_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
        except requests.exceptions.ConnectionError:
            return jsonify({
                "status": "error",
                "message": f"No se pudo conectar con el servidor MCP en {MCP_SERVER_URL}",
                "data": extracted_data
            }), 503
        except requests.exceptions.Timeout:
            return jsonify({
                "status": "error",
                "message": "Timeout al comunicarse con el servidor MCP durante la validación",
                "data": extracted_data
            }), 504
        
        if validation_response.status_code != 200:
            return jsonify({
                "status": "error",
                "message": f"Error al validar: {validation_response.text}",
                "data": extracted_data
            }), 500
        
        validation_result = validation_response.json()
        print(f"[AGENT] Resultado de validación: {validation_result}")
        
        # Paso 3: Si la validación falla, generar pregunta
        if not validation_result.get("valid", False):
            errors = validation_result.get("errors", [])
            missing_fields = validation_result.get("missing_fields", [])
            
            print(f"[AGENT] Validación fallida. Errores: {errors}, Faltantes: {missing_fields}")
            
            try:
                question = llm_provider.generate_question(missing_fields, errors)
            except Exception as e:
                print(f"[AGENT] Error al generar pregunta: {str(e)}")
                question = f"Necesito más información para completar el contrato. Por favor, proporciona: {', '.join(missing_fields[:3])}."
            
            return jsonify({
                "status": "validation_error",
                "message": "La información proporcionada no es completa o correcta",
                "data": extracted_data,
                "validation_result": validation_result,
                "question": question
            }), 200
        
        # Paso 4: Si la validación es exitosa, generar el contrato
        print(f"[AGENT] Validación exitosa. Generando contrato...")
        try:
            document_response = requests.post(
                f"{MCP_SERVER_URL}/generate_document",
                json=extracted_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
        except requests.exceptions.ConnectionError:
            return jsonify({
                "status": "error",
                "message": f"No se pudo conectar con el servidor MCP en {MCP_SERVER_URL}",
                "data": extracted_data
            }), 503
        except requests.exceptions.Timeout:
            return jsonify({
                "status": "error",
                "message": "Timeout al comunicarse con el servidor MCP durante la generación del documento",
                "data": extracted_data
            }), 504
        
        if document_response.status_code != 200:
            return jsonify({
                "status": "error",
                "message": f"Error al generar el documento: {document_response.text}",
                "data": extracted_data
            }), 500
        
        document_result = document_response.json()
        contract_document = document_result.get("document", "")
        
        print(f"[AGENT] Contrato generado exitosamente")
        
        return jsonify({
            "status": "success",
            "message": "Contrato procesado y generado exitosamente",
            "data": extracted_data,
            "document": contract_document
        }), 200
        
    except Exception as e:
        print(f"[AGENT] Error inesperado: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error al procesar el contrato: {str(e)}",
            "data": None
        }), 500


@app.route('/send_contract_email', methods=['POST'])
def send_contract_email():
    """
    Endpoint para enviar el contrato por correo electrónico.
    Flujo 2: Recibe documento y firma → Envía por correo
    
    Request body:
    {
        "document": "Contenido del contrato en formato Markdown o texto",
        "firma": "Información de la firma (opcional)"
    }
    
    Response:
    {
        "status": "success|error",
        "message": "...",
        "email_status": {...}
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "No se recibieron datos",
                "email_status": None
            }), 400
        
        contract_document = data.get("document", "").strip()
        if not contract_document:
            return jsonify({
                "status": "error",
                "message": "No se proporcionó el documento del contrato",
                "email_status": None
            }), 400
        
        firma = data.get("firma", "")
        print(f"[AGENT] Enviando contrato por correo. Firma: {firma[:50] if firma else 'No proporcionada'}...")
        
        # Paso 5: Enviar por correo
        try:
            email_payload = {
                "document": contract_document,
                "recipient": "jairo@mantisapp.co"
            }
            # Agregar firma si se proporciona
            if firma:
                email_payload["firma"] = firma
            
            email_response = requests.post(
                f"{MCP_SERVER_URL}/send_email",
                json=email_payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
        except requests.exceptions.ConnectionError:
            return jsonify({
                "status": "error",
                "message": f"No se pudo conectar con el servidor MCP en {MCP_SERVER_URL}",
                "email_status": None
            }), 503
        except requests.exceptions.Timeout:
            return jsonify({
                "status": "error",
                "message": "Timeout al comunicarse con el servidor MCP durante el envío del correo",
                "email_status": None
            }), 504
        
        if email_response.status_code != 200:
            return jsonify({
                "status": "error",
                "message": f"Error al enviar el correo: {email_response.text}",
                "email_status": None
            }), 500
        
        email_result = email_response.json()
        
        print(f"[AGENT] Correo enviado exitosamente")
        
        return jsonify({
            "status": "success",
            "message": "Contrato enviado por correo exitosamente",
            "email_status": email_result
        }), 200
        
    except Exception as e:
        print(f"[AGENT] Error inesperado al enviar correo: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error al enviar el correo: {str(e)}",
            "email_status": None
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Endpoint de salud del servidor"""
    try:
        # Verificar conexión con MCP
        mcp_health = requests.get(f"{MCP_SERVER_URL}/health", timeout=5)
        mcp_status = "connected" if mcp_health.status_code == 200 else "disconnected"
    except:
        mcp_status = "disconnected"
    
    return jsonify({
        "status": "healthy",
        "service": "AI Agent",
        "port": 8082,
        "llm_provider": os.getenv("LLM_PROVIDER", "openai"),
        "mcp_server_status": mcp_status,
        "mcp_server_url": MCP_SERVER_URL
    }), 200


if __name__ == '__main__':
    print("Iniciando Agente AI en puerto 8082...")
    
    try:
        init_llm_provider()
        provider = os.getenv('LLM_PROVIDER', 'openai')
        print(f"Proveedor LLM inicializado: {provider}")
        if provider == "ollama":
            print(f"  - API URL: {os.getenv('OLLAMA_API_URL', 'http://localhost:11434')}")
            print(f"  - Modelo: {os.getenv('OLLAMA_MODEL', 'mistral')}")
    except Exception as e:
        print(f"ERROR: No se pudo inicializar el proveedor LLM: {str(e)}")
        provider = os.getenv('LLM_PROVIDER', 'openai')
        if provider == "openai":
            print("Asegúrate de configurar OPENAI_API_KEY como variable de entorno")
        elif provider == "ollama":
            print("Asegúrate de que Ollama esté corriendo en http://localhost:11434")
            print("Puedes configurar OLLAMA_API_URL y OLLAMA_MODEL si usas una configuración diferente")
        exit(1)
    
    print(f"Servidor MCP configurado en: {MCP_SERVER_URL}")
    app.run(host='0.0.0.0', port=8082, debug=True)

