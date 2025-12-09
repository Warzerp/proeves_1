# src/app/routers/query.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal, Union
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging
import time
import asyncio

from app.services.llm_service import llm_service
from app.services.clinical_service import fetch_patient_and_records
from app.services.vector_search import search_similar_chunks
from app.database.database import get_db
from app.schemas.clinical import PatientInfo, ClinicalRecords

router = APIRouter(prefix="/query", tags=["RAG Query"])
logger = logging.getLogger(__name__)

# === CONFIGURACIÓN DE TIMEOUTS ===
LLM_TIMEOUT_SECONDS = 30
VECTOR_SEARCH_TIMEOUT_SECONDS = 10
TOTAL_REQUEST_TIMEOUT_SECONDS = 45

# === SCHEMAS ===

class QueryInput(BaseModel):
    user_id: str
    session_id: str
    document_type_id: int
    document_number: str
    question: str


# === FUNCIONES AUXILIARES ===

def get_iso_timestamp() -> str:
    """Retorna timestamp en formato ISO 8601 con Z (UTC)"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_context_from_real_data(
    patient_info: PatientInfo,
    clinical_records: ClinicalRecords,
    similar_chunks: List
) -> str:
    """Construye el contexto clínico de manera segura"""
    
    from datetime import date, datetime

    # === Calcular edad ===
    age = "No disponible"
    if patient_info.birth_date:
        try:
            birth_date = (
                patient_info.birth_date
                if isinstance(patient_info.birth_date, date)
                else datetime.strptime(patient_info.birth_date, "%Y-%m-%d").date()
            )
            today = date.today()
            age = today.year - birth_date.year - (
                (today.month, today.day) < (birth_date.month, birth_date.day)
            )
        except Exception as e:
            logger.warning(f"Error calculando edad: {e}")
            age = "No disponible"

    # Usar getattr para todos los campos de patient_info
    first_name = getattr(patient_info, 'first_name', 'Nombre')
    first_surname = getattr(patient_info, 'first_surname', 'Apellido')
    document_number = getattr(patient_info, 'document_number', 'No disponible')
    gender = getattr(patient_info, 'gender', None) or "No registrado"
    email = getattr(patient_info, 'email', None) or "No registrado"

    context = f"""
### INFORMACIÓN BÁSICA DEL PACIENTE
Nombre: {first_name} {first_surname}
Edad: {age}
Documento: {document_number}
Género: {gender}
Email: {email}

