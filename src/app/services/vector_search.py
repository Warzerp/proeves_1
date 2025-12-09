from typing import List
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.schemas.rag import SimilarChunk
from app.services.llm_client import get_embedding
from app.database.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

# Configuración
DEFAULT_TOP_K = 15
MAX_PER_TABLE = 10
DEFAULT_YEARS_BACK = 5
DEFAULT_MIN_SCORE = 0.3


async def search_similar_chunks(
    patient_id: int,
    question: str,
    k: int = DEFAULT_TOP_K,
    min_score: float = DEFAULT_MIN_SCORE,
    allowed_sources: list[str] | None = None,
) -> List[SimilarChunk]:
    """
    Devuelve los k chunks más relevantes para la pregunta de un paciente.

    Fuentes consultadas:
    - appointments
    - medical_records
    - diagnoses
    - prescriptions
    """

    # Generar embedding de la pregunta
    question_embedding = await get_embedding(question)

    if isinstance(question_embedding, list):
        embedding_str = '[' + ','.join(map(str, question_embedding)) + ']'
    else:
        embedding_str = question_embedding

    db: Session = SessionLocal()
    try:
        chunks: List[SimilarChunk] = []

        # ================================
        # 1. APPOINTMENTS
        # ================================
        try:
            sql_appointments = text("""
                SELECT DISTINCT ON (a.appointment_id)
                    a.appointment_id AS source_id,
                    a.patient_id AS patient_id,
                    a.reason AS text,
                    a.appointment_date AS date,
                    d.first_name || ' ' || d.last_name AS doctor_name,
                    s.specialty_name,
                    d.medical_license_number,
                    1 - (a.reason_embedding <-> CAST(:q_emb AS vector)) AS relevance_score
                FROM smart_health.appointments a
                INNER JOIN smart_health.doctors d ON a.doctor_id = d.doctor_id
                LEFT JOIN smart_health.doctor_specialties ds 
                       ON d.doctor_id = ds.doctor_id AND ds.is_active = TRUE
                LEFT JOIN smart_health.specialties s ON ds.specialty_id = s.specialty_id
                WHERE a.patient_id = :patient_id
                    AND a.reason_embedding IS NOT NULL
                    AND a.reason IS NOT NULL
                    AND a.appointment_date >= NOW() - INTERVAL '5 years'
                ORDER BY a.appointment_id, 
                         ds.certification_date DESC NULLS LAST, 
                         a.reason_embedding <-> CAST(:q_emb AS vector)
                LIMIT :limit_value
            """)

            rows = db.execute(
                sql_appointments,
                {
                    "patient_id": patient_id,
                    "q_emb": embedding_str,
                    "limit_value": min(k, MAX_PER_TABLE),
                },
            ).fetchall()

            for row in rows:
                chunks.append(
                    SimilarChunk(
                        source_type="appointment",
                        source_id=row.source_id,
                        patient_id=row.patient_id,
                        chunk_text=row.text,
                        date=row.date,
                        relevance_score=float(row.relevance_score),
                        doctor_name=row.doctor_name,
                        specialty_name=row.specialty_name,
                        medical_license=row.medical_license_number,
                    )
                )
        except Exception as e:
            logger.error(f"Error al consultar appointments: {e}")

        # ================================
        # 2. MEDICAL RECORDS
        # ================================
        try:
            sql_medical_records = text("""
                SELECT
                    medical_record_id AS source_id,
                    patient_id AS patient_id,
                    summary_text AS text,
                    registration_datetime AS date,
                    1 - (summary_embedding <-> CAST(:q_emb AS vector)) AS relevance_score
                FROM smart_health.medical_records
                WHERE patient_id = :patient_id
                    AND summary_embedding IS NOT NULL
                    AND summary_text IS NOT NULL
                    AND registration_datetime >= NOW() - INTERVAL '5 years'
                ORDER BY summary_embedding <-> CAST(:q_emb AS vector)
                LIMIT :limit_value
            """)

            rows_mr = db.execute(
                sql_medical_records,
                {
                    "patient_id": patient_id,
                    "q_emb": embedding_str,
                    "limit_value": min(k, MAX_PER_TABLE),
                },
            ).fetchall()

            for row in rows_mr:
                chunks.append(
                    SimilarChunk(
                        source_type="medical_record",
                        source_id=row.source_id,
                        patient_id=row.patient_id,
                        chunk_text=row.text,
                        date=row.date,
                        relevance_score=float(row.relevance_score),
                    )
                )
        except Exception as e:
            logger.error(f"Error al consultar medical_records: {e}")

        # ================================
        # 3. DIAGNOSES
        # ================================
        try:
            sql_diagnoses = text("""
                SELECT
                    d.diagnosis_id AS source_id,
                    mr.patient_id AS patient_id,
                    d.icd_code || ' - ' || d.description AS text,
                    mr.registration_datetime AS date,
                    1 - (d.description_embedding <-> CAST(:q_emb AS vector)) AS relevance_score
                FROM smart_health.diagnoses d
                INNER JOIN smart_health.record_diagnoses rd 
                        ON d.diagnosis_id = rd.diagnosis_id
                INNER JOIN smart_health.medical_records mr 
                        ON rd.medical_record_id = mr.medical_record_id
                WHERE mr.patient_id = :patient_id
                    AND d.description_embedding IS NOT NULL
                    AND d.description IS NOT NULL
                    AND mr.registration_datetime >= NOW() - INTERVAL '5 years'
                ORDER BY d.description_embedding <-> CAST(:q_emb AS vector)
                LIMIT :limit_value
            """)

            rows_diag = db.execute(
                sql_diagnoses,
                {
                    "patient_id": patient_id,
                    "q_emb": embedding_str,
                    "limit_value": min(k, MAX_PER_TABLE),
                },
            ).fetchall()

            for row in rows_diag:
                chunks.append(
                    SimilarChunk(
                        source_type="diagnosis",
                        source_id=row.source_id,
                        patient_id=row.patient_id,
                        chunk_text=row.text,
                        date=row.date,
                        relevance_score=float(row.relevance_score),
                    )
                )
        except Exception as e:
            logger.error(f"Error al consultar diagnoses: {e}")

        # ================================
        # 4. PRESCRIPTIONS
        # ================================
        try:
            sql_prescriptions = text("""
                SELECT
                    p.prescription_id AS source_id,
                    mr.patient_id AS patient_id,
                    m.commercial_name || ' - ' || 
                    COALESCE(p.dosage, '') || ' - ' || 
                    COALESCE(p.frequency, '') AS text,
                    p.prescription_date AS date,
                    1 - (m.medication_embedding <-> CAST(:q_emb AS vector)) AS relevance_score
                FROM smart_health.prescriptions p
                INNER JOIN smart_health.medical_records mr 
                        ON p.medical_record_id = mr.medical_record_id
                INNER JOIN smart_health.medications m 
                        ON p.medication_id = m.medication_id
                WHERE mr.patient_id = :patient_id
                    AND m.medication_embedding IS NOT NULL
                    AND m.commercial_name IS NOT NULL
                    AND p.prescription_date >= NOW() - INTERVAL '5 years'
                ORDER BY m.medication_embedding <-> CAST(:q_emb AS vector)
                LIMIT :limit_value
            """)

            rows_presc = db.execute(
                sql_prescriptions,
                {
                    "patient_id": patient_id,
                    "q_emb": embedding_str,
                    "limit_value": min(k, MAX_PER_TABLE),
                },
            ).fetchall()

            for row in rows_presc:
                chunks.append(
                    SimilarChunk(
                        source_type="prescription",
                        source_id=row.source_id,
                        patient_id=row.patient_id,
                        chunk_text=row.text,
                        date=row.date,
                        relevance_score=float(row.relevance_score),
                    )
                )
        except Exception as e:
            logger.error(f"Error al consultar prescriptions: {e}")

        # ================================
        # FILTRADO FINAL
        # ================================
        chunks = [c for c in chunks if c.relevance_score >= min_score]

        if allowed_sources is not None:
            chunks = [c for c in chunks if c.source_type in allowed_sources]

        chunks.sort(key=lambda c: c.relevance_score, reverse=True)
        chunks = chunks[:k]

        return chunks

    except Exception as e:
        logger.error(f"Error general en vector search: {e}")
        return []
    finally:
        db.close()
