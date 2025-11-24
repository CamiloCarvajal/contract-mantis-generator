"""
Proveedor abstracto de LLM
Permite cambiar entre diferentes proveedores (OpenAI, Claude, etc.)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class LLMProvider(ABC):
    """Interfaz abstracta para proveedores de LLM"""
    
    @abstractmethod
    def extract_contract_data(self, text: str) -> Dict[str, Any]:
        """
        Extrae y normaliza los datos del contrato desde texto libre.
        
        Args:
            text: Texto libre con la información del contrato
            
        Returns:
            Dict con la estructura:
            {
                "proveedor": {...},
                "contrato": {...},
                "contratante": {...}
            }
        """
        pass
    
    @abstractmethod
    def generate_question(self, missing_fields: list, errors: list) -> str:
        """
        Genera una pregunta natural para solicitar información faltante.
        
        Args:
            missing_fields: Lista de campos faltantes
            errors: Lista de errores de validación
            
        Returns:
            Pregunta en lenguaje natural
        """
        pass

