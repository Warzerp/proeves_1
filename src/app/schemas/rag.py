# src/app/schemas/rag.py
from datetime import datetime, date
from pydantic import BaseModel
from typing import Optional, Union

class SimilarChunk(BaseModel):
    """
    Schema para chunks similares encontrados en búsqueda vectorial.
    Incluye información del doctor cuando el source_type es 'appointment'.
    """
    source_type: str          # "appointment", "diagnosis", "medical_record", "prescription"
    source_id: int            # id de la fila en su tabla
    patient_id: int
    chunk_text: str           # texto que verá el LLM
    date: Union[datetime, date, None] = None
    relevance_score: float    # mientras más alto, más relevante
    
    # Campos opcionales para appointments (información del doctor)
    doctor_name: Optional[str] = None
    specialty_name: Optional[str] = None
    medical_license: Optional[str] = None
    
    class Config:
        from_attributes = True