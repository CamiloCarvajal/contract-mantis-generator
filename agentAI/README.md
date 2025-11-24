# Agente AI

Servicio que procesa texto libre y gestiona el flujo completo de contratos usando LLM.

## Puerto
8082

## Endpoints

### POST /process_contract
Procesa texto libre y ejecuta el flujo completo (validación → generación → envío).

**Request:**
```json
{
  "text": "Queremos contratar a Laura Martínez para un proyecto de conciliación desde enero a abril por 4.800 dólares."
}
```

**Response (éxito):**
```json
{
  "status": "success",
  "message": "Contrato procesado, generado y enviado exitosamente",
  "data": {...},
  "document": "...",
  "email_status": {...}
}
```

**Response (validación fallida):**
```json
{
  "status": "validation_error",
  "message": "La información proporcionada no es completa o correcta",
  "data": {...},
  "validation_result": {...},
  "question": "¿Podrías proporcionar más información sobre..."
}
```

### GET /health
Endpoint de salud del servidor.

## Configuración

### Variables de Entorno

**Para Ollama (recomendado):**
- `OLLAMA_API_URL`: URL de la API de Ollama (default: `http://localhost:11434`)
- `OLLAMA_MODEL`: Modelo a usar (default: `mistral`)

**Para OpenAI:**
- `OPENAI_API_KEY`: API key de OpenAI (requerida si usas OpenAI)
- `OPENAI_MODEL`: Modelo a usar (default: `gpt-4o-mini`)


**Comunes:**
- `LLM_PROVIDER`: Proveedor LLM a usar: `openai` o `ollama` (default: `openai`)
- `MCP_SERVER_URL`: URL del servidor MCP (default: `http://localhost:8081`)


### Ejemplo (.env) - Ollama
```
LLM_PROVIDER=ollama
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=mistral
MCP_SERVER_URL=http://localhost:8081
```

### Ejemplo (.env) - OpenAI
```
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
MCP_SERVER_URL=http://localhost:8081
```

## Variables Disponibles

| Variable | Descripción | Requerida | Default |
|----------|-------------|-----------|---------|
| `LLM_PROVIDER` | Proveedor a usar: `openai` o `ollama` | No | `openai` |
| `OPENAI_API_KEY` | API key de OpenAI | Sí (si usas OpenAI) | - |
| `OPENAI_MODEL` | Modelo de OpenAI | No | `gpt-4o-mini` |
| `OLLAMA_API_URL` | URL de la API de Ollama | No | `http://localhost:11434` |
| `OLLAMA_MODEL` | Modelo de Ollama | No | `mistral` |
| `MCP_SERVER_URL` | URL del servidor MCP | No | `http://localhost:8081` |


## Instalación

```bash
pip install -r requirements.txt
```

## Ejecución

**Con OpenAI:**
```bash
# Asegúrate de tener configurada OPENAI_API_KEY
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...

python app.py
```

**Con Ollama:**
```bash
# Asegúrate de que Ollama esté corriendo
export LLM_PROVIDER=ollama
export OLLAMA_API_URL=http://localhost:11434
export OLLAMA_MODEL=llama2  # O el modelo que prefieras

python app.py
```

El servidor estará disponible en `http://localhost:8082`

## Arquitectura

El agente usa una arquitectura abstracta que permite cambiar entre diferentes proveedores de LLM:

- `LLMProvider`: Interfaz abstracta
- `OpenAIProvider`: Implementación concreta para OpenAI
- `OllamaProvider`: Implementación concreta para Ollama

Para agregar nuevos proveedores (Claude, etc.), implementa la clase `LLMProvider`.

## Usar Ollama como Proveedor LLM

Ollama es una herramienta para ejecutar modelos LLM localmente. Para usarlo:

1. **Instala Ollama**: Descarga desde [ollama.ai](https://ollama.ai)

2. **Descarga un modelo**:
   ```bash
   ollama pull llama2
   # O cualquier otro modelo: mistral, codellama, etc.
   ```

3. **Asegúrate de que Ollama esté corriendo**:
   ```bash
   ollama serve
   ```

4. **Configura las variables de entorno**:
   ```bash
   export LLM_PROVIDER=ollama
   export OLLAMA_API_URL=http://localhost:11434
   export OLLAMA_MODEL=llama2
   ```

5. **Ejecuta el agente**:
   ```bash
   python app.py
   ```

El proveedor de Ollama intenta usar ambos endpoints (`/api/generate` y `/api/chat`) para máxima compatibilidad con diferentes versiones de Ollama.

