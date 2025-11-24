"""
Servidor MCP - Model Context Protocol Server
Expone endpoints para validación, generación de documentos y envío de correos.
Puerto: 8081
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# Datos oficiales del caso (única fuente de verdad)
OFFICIAL_DATA = {
    "proveedor": {
        "nombre": "Laura Sofía Martínez Gómez",
        "documento": "CC 52.871.993",
        "correo": "laura.martinez@example.com",
        "telefono": "+57 310 555 9080"
    },
    "contrato": {
        "proyecto": "Optimización del Proceso de Conciliación",
        "servicio": "Consultoría en automatización de procesos y conciliación contable",
        "valor": 4800,
        "moneda": "USD",
        "fecha_inicio": "2026-01-15",
        "fecha_fin": "2026-04-15",
        "entregables": [
            "Diagnóstico inicial",
            "plan de automatización",
            "piloto",
            "informe final"
        ]
    },
    "contratante": {
        "empresa": "TechNova S.A.S.",
        "nit": "901.456.789-1",
        "representante_legal": "Carlos Eduardo Rincón",
        "cargo": "CEO",
        "direccion": "Cra. 45 #100–32, Bogotá",
        "correo": "contratos@technova.co"
    }
}


def normalize_text(text):
    """Normaliza texto para comparación (minúsculas, sin espacios extra)"""
    if not text:
        return ""
    return " ".join(str(text).lower().split())


def normalize_date(date_str):
    """Normaliza una fecha a formato YYYY-MM-DD"""
    if not date_str:
        return None
    try:
        # Si ya está en formato YYYY-MM-DD
        if len(str(date_str)) == 10 and str(date_str)[4] == '-' and str(date_str)[7] == '-':
            return str(date_str)
        # Intentar parsear diferentes formatos
        from datetime import datetime
        # Intentar formatos comunes
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']:
            try:
                dt = datetime.strptime(str(date_str), fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue
        return str(date_str)
    except:
        return str(date_str)


def normalize_document(doc_str):
    """
    Normaliza un documento de identidad para comparación.
    Extrae solo los números y puntos, ignorando prefijos como CC, CE, TI, etc.
    """
    if not doc_str:
        return ""
    # Convertir a string y remover espacios
    doc = str(doc_str).strip()
    # Remover prefijos comunes (CC, CE, TI, NIT, etc.) y espacios
    import re
    # Remover prefijos al inicio
    doc = re.sub(r'^(CC|CE|TI|NIT|PASAPORTE|PA)\s*', '', doc, flags=re.IGNORECASE)
    # Normalizar espacios y mantener solo números, puntos y guiones
    doc = re.sub(r'[^\d.\-]', '', doc)
    return doc.strip()


def compare_field(extracted, official, field_name, tolerance=0.8):
    """
    Compara un campo extraído con el oficial.
    Retorna (is_valid, error_message)
    """
    if not extracted:
        return False, f"Campo '{field_name}' no proporcionado"
    
    # Para fechas, normalizar primero
    if field_name in ["fecha_inicio", "fecha_fin"]:
        extracted_norm = normalize_date(extracted)
        official_norm = normalize_date(official)
        if extracted_norm == official_norm:
            return True, None
        return False, f"Campo '{field_name}' no coincide. Esperado: '{official}', Recibido: '{extracted}'"
    
    # Para documentos, normalizar removiendo prefijos
    if field_name == "documento":
        extracted_norm = normalize_document(extracted)
        official_norm = normalize_document(official)
        if extracted_norm == official_norm:
            return True, None
        # También comparar el texto normalizado completo como fallback
        extracted_text = normalize_text(extracted)
        official_text = normalize_text(official)
        if extracted_text == official_text:
            return True, None
        return False, f"Campo '{field_name}' no coincide. Esperado: '{official}', Recibido: '{extracted}'"
    
    extracted_norm = normalize_text(extracted)
    official_norm = normalize_text(official)
    
    # Comparación exacta o por similitud
    if extracted_norm == official_norm:
        return True, None
    
    # Para nombres, permitir coincidencias parciales
    if field_name in ["nombre", "proveedor", "representante_legal"]:
        if official_norm in extracted_norm or extracted_norm in official_norm:
            return True, None
    
    # Para valores numéricos
    if field_name == "valor":
        try:
            extracted_val = float(str(extracted).replace(",", "").replace("$", "").replace("USD", "").strip())
            official_val = float(official)
            if abs(extracted_val - official_val) < 1:
                return True, None
        except:
            pass
    
    # Para entregables, verificar que todos estén presentes
    if field_name == "entregables":
        if isinstance(extracted, list) and isinstance(official, list):
            extracted_lower = [normalize_text(e) for e in extracted]
            official_lower = [normalize_text(o) for o in official]
            # Verificar que todos los entregables oficiales estén presentes
            all_present = all(any(o in e or e in o for e in extracted_lower) for o in official_lower)
            if all_present:
                return True, None
    
    return False, f"Campo '{field_name}' no coincide. Esperado: '{official}', Recibido: '{extracted}'"


@app.route('/validate_request', methods=['POST'])
def validate_request():
    """
    Valida los datos extraídos contra los datos oficiales.
    
    Request body:
    {
        "proveedor": {...},
        "contrato": {...},
        "contratante": {...}
    }
    
    Response:
    {
        "valid": true/false,
        "errors": [...],
        "missing_fields": [...],
        "message": "..."
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "valid": False,
                "errors": ["No se recibieron datos"],
                "missing_fields": [],
                "message": "Datos de entrada vacíos"
            }), 400
        
        errors = []
        missing_fields = []
        
        # Validar proveedor
        proveedor_data = data.get("proveedor", {})
        if not proveedor_data:
            missing_fields.append("proveedor")
        else:
            for field, official_value in OFFICIAL_DATA["proveedor"].items():
                extracted_value = proveedor_data.get(field)
                if not extracted_value:
                    missing_fields.append(f"proveedor.{field}")
                else:
                    is_valid, error_msg = compare_field(extracted_value, official_value, field)
                    if not is_valid:
                        errors.append(error_msg)
        
        # Validar contrato
        contrato_data = data.get("contrato", {})
        if not contrato_data:
            missing_fields.append("contrato")
        else:
            for field, official_value in OFFICIAL_DATA["contrato"].items():
                extracted_value = contrato_data.get(field)
                if not extracted_value:
                    missing_fields.append(f"contrato.{field}")
                else:
                    is_valid, error_msg = compare_field(extracted_value, official_value, field)
                    if not is_valid:
                        errors.append(error_msg)
        
        # Validar contratante
        contratante_data = data.get("contratante", {})
        if not contratante_data:
            missing_fields.append("contratante")
        else:
            for field, official_value in OFFICIAL_DATA["contratante"].items():
                extracted_value = contratante_data.get(field)
                if not extracted_value:
                    missing_fields.append(f"contratante.{field}")
                else:
                    is_valid, error_msg = compare_field(extracted_value, official_value, field)
                    if not is_valid:
                        errors.append(error_msg)
        
        is_valid = len(errors) == 0 and len(missing_fields) == 0
        
        return jsonify({
            "valid": is_valid,
            "errors": errors,
            "missing_fields": missing_fields,
            "message": "Validación exitosa" if is_valid else "Se encontraron errores o campos faltantes"
        }), 200
        
    except Exception as e:
        return jsonify({
            "valid": False,
            "errors": [str(e)],
            "missing_fields": [],
            "message": f"Error en la validación: {str(e)}"
        }), 500


