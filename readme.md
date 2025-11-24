# Instrucciones de Uso

## Requisitos Previos

1. Python 3.8 o superior
2. **Opción A**: Ollama instalado y corriendo (Recomendado) [Ver como instalar Ollama](OLLAMA_SETUP.md).
   **Opción B**: API Key de OpenAI (para el agente AI)

## Instalación

### 1. Servidor MCP (Puerto 8081)

```bash
cd serverMCP
pip install -r requirements.txt
```

### 2. Agente AI (Puerto 8082)

```bash
cd agentAI
pip install -r requirements.txt
```

Configurar las variables de entorno según el proveedor que uses:

Crea un archivo .env en la carpeta agentAI con los parametros:

**Para OpenAI:**
```bash
LLM_PROVIDER=openai
OPENAI_MODEL=gpt-4o-mini
OPENAI_API_KEY="sk-proj-..."
```

**Para Ollama:**
```bash
LLM_PROVIDER=ollama
OLLAMA_MODEL=mistral
OLLAMA_API_URL="http://localhost:11434"
```

## Ejecución

### Terminal 1 - Servidor MCP
```bash
cd serverMCP
python app.py
```

El servidor estará disponible en `http://localhost:8081`

### Terminal 2 - Agente AI
```bash
cd agentAI
python app.py
```

El agente estará disponible en `http://localhost:8082`


### Web

Con ambos servicios activos, dirigete a la pagina web [contract-mantis-generator](https://contract-mantis-generator.lovable.app) e ingresa el texto para la creación del contrato.

#### Texto de ejemplo:
"Queremos contratar a Laura Sofía Martínez Gómez, con documento CC 52.871.993, correo laura.martinez@example.com y teléfono +57 310 555 9080, para el proyecto Optimización del Proceso de Conciliación. El servicio es Consultoría en automatización de procesos y conciliación contable. El valor es USD 4,800. Fecha de inicio: 15 de enero de 2026. Fecha de fin: 15 de abril de 2026. Entregables: Diagnóstico inicial, plan de automatización, piloto, informe final. La empresa contratante es TechNova S.A.S. con NIT 901.456.789-1. Representante legal: Carlos Eduardo Rincón, CEO. Dirección: Cra. 45 #100–32, Bogotá. Correo: contratos@technova.co"



## Flujo del Sistema

1. **Usuario envía texto libre** → `POST /process_contract` (Agente AI)
2. **Agente AI extrae datos** → Usa LLM (OpenAI u Ollama) para extraer y normalizar campos
3. **Agente AI valida** → `POST /validate_request` (Servidor MCP)
4. **Si hay errores** → Agente AI genera pregunta y retorna
5. **Si es válido** → `POST /generate_document` (Servidor MCP)
6. **Agente AI envía correo** → `POST /send_email` (Servidor MCP)
7. **Retorna resultado completo** → Contrato generado y confirmación de envío

## Estructura de Respuestas

### Éxito
```json
{
  "status": "success,
  "message": "Contrato procesado, generado y enviado exitosamente",
  "data": {...},
  "document": "...",
  "email_status": {...}
}
```

### Error de Validación
```json
{
  "status": "validation_error",
  "message": "La información proporcionada no es completa o correcta",
  "data": {...},
  "validation_result": {...},
  "question": "¿Podrías proporcionar más información sobre..."
}
```

## Datos Oficiales del Caso

Los datos oficiales están hardcodeados en `serverMCP/app.py` y son la única fuente de verdad para la validación:

- **Proveedor**: Laura Sofía Martínez Gómez (CC 52.871.993)
- **Proyecto**: Optimización del Proceso de Conciliación
- **Valor**: USD 4,800
- **Fechas**: 15 enero 2026 - 15 abril 2026
- **Contratante**: TechNova S.A.S. (NIT 901.456.789-1)

## Notas

- El agente AI está diseñado para ser abstracto y permitir cambiar entre diferentes proveedores de LLM
- Actualmente soporta OpenAI y Ollama, pero se puede extender para usar Claude u otros
- El envío de correo está simulado (retorna status "SENT")
- Ambos servicios se comunican vía REST

## Usar Ollama como Proveedor LLM

Ollama permite ejecutar modelos LLM localmente sin necesidad de API keys. Es ideal para desarrollo y privacidad.

**Instalación de Ollama:**
1. Descarga desde [ollama.ai](https://ollama.ai)
2. Instala y ejecuta `ollama serve`
3. Descarga un modelo: `ollama pull llama2` (o `mistral`, `codellama`, etc.)

**Ventajas de Ollama:**
- No requiere API keys
- Ejecución local (privacidad)
- Gratis
- Múltiples modelos disponibles

**Desventajas:**
- Requiere recursos computacionales locales
- Puede ser más lento que servicios en la nube
- Calidad puede variar según el modelo

