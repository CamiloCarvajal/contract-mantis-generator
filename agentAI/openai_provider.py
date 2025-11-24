"""
Implementación del proveedor LLM usando OpenAI
"""

import os
import json
from typing import Dict, Any
from llm_provider import LLMProvider


class OpenAIProvider(LLMProvider):
    """Implementación concreta usando OpenAI"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        """
        Inicializa el proveedor OpenAI.
        
        Args:
            api_key: API key de OpenAI (si no se proporciona, se busca en OPENAI_API_KEY)
            model: Modelo a usar (default: gpt-4o-mini)
        """
        try:
            from openai import OpenAI
            
            # Obtener API key
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY no está configurada")
            
            # Inicializar cliente de forma simple y directa
            # La librería openai maneja proxies automáticamente a través de variables de entorno
            # No pasamos proxies explícitamente para evitar conflictos de versión
            self.client = OpenAI(api_key=api_key)
            self.model = model
        except ImportError:
            raise ImportError("openai no está instalado. Ejecuta: pip install --upgrade openai")
        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise Exception(f"Error al inicializar OpenAI: {str(e)}")
    
    def extract_contract_data(self, text: str) -> Dict[str, Any]:
        """
        Extrae y normaliza los datos del contrato desde texto libre usando OpenAI.
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            
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
            raise Exception(f"Error al parsear respuesta de OpenAI: {str(e)}")
        except Exception as e:
            raise Exception(f"Error al extraer datos con OpenAI: {str(e)}")
    
    def generate_question(self, missing_fields: list, errors: list) -> str:
        """
        Genera una pregunta natural para solicitar información faltante.
        """
        system_prompt = """Eres un asistente que ayuda a completar información de contratos.
Tu tarea es generar una pregunta amigable y natural en español que solicite la información faltante o incorrecta.
La pregunta debe ser clara, específica y en lenguaje natural (no mencionar campos técnicos)."""

        missing_info = []
        if missing_fields:
            missing_info.append(f"Campos faltantes: {', '.join(missing_fields)}")
        if errors:
            missing_info.append(f"Errores encontrados: {', '.join(errors)}")
        
        user_prompt = f"""Basándote en la siguiente información, genera una pregunta natural en español para solicitar los datos faltantes o corregir los errores:

{chr(10).join(missing_info)}

IMPORTANTE:
- La pregunta debe ser en lenguaje natural, como si hablaras con una persona
- No uses términos técnicos como "proveedor.nombre" o "contrato.valor"
- Sé específico sobre qué información necesitas
- Mantén un tono profesional pero amigable
- Retorna SOLO la pregunta, sin explicaciones adicionales"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback a pregunta genérica
            return f"Necesito más información para completar el contrato. Por favor, proporciona: {', '.join(missing_fields[:3])}."