@app.route('/generate_document', methods=['POST'])
def generate_document():
    """
    Genera un contrato en formato Markdown.
    
    Request body:
    {
        "proveedor": {...},
        "contrato": {...},
        "contratante": {...}
    }
    
    Response:
    {
        "document": "...",
        "format": "markdown",
        "status": "success"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "document": "",
                "format": "markdown",
                "status": "error",
                "message": "No se recibieron datos"
            }), 400
        
        proveedor = data.get("proveedor", {})
        contrato = data.get("contrato", {})
        contratante = data.get("contratante", {})
        
        # Generar contrato en Markdown
        document = f"""# CONTRATO DE PRESTACIÓN DE SERVICIOS

## PARTES

### CONTRATANTE
**Empresa:** {contratante.get('empresa', 'N/A')}  
**NIT:** {contratante.get('nit', 'N/A')}  
**Representante Legal:** {contratante.get('representante_legal', 'N/A')} ({contratante.get('cargo', 'N/A')})  
**Dirección:** {contratante.get('direccion', 'N/A')}  
**Correo:** {contratante.get('correo', 'N/A')}

### CONTRATISTA (PROVEEDOR)
**Nombre:** {proveedor.get('nombre', 'N/A')}  
**Documento:** {proveedor.get('documento', 'N/A')}  
**Correo:** {proveedor.get('correo', 'N/A')}  
**Teléfono:** {proveedor.get('telefono', 'N/A')}

---

## OBJETO DEL CONTRATO

