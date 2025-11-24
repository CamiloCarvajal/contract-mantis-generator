# Guía Rápida: Usar Ollama con el Agente AI

## ¿Qué es Ollama?

Ollama es una herramienta que permite ejecutar modelos LLM grandes localmente en tu computadora, sin necesidad de API keys ni conexión a servicios externos.

## Instalación de Ollama

### Windows/Mac/Linux
1. Visita [ollama.ai](https://ollama.ai)
2. Descarga e instala Ollama
3. Verifica la instalación:
   ```bash
   ollama --version
   ```

## Iniciar Ollama

```bash
# Inicia el servidor de Ollama
ollama serve
```

El servidor estará disponible en `http://localhost:11434`

## Descargar un Modelo

Ollama necesita que descargues un modelo antes de usarlo:

```bash
# Modelo recomendado para este proyecto
ollama pull mistral

# Modelos populares:
ollama pull mistral        # Modelo más pequeño y rápido
ollama pull codellama      # Especializado en código
ollama pull llama2:13b     # Versión más grande (mejor calidad)
```

**Nota:** La primera vez que descargas un modelo puede tardar varios minutos dependiendo de tu conexión.

## Configurar el Agente AI para Usar Ollama

### Opción 1: Variables de Entorno

```bash
# Windows (PowerShell)
$env:LLM_PROVIDER="ollama"
$env:OLLAMA_API_URL="http://localhost:11434"
$env:OLLAMA_MODEL="llama2"

# Linux/Mac
export LLM_PROVIDER=ollama
export OLLAMA_API_URL="http://localhost:11434"
export OLLAMA_MODEL="llama2"
```

### Opción 2: Archivo .env

Crea un archivo `.env` en la carpeta `agentAI`:

```
LLM_PROVIDER=ollama
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

## Ejecutar el Agente

```bash
cd agentAI
python app.py
```

Deberías ver:
```
Proveedor LLM inicializado: ollama
  - API URL: http://localhost:11434
  - Modelo: llama2
```

## Verificar que Ollama Está Funcionando

Puedes probar Ollama directamente:

```bash
# Probar desde la terminal
ollama run llama2 "Hola, ¿cómo estás?"

# O verificar la API
curl http://localhost:11434/api/tags
```

## Modelos Recomendados

Para este proyecto de extracción de contratos, estos modelos funcionan bien:

1. **llama2** - Balance entre calidad y velocidad
2. **mistral** - Más rápido, buena calidad
3. **llama2:13b** - Mejor calidad, más lento
4. **codellama** - Si necesitas mejor comprensión de estructura

## Troubleshooting

### Error: "No se pudo conectar con Ollama"
- Asegúrate de que `ollama serve` esté corriendo
- Verifica que el puerto 11434 esté disponible
- Prueba: `curl http://localhost:11434/api/tags`

### Error: "Modelo no encontrado"
- Descarga el modelo: `ollama pull nombre-del-modelo`
- Verifica modelos disponibles: `ollama list`

### Respuestas lentas
- Usa un modelo más pequeño (ej: `mistral` en lugar de `llama2:13b`)
- Asegúrate de tener suficiente RAM (los modelos grandes necesitan 8GB+)

### Respuestas de baja calidad
- Prueba un modelo más grande (ej: `llama2:13b`)
- Ajusta la temperatura en `ollama_provider.py` si es necesario

## Ventajas de Usar Ollama

✅ **Privacidad**: Todo se ejecuta localmente  
✅ **Sin costos**: No hay límites de uso ni API keys  
✅ **Sin internet**: Funciona offline  
✅ **Control total**: Puedes usar cualquier modelo compatible  

## Desventajas

❌ **Recursos**: Requiere RAM y CPU suficientes  
❌ **Velocidad**: Puede ser más lento que servicios en la nube  
❌ **Calidad**: Depende del modelo que uses  

## Próximos Pasos

Una vez configurado, puedes usar el agente normalmente:

```bash
# Probar con el script de ejemplo
python ../example_usage.py
```

El agente funcionará igual que con OpenAI, pero usando tu modelo local de Ollama.

