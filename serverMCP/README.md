# Servidor MCP (Model Context Protocol)

Servidor REST que expone endpoints para validación, generación de documentos y envío de correos.

## Puerto
8081

## Endpoints

### POST /validate_request
Valida los datos extraídos contra los datos oficiales del caso.

**Request:**
```json
{
  "proveedor": {
    "nombre": "...",
    "documento": "...",
    "correo": "...",
    "telefono": "..."
  },
  "contrato": {
    "proyecto": "...",
    "servicio": "...",
    "valor": 4800,
    "moneda": "USD",
    "fecha_inicio": "2026-01-15",
    "fecha_fin": "2026-04-15",
    "entregables": [...]
  },
  "contratante": {
    "empresa": "...",
    "nit": "...",
    "representante_legal": "...",
    "cargo": "...",
    "direccion": "...",
    "correo": "..."
  }
}
```

**Response:**
```json
{
  "valid": true/false,
  "errors": [...],
  "missing_fields": [...],
  "message": "..."
}
```

### POST /generate_document
Genera un contrato en formato Markdown.

**Request:** Mismo formato que `/validate_request`

**Response:**
```json
{
  "document": "...",
  "format": "markdown",
  "status": "success",
  "message": "..."
}
```

### POST /send_email
Envía el contrato por correo electrónico (simulado).

**Request:**
```json
{
  "document": "...",
  "recipient": "jairo@mantisapp.co"
}
```

**Response:**
```json
{
  "status": "SENT",
  "recipient": "...",
  "message": "...",
  "timestamp": "..."
}
```

### GET /health
Endpoint de salud del servidor.

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecución

```bash
python app.py
```

El servidor estará disponible en `http://localhost:8081`