El presente contrato tiene por objeto la prestación del siguiente servicio:

**Proyecto:** {contrato.get('proyecto', 'N/A')}  
**Servicio:** {contrato.get('servicio', 'N/A')}

---

## DURACIÓN Y VALOR

**Fecha de Inicio:** {contrato.get('fecha_inicio', 'N/A')}  
**Fecha de Finalización:** {contrato.get('fecha_fin', 'N/A')}  
**Valor Total:** {contrato.get('moneda', 'USD')} {contrato.get('valor', 'N/A'):,.2f}

---

## ENTREGABLES

{chr(10).join(f"- {entregable}" for entregable in contrato.get('entregables', []))}

---

## CLÁUSULAS

### 1. OBLIGACIONES DEL CONTRATISTA
El contratista se compromete a:
- Ejecutar el servicio conforme a los términos acordados
- Entregar los entregables en las fechas establecidas
- Mantener la confidencialidad de la información recibida

### 2. OBLIGACIONES DEL CONTRATANTE
El contratante se compromete a:
- Proporcionar la información necesaria para la ejecución del servicio
- Realizar los pagos conforme al cronograma acordado
- Colaborar activamente en el desarrollo del proyecto

### 3. PAGO
El pago se realizará según el cronograma acordado entre las partes.

### 4. CONFIDENCIALIDAD
Ambas partes se comprometen a mantener la confidencialidad de la información intercambiada.

### 5. TERMINACIÓN
El contrato podrá ser terminado por mutuo acuerdo o por incumplimiento de cualquiera de las partes.

---

## FIRMAS

**CONTRATANTE**

{contratante.get('representante_legal', 'N/A')}  
{contratante.get('cargo', 'N/A')}  
{contratante.get('empresa', 'N/A')}

_________________________  
Firma

**CONTRATISTA**

{proveedor.get('nombre', 'N/A')}

_________________________  
Firma

---

*Contrato generado el {datetime.now().strftime('%d de %B de %Y')}*
"""
        
        return jsonify({
            "document": document,
            "format": "markdown",
            "status": "success",
            "message": "Contrato generado exitosamente"
        }), 200
        
    except Exception as e:
        return jsonify({
            "document": "",
            "format": "markdown",
            "status": "error",
            "message": f"Error al generar el documento: {str(e)}"
        }), 500


@app.route('/send_email', methods=['POST'])
def send_email():
    """
    Envía el contrato por correo electrónico (simulado).
    
    Request body:
    {
        "document": "...",
        "recipient": "jairo@mantisapp.co",
        "firma": "..." (opcional)
    }
    
    Response:
    {
        "status": "SENT",
        "recipient": "...",
        "message": "..."
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "ERROR",
                "recipient": "",
                "message": "No se recibieron datos"
            }), 400
        
        document = data.get("document", "")
        recipient = data.get("recipient", "jairo@mantisapp.co")
        firma = data.get("firma", "")
        
        if not document:
            return jsonify({
                "status": "ERROR",
                "recipient": recipient,
                "message": "No se proporcionó el documento a enviar"
            }), 400
        
        # Reemplazar líneas bajas por la firma si se proporciona
        if firma:
            # Buscar y reemplazar líneas bajas después del nombre del contratante
            # El documento tiene esta estructura:
            # **CONTRATANTE**
            # [nombre]
            # [cargo]
            # [empresa]
            # _________________________  <- Reemplazar esto
            # Firma
            lines = document.split('\n')
            in_contratante_section = False
            for i, line in enumerate(lines):
                if '**CONTRATANTE**' in line:
                    in_contratante_section = True
                elif in_contratante_section and '_________________________' in line:
                    # Reemplazar las líneas bajas con la firma
                    lines[i] = firma
                    break
                elif in_contratante_section and '**CONTRATISTA**' in line:
                    # Si llegamos a CONTRATISTA sin encontrar las líneas bajas, salir
                    break
            document = '\n'.join(lines)
        
        # Simulación de envío de correo
        # En producción, aquí se integraría con un servicio de correo real
        
        return jsonify({
            "status": "SENT",
            "recipient": recipient,
            "message": f"Contrato enviado exitosamente a {recipient}",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "recipient": data.get("recipient", ""),
            "message": f"Error al enviar el correo: {str(e)}"
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Endpoint de salud del servidor"""
    return jsonify({
        "status": "healthy",
        "service": "MCP Server",
        "port": 8081
    }), 200


if __name__ == '__main__':
    print("Iniciando servidor MCP en puerto 8081...")
    app.run(host='0.0.0.0', port=8081, debug=True)

