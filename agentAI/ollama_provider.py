"""
Implementación del proveedor LLM usando Ollama
"""

import os
import json
import requests
from typing import Dict, Any
from llm_provider import LLMProvider


class OllamaProvider(LLMProvider):
    """Implementación concreta usando Ollama"""
    
    def __init__(self, api_url: str = None, model: str = "llama2"):
        """
        Inicializa el proveedor Ollama.
        
        Args:
            api_url: URL base de la API de Ollama (default: http://localhost:11434)
            model: Modelo a usar (default: llama2)
        """
        self.api_url = (api_url or os.getenv("OLLAMA_API_URL", "http://localhost:11434")).rstrip('/')
        self.model = model or os.getenv("OLLAMA_MODEL", "llama2")
        
        # Verificar que Ollama esté disponible
        try:
            health_response = requests.get(f"{self.api_url}/api/tags", timeout=5)
            if health_response.status_code != 200:
                print(f"⚠ Advertencia: No se pudo verificar Ollama en {self.api_url}")
        except requests.exceptions.ConnectionError:
            print(f"⚠ Advertencia: No se pudo conectar con Ollama en {self.api_url}. Asegúrate de que Ollama esté corriendo.")
        except Exception as e:
            print(f"⚠ Advertencia al verificar Ollama: {str(e)}")
    
    def _make_request(self, messages: list, temperature: float = 0.1, format: str = None) -> str:
        """
        Realiza una petición a la API de Ollama.
        
        Args:
            messages: Lista de mensajes en formato OpenAI
            temperature: Temperatura para la generación
            format: Formato de respuesta (opcional, para JSON)
            
        Returns:
            Contenido de la respuesta
        """
        # Convertir mensajes de formato OpenAI a formato Ollama
        # Ollama espera un campo "prompt" o "messages"
        # Para modelos más recientes, usa "messages", para otros usa "prompt"
        
        # Construir el prompt combinando system y user messages
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        full_prompt = "\n\n".join(prompt_parts)
        
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        # Si se requiere formato JSON
        if format == "json":
            payload["format"] = "json"
        
        try:
            # Intentar endpoint /api/generate (más común en Ollama)
            endpoint = f"{self.api_url}/api/generate"
            response = requests.post(
                endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120  # Ollama puede tardar más en responder
            )
            
            if response.status_code == 200:
                result = response.json()
                if "response" in result:
                    return result["response"]
                else:
                    raise Exception(f"Respuesta inesperada de Ollama: {result}")
            else:
                # Intentar endpoint /api/chat (para modelos más recientes)
                endpoint = f"{self.api_url}/api/chat"
                chat_payload = {
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature
                    }
                }
                
                if format == "json":
                    chat_payload["format"] = "json"
                
                chat_response = requests.post(
                    endpoint,
                    json=chat_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=120
                )
                
                if chat_response.status_code == 200:
                    result = chat_response.json()
                    if "message" in result and "content" in result["message"]:
                        return result["message"]["content"]
                    elif "response" in result:
                        return result["response"]
                    else:
                        raise Exception(f"Respuesta inesperada de Ollama: {result}")
                else:
                    raise Exception(f"Error {response.status_code}: {response.text}")
                    
        except requests.exceptions.ConnectionError:
            raise Exception(f"No se pudo conectar con Ollama en {self.api_url}. Asegúrate de que Ollama esté corriendo.")
        except requests.exceptions.Timeout:
            raise Exception("Timeout al comunicarse con Ollama. El modelo puede estar tardando mucho en responder.")
        except Exception as e:
            raise Exception(f"Error al comunicarse con Ollama: {str(e)}")
    

    def extract_contract_data(self, text: str) -> Dict[str, Any]:
        """
        Extrae y normaliza los datos del contrato desde texto libre usando Ollama.
        """
        system_prompt = """Eres un asistente experto en extraer información de contratos desde texto libre.
Tu tarea es analizar el texto proporcionado y extraer la siguiente información estructurada:

1. PROVEEDOR (Contratista):
   - nombre: Nombre completo de la persona
   - documento: Número de documento de identidad (INCLUYE el prefijo si está presente: CC, CE, TI, NIT, etc. Ejemplo: "CC 52.871.993" no solo "52.871.993")
   - correo: Correo electrónico
   - telefono: Número de teléfono

2. CONTRATO:
   - proyecto: Nombre del proyecto
   - servicio: Descripción del servicio
   - valor: Valor numérico (solo el número)
   - moneda: Moneda (USD, COP, etc.)
   - fecha_inicio: Fecha de inicio en formato YYYY-MM-DD
   - fecha_fin: Fecha de fin en formato YYYY-MM-DD
   - entregables: Lista de entregables (array de strings)

3. CONTRATANTE:
   - empresa: Nombre de la empresa
   - nit: NIT de la empresa
   - representante_legal: Nombre del representante legal
   - cargo: Cargo del representante legal
   - direccion: Dirección de la empresa
   - correo: Correo electrónico de la empresa

IMPORTANTE:
- Si algún campo no está presente en el texto, déjalo como null o string vacío
- Normaliza las fechas al formato YYYY-MM-DD
- Extrae valores numéricos sin símbolos de moneda
- Para documentos de identidad: SI el texto menciona "CC", "CE", "TI", "NIT" u otro prefijo antes del número, INCLÚYELO en el campo documento (ejemplo: "CC 52.871.993" no solo "52.871.993")
- Retorna SOLO un JSON válido, sin texto adicional
- Si no puedes determinar un valor, usa null"""

        user_prompt = f"""Extrae la información del siguiente texto sobre un contrato:

{text}

Retorna SOLO un JSON con esta estructura exacta:
{{
    "proveedor": {{
        "nombre": "...",
        "documento": "...",
        "correo": "...",
        "telefono": "..."
    }},
    "contrato": {{
        "proyecto": "...",
        "servicio": "...",
        "valor": 0,
        "moneda": "USD",
        "fecha_inicio": "YYYY-MM-DD",
        "fecha_fin": "YYYY-MM-DD",
        "entregables": []
    }},
    "contratante": {{
        "empresa": "...",
        "nit": "...",
        "representante_legal": "...",
        "cargo": "...",
        "direccion": "...",
        "correo": "..."
    }}
}}"""

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            content = self._make_request(
                messages=messages,
                temperature=0.1,
                format="json"
            )
            
            # Limpiar el contenido si tiene markdown code blocks
            if content.strip().startswith("```"):
                # Extraer JSON de code blocks
                lines = content.strip().split("\n")
                json_lines = []
                in_json = False
                for line in lines:
                    if line.strip().startswith("```"):
                        in_json = not in_json
                        continue
                    if in_json or (not content.strip().startswith("```") and line.strip()):
                        json_lines.append(line)
                content = "\n".join(json_lines)
            
            # Intentar parsear el JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                # Si falla, intentar extraer JSON del texto
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    raise Exception(f"No se pudo extraer JSON de la respuesta: {content[:200]}")
            
            # Normalizar valores
            if "contrato" in data and "valor" in data["contrato"]:
                try:
                    valor = data["contrato"]["valor"]
                    if isinstance(valor, str):
                        # Limpiar string de valor
                        valor = valor.replace(",", "").replace("$", "").replace("USD", "").strip()
                    data["contrato"]["valor"] = float(valor)
                except:
                    data["contrato"]["valor"] = 0
            
            # Normalizar documento: asegurar que incluya prefijo si es necesario
            if "proveedor" in data and "documento" in data["proveedor"]:
                documento = str(data["proveedor"]["documento"]).strip()
                # Si el documento no tiene prefijo pero debería tenerlo (solo números y puntos)
                # y el texto original mencionaba CC, agregarlo
                if documento and not any(prefijo in documento.upper() for prefijo in ["CC", "CE", "TI", "NIT", "PASAPORTE"]):
                    # Si solo tiene números y puntos, podría necesitar prefijo CC
                    # Pero no lo agregamos automáticamente, confiamos en el LLM
                    pass
            
            return data
            
        except json.JSONDecodeError as e:
            raise Exception(f"Error al parsear respuesta de Ollama: {str(e)}. Respuesta recibida: {content[:200]}")
        except Exception as e:
            raise Exception(f"Error al extraer datos con Ollama: {str(e)}")
    
    
    def generate_question(self, missing_fields: list, errors: list) -> str:
        """
        Genera una pregunta natural para solicitar información faltante.
        """
        system_prompt = """Eres un asistente que ayuda a completar información de contratos.
Tu tarea es generar una pregunta amigable y natural en español que solicite la información faltante o incorrecta.
La pregunta debe ser clara y en lenguaje natural (no mencionar campos técnicos)."""

        missing_info = []
        if missing_fields:
            missing_info.append(f"Campos faltantes: {', '.join(missing_fields)}")
        if errors:
            missing_info.append(f"Errores encontrados: {', '.join(errors)}")
        
        user_prompt = f"""Basándote en la siguiente información, genera una pregunta natural en español para solicitar mas texto relacionado a los campos faltantes:

{chr(10).join(missing_info)}

IMPORTANTE:
- La pregunta debe ser en lenguaje natural, como si hablaras con una persona
- No uses términos técnicos como "proveedor.nombre" o "contrato.valor"
- No preguntes por campos específicos, pregunta de forma general para que el usuario redacte mas texto que pueda contener la información necesaria para completar el contrato
- Mantén un tono profesional pero amigable
- Retorna SOLO la pregunta, sin explicaciones adicionales"""

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            content = self._make_request(
                messages=messages,
                temperature=0.7
            )
            
            # Limpiar la respuesta si tiene markdown o formato extra
            content = content.strip()
            if content.startswith('"') and content.endswith('"'):
                content = content[1:-1]
            
            return content
            
        except Exception as e:
            # Fallback a pregunta genérica
            return f"Necesito más información para completar el contrato. Por favor, proporciona: {', '.join(missing_fields[:3])}."

