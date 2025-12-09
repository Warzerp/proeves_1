from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class LLMResponse(BaseModel):
    """Respuesta del LLM"""
    text: str = Field(..., description="Respuesta generada por el LLM")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Nivel de confianza")
    model_used: str = Field(..., description="Modelo utilizado")
    tokens_used: int = Field(default=0, description="Tokens consumidos")
    
    # Configuración para evitar el warning de pydantic
    model_config = ConfigDict(protected_namespaces=())

class LLMError(Exception):
    """Excepción personalizada para errores del LLM"""
    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)