"""

    # === CITAS ===
    if clinical_records.appointments:
        context += "### CITAS MÉDICAS RECIENTES\n"
        for apt in clinical_records.appointments[:10]:
            apt_date = getattr(apt, 'appointment_date', 'Fecha no disponible')
            apt_status = getattr(apt, 'status', None) or 'No disponible'
            apt_reason = getattr(apt, 'reason', None) or 'No especificado'
            apt_type = getattr(apt, 'appointment_type', None) or 'Consulta'
            doctor_name = getattr(apt, 'doctor_name', None)
            specialty = getattr(apt, 'specialty_name', None)
            
            context += f"**Cita {apt_date}**\n"
            context += f"- Tipo: {apt_type}\n"
            context += f"- Estado: {apt_status}\n"
            context += f"- Motivo: {apt_reason}\n"
            if doctor_name:
                context += f"- Doctor: {doctor_name}"
                if specialty:
                    context += f" ({specialty})"
                context += "\n"
            context += "\n"

    # === REGISTROS MÉDICOS ===
    if clinical_records.medical_records:
        context += "### REGISTROS MÉDICOS\n"
        for rec in clinical_records.medical_records[:10]:
            desc = (
                getattr(rec, "summary_text", None) or
                getattr(rec, "description", None) or
                getattr(rec, "details", None) or
                getattr(rec, "notes", None) or
                "Sin descripción"
            )
            
            rec_date = getattr(rec, 'registration_datetime', 'Fecha no disponible')
            rec_type = getattr(rec, 'record_type', 'Tipo no especificado')

            context += (
                f"- Fecha: {rec_date}\n"
                f"  Tipo: {rec_type}\n"
                f"  Descripción: {desc}\n\n"
            )

    # === PRESCRIPCIONES ===
    if clinical_records.prescriptions:
        context += "### MEDICAMENTOS Y PRESCRIPCIONES\n"
        for presc in clinical_records.prescriptions[:15]:
            medication = getattr(presc, 'medication_name', 'Medicamento sin nombre')
            dosage = getattr(presc, 'dosage', '')
            frequency = getattr(presc, 'frequency', '')
            duration = getattr(presc, 'duration', None)
            instruction = getattr(presc, 'instruction', None)
            presc_date = getattr(presc, 'prescription_date', None)
            
            context += f"**{medication}**\n"
            if dosage or frequency:
                context += f"- Dosis: {dosage} {frequency}\n"
            if duration:
                context += f"- Duración: {duration}\n"
            if instruction:
                context += f"- Indicaciones: {instruction}\n"
            if presc_date:
                context += f"- Fecha de prescripción: {presc_date}\n"
            context += "\n"

    # === DIAGNÓSTICOS ===
    if clinical_records.diagnoses:
        context += "### DIAGNÓSTICOS\n"
        for diag in clinical_records.diagnoses[:15]:
            diag_desc = getattr(diag, 'description', 'Diagnóstico sin descripción')
            icd_code = getattr(diag, 'icd_code', 'Sin código')
            diag_type = getattr(diag, 'diagnosis_type', 'Tipo no especificado')
            note = getattr(diag, 'note', None)
            diag_date = getattr(diag, 'diagnosis_date', None)
            
            context += f"**{diag_desc}**\n"
            context += f"- Código ICD-10: {icd_code}\n"
            context += f"- Tipo: {diag_type}\n"
            if diag_date:
                context += f"- Fecha: {diag_date}\n"
            if note:
                context += f"- Nota: {note}\n"
            context += "\n"

    # === VECTOR SEARCH ===
    if similar_chunks:
        context += "### INFORMACIÓN ADICIONAL RELEVANTE (BÚSQUEDA SEMÁNTICA)\n"
        for chunk in similar_chunks[:5]:
            chunk_text = getattr(chunk, 'chunk_text', 'Texto no disponible')
            relevance = getattr(chunk, 'relevance_score', 0.0)
            source_type = getattr(chunk, 'source_type', 'Desconocida')
            chunk_date = getattr(chunk, 'date', 'Sin fecha')
            
            context += f"- [Relevancia: {relevance:.2f}] {chunk_text}\n"
            context += f"  Fuente: {source_type} - Fecha: {chunk_date}\n\n"

    return context


def build_sources_from_real_data(
    clinical_records: ClinicalRecords, 
    similar_chunks: List,
    sequence_counter: int
) -> List[Dict]:
    """
    Construye lista de fuentes siguiendo el formato EXACTO de la especificación.
    """
    sources = []
    current_sequence = sequence_counter

    # CITAS - formato especificación EXACTO
    try:
        for apt in clinical_records.appointments[:5]:
            apt_id = getattr(apt, 'appointment_id', None)
            if not apt_id:
                continue
                
            apt_date = getattr(apt, 'appointment_date', None)
            apt_reason = getattr(apt, 'reason', None)
            
            # ✅ Extraer información del doctor (ahora viene del JOIN)
            doctor_name = getattr(apt, 'doctor_name', None)
            specialty_name = getattr(apt, 'specialty_name', None)
            medical_license = getattr(apt, 'medical_license_number', None)
            
            source = {
                "source_id": current_sequence,
                "type": "appointment",
                "appointment_id": int(apt_id),
                "date": str(apt_date) if apt_date else None,
                "relevance_score": 0.98  # Alta relevancia para datos directos
            }
            
            # Agregar doctor si existe (formato EXACTO)
            if doctor_name or specialty_name:
                doctor_info = {}
                if doctor_name:
                    doctor_info["name"] = doctor_name
                if specialty_name:
                    doctor_info["specialty"] = specialty_name
                if medical_license:
                    doctor_info["medical_license"] = medical_license
                
                if doctor_info:
                    source["doctor"] = doctor_info
            
            if apt_reason:
                source["reason"] = apt_reason
                
            sources.append(source)
            current_sequence += 1
            
    except Exception as e:
        logger.warning(f"Error construyendo sources de appointments: {e}")

    # DIAGNÓSTICOS - formato especificación EXACTO
    try:
        for diag in clinical_records.diagnoses[:5]:
            diag_id = getattr(diag, 'diagnosis_id', None)
            if not diag_id:
                continue
                
            diag_desc = getattr(diag, 'description', 'Sin descripción')
            icd_code = getattr(diag, 'icd_code', None)
            # ✅ Fecha del diagnóstico (ahora viene del medical_record)
            diag_date = getattr(diag, 'diagnosis_date', None)
            
            source = {
                "source_id": current_sequence,
                "type": "diagnosis",
                "diagnosis_id": int(diag_id),
                "description": diag_desc,
                "relevance_score": 0.95
            }
            
            if icd_code:
                source["icd_code"] = icd_code
            if diag_date:
                # ✅ Convertir datetime a string solo con fecha
                source["date"] = str(diag_date.date()) if hasattr(diag_date, 'date') else str(diag_date)
                
            sources.append(source)
            current_sequence += 1
            
    except Exception as e:
        logger.warning(f"Error construyendo sources de diagnoses: {e}")

    # PRESCRIPCIONES
    try:
        for presc in clinical_records.prescriptions[:3]:
            presc_id = getattr(presc, 'prescription_id', None)
            if not presc_id:
                continue
                
            # ✅ Nombre del medicamento (ahora viene del JOIN)
            medication = getattr(presc, 'medication_name', 'Medicamento no especificado')
            presc_date = getattr(presc, 'prescription_date', None)
            dosage = getattr(presc, 'dosage', None)
            frequency = getattr(presc, 'frequency', None)
            
            source = {
                "source_id": current_sequence,
                "type": "prescription",
                "prescription_id": int(presc_id),
                "medication": medication,
                "date": str(presc_date) if presc_date else None,
                "relevance_score": 0.92
            }
            
            # Agregar dosage y frequency si existen
            if dosage:
                source["dosage"] = dosage
            if frequency:
                source["frequency"] = frequency
            
            sources.append(source)
            current_sequence += 1
            
    except Exception as e:
        logger.warning(f"Error construyendo sources de prescriptions: {e}")

    # VECTOR CHUNKS
    try:
        for chunk in similar_chunks[:5]:
            source_id = getattr(chunk, 'source_id', None)
            if not source_id:
                continue
                
            source_type = getattr(chunk, 'source_type', 'unknown')
            relevance = getattr(chunk, 'relevance_score', 0.0)
            chunk_date = getattr(chunk, 'date', None)
            
            source = {
                "source_id": current_sequence,
                "type": "vector_search",
                "original_source_id": str(source_id),
                "source_type": source_type,
                "relevance_score": float(relevance),
                "date": str(chunk_date) if chunk_date else None
            }
            
            sources.append(source)
            current_sequence += 1
            
    except Exception as e:
        logger.warning(f"Error construyendo sources de vector chunks: {e}")

    return sources


def get_document_type_name(document_type_id: int) -> str:
    """Mapea ID de tipo de documento a nombre"""
    types = {
        1: "CC", 2: "CE", 3: "TI", 4: "PA",
        5: "RC", 6: "MS", 7: "AS", 8: "CD",
    }
    return types.get(document_type_id, "CC")


def _generate_fallback_response(clinical_records: ClinicalRecords, question: str) -> str:
    """Genera una respuesta básica cuando el LLM falla"""
    response_parts = []
    
    if clinical_records.appointments:
        response_parts.append("*Citas Médicas Recientes:*\n")
        for apt in clinical_records.appointments[:3]:
            date = getattr(apt, 'appointment_date', 'Fecha no disponible')
            reason = getattr(apt, 'reason', 'No especificado')
            status = getattr(apt, 'status', 'No disponible')
            response_parts.append(f"- {date}: {reason} (Estado: {status})")
    
    if clinical_records.diagnoses:
        response_parts.append("\n*Diagnósticos:*\n")
        for diag in clinical_records.diagnoses[:3]:
            desc = getattr(diag, 'description', 'Sin descripción')
            icd = getattr(diag, 'icd_code', '')
            response_parts.append(f"- {desc} (ICD: {icd})")
    
    if clinical_records.prescriptions:
        response_parts.append("\n*Medicamentos Prescritos:*\n")
        for presc in clinical_records.prescriptions[:3]:
            med = getattr(presc, 'medication_name', 'Medicamento no especificado')
            dosage = getattr(presc, 'dosage', '')
            response_parts.append(f"- {med} {dosage}")
    
    if not response_parts:
        return "No se encontró información relevante para responder la pregunta."
    
    response_parts.append("\n*Nota: Esta respuesta fue generada desde los registros clínicos debido a un problema temporal.*")
    
    return "\n".join(response_parts)


# === ENDPOINT PRINCIPAL ===

@router.post("/")
async def query_patient(input_data: QueryInput, db: Session = Depends(get_db)):
    """
    Endpoint principal de consulta RAG.
    Formato de salida EXACTO según especificación del proyecto.
    """
    start_time = time.time()
    timestamp = get_iso_timestamp()
    sequence_chat_id = 1

    try:
        return await asyncio.wait_for(
            _process_query(input_data, db, start_time, timestamp, sequence_chat_id),
            timeout=TOTAL_REQUEST_TIMEOUT_SECONDS
        )
    
    except asyncio.TimeoutError:
        logger.error(f"Request timeout después de {TOTAL_REQUEST_TIMEOUT_SECONDS}s")
        return {
            "status": "error",
            "session_id": input_data.session_id,
            "sequence_chat_id": sequence_chat_id,
            "timestamp": get_iso_timestamp(),
            "error": {
                "code": "REQUEST_TIMEOUT",
                "message": f"La solicitud excedió el tiempo máximo de {TOTAL_REQUEST_TIMEOUT_SECONDS} segundos",
                "details": "Intente nuevamente con una pregunta más específica"
            }
        }
    
    except asyncio.CancelledError:
        logger.warning("Request cancelado por el cliente")
        raise
    
    except Exception as e:
        logger.exception("Error inesperado en endpoint")
        return {
            "status": "error",
            "session_id": input_data.session_id,
            "sequence_chat_id": sequence_chat_id,
            "timestamp": get_iso_timestamp(),
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Error interno del servidor",
                "details": str(e)
            }
        }


async def _process_query(
    input_data: QueryInput,
    db: Session,
    start_time: float,
    timestamp: str,
    sequence_chat_id: int
) -> dict:
    """Lógica principal del procesamiento de la query"""
    
    logger.info(f"Procesando query - Session: {input_data.session_id}")

    # 1. BUSCAR PACIENTE
    try:
        patient_info, clinical_data = fetch_patient_and_records(
            db=db,
            document_type_id=input_data.document_type_id,
            document_number=input_data.document_number
        )
    except Exception as e:
        logger.error(f"Error en búsqueda de paciente: {type(e).__name__}")
        return {
            "status": "error",
            "session_id": input_data.session_id,
            "sequence_chat_id": sequence_chat_id,
            "timestamp": get_iso_timestamp(),
            "error": {
                "code": "DATABASE_ERROR",
                "message": "Error al buscar datos del paciente",
                "details": str(e)
            }
        }

    if not patient_info:
        doc_type = get_document_type_name(input_data.document_type_id)
        return {
            "status": "error",
            "session_id": input_data.session_id,
            "sequence_chat_id": sequence_chat_id,
            "timestamp": get_iso_timestamp(),
            "error": {
                "code": "PATIENT_NOT_FOUND",
                "message": f"No se encontró paciente con documento {doc_type} {input_data.document_number}",
                "details": "Verifique el tipo y número de documento"
            }
        }

    # 2. VECTOR SEARCH CON TIMEOUT
    similar_chunks = []
    try:
        similar_chunks = await asyncio.wait_for(
            search_similar_chunks(
                patient_id=getattr(patient_info, 'patient_id', None),
                question=input_data.question,
                k=15,
                min_score=0.3
            ),
            timeout=VECTOR_SEARCH_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError:
        logger.warning(f"Vector search timeout después de {VECTOR_SEARCH_TIMEOUT_SECONDS}s")
    except Exception as e:
        logger.warning(f"Vector search falló: {type(e).__name__}")

    # 3. CONSTRUIR CONTEXTO
    try:
        context = build_context_from_real_data(
            patient_info=patient_info,
            clinical_records=clinical_data.records,
            similar_chunks=similar_chunks
        )
    except Exception as e:
        logger.error(f"Error construyendo contexto: {type(e).__name__}")
        return {
            "status": "error",
            "session_id": input_data.session_id,
            "sequence_chat_id": sequence_chat_id,
            "timestamp": get_iso_timestamp(),
            "error": {
                "code": "CONTEXT_BUILD_ERROR",
                "message": "Error al construir contexto clínico",
                "details": str(e)
            }
        }

    # Extraer info del paciente
    patient_id = getattr(patient_info, 'patient_id', None)
    first_name = getattr(patient_info, 'first_name', 'Nombre')
    first_surname = getattr(patient_info, 'first_surname', 'Apellido')
    second_surname = getattr(patient_info, 'second_surname', '')
    document_number = getattr(patient_info, 'document_number', 'No disponible')
    doc_type = get_document_type_name(input_data.document_type_id)
    
    full_name = f"{first_name} {first_surname}"
    if second_surname:
        full_name += f" {second_surname}"

    # 4. VERIFICAR SI HAY DATOS (Caso: sin datos)
    total_records = (
        len(clinical_data.records.appointments) +
        len(clinical_data.records.medical_records) +
        len(clinical_data.records.prescriptions) +
        len(clinical_data.records.diagnoses) +
        len(similar_chunks)
    )

    if total_records == 0:
        return {
            "status": "success",
            "session_id": input_data.session_id,
            "sequence_chat_id": sequence_chat_id,
            "timestamp": get_iso_timestamp(),
            "patient_info": {
                "patient_id": patient_id,
                "full_name": full_name,
                "document_type": doc_type,
                "document_number": document_number
            },
            "answer": {
                "text": f"El paciente {full_name} no tiene citas médicas registradas en el sistema.",
                "confidence": 1.0,
                "model_used": "gpt-4o-mini"
            },
            "sources": [],
            "metadata": {
                "total_records_analyzed": 0,
                "query_time_ms": int((time.time() - start_time) * 1000),
                "sources_used": 0
            }
        }

    # 5. LLAMAR AL LLM CON TIMEOUT Y RETRY
    llm_response = None
    llm_attempts = 0
    max_attempts = 2
    
    while llm_attempts < max_attempts and not llm_response:
        llm_attempts += 1
        try:
            logger.info(f"Intento {llm_attempts}/{max_attempts} de llamada al LLM")
            
            llm_response = await asyncio.wait_for(
                llm_service.run_llm(
                    question=input_data.question,
                    context=context
                ),
                timeout=LLM_TIMEOUT_SECONDS
            )
            
            if not llm_response or not hasattr(llm_response, 'text') or not llm_response.text:
                if llm_attempts < max_attempts:
                    logger.warning(f"Respuesta LLM inválida, reintentando...")
                    await asyncio.sleep(0.5)
                    continue
                else:
                    raise ValueError("Respuesta del LLM vacía")
            
            if len(llm_response.text.strip()) < 10:
                if llm_attempts < max_attempts:
                    logger.warning(f"Respuesta LLM muy corta, reintentando...")
                    await asyncio.sleep(0.5)
                    continue
                else:
                    raise ValueError("Respuesta del LLM demasiado corta")
            
            break
        
        except asyncio.TimeoutError:
            logger.error(f"⏱️ LLM timeout en intento {llm_attempts}")
            if llm_attempts >= max_attempts:
                fallback_text = _generate_fallback_response(clinical_data.records, input_data.question)
                
                return {
                    "status": "success",
                    "session_id": input_data.session_id,
                    "sequence_chat_id": sequence_chat_id,
                    "timestamp": get_iso_timestamp(),
                    "patient_info": {
                        "patient_id": patient_id,
                        "full_name": full_name,
                        "document_type": doc_type,
                        "document_number": document_number
                    },
                    "answer": {
                        "text": fallback_text,
                        "confidence": 0.65,
                        "model_used": "fallback-system"
                    },
                    "sources": [],
                    "metadata": {
                        "total_records_analyzed": total_records,
                        "query_time_ms": int((time.time() - start_time) * 1000),
                        "sources_used": 0,
                        "context_tokens": 0
                    }
                }
            else:
                await asyncio.sleep(0.5)
                continue
        
        except Exception as e:
            logger.error(f"Error en intento {llm_attempts} del LLM: {e}")
            
            if llm_attempts >= max_attempts:
                fallback_text = _generate_fallback_response(clinical_data.records, input_data.question)
                
                return {
                    "status": "success",
                    "session_id": input_data.session_id,
                    "sequence_chat_id": sequence_chat_id,
                    "timestamp": get_iso_timestamp(),
                    "patient_info": {
                        "patient_id": patient_id,
                        "full_name": full_name,
                        "document_type": doc_type,
                        "document_number": document_number
                    },
                    "answer": {
                        "text": fallback_text,
                        "confidence": 0.65,
                        "model_used": "fallback-system"
                    },
                    "sources": [],
                    "metadata": {
                        "total_records_analyzed": total_records,
                        "query_time_ms": int((time.time() - start_time) * 1000),
                        "sources_used": 0,
                        "context_tokens": 0
                    }
                }
            else:
                await asyncio.sleep(0.5)
                continue

    # 6. CONSTRUIR SOURCES
    try:
        sources = build_sources_from_real_data(
            clinical_data.records, 
            similar_chunks,
            sequence_counter=1
        )
    except Exception as e:
        logger.warning(f"Error construyendo sources: {type(e).__name__}")
        sources = []

    # 7. RESPUESTA EXITOSA (Formato EXACTO según especificación)
    response = {
        "status": "success",
        "session_id": input_data.session_id,
        "sequence_chat_id": sequence_chat_id,
        "timestamp": get_iso_timestamp(),
        "patient_info": {
            "patient_id": patient_id,
            "full_name": full_name,
            "document_type": doc_type,
            "document_number": document_number
        },
        "answer": {
            "text": llm_response.text,
            "confidence": getattr(llm_response, 'confidence', 0.94),
            "model_used": getattr(llm_response, 'model_used', 'gpt-4o-mini')
        },
        "sources": sources,
        "metadata": {
            "total_records_analyzed": total_records,
            "query_time_ms": int((time.time() - start_time) * 1000),
            "sources_used": len(sources),
            "context_tokens": getattr(llm_response, 'tokens_used', 0)
        }
    }

    logger.info(f"Query completada exitosamente en {response['metadata']['query_time_ms']}ms")
    return response