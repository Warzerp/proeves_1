# src/app/services/clinical_service.py
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

# Modelos SQLAlchemy
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.medical_record import MedicalRecord
from app.models.prescription import Prescription
from app.models.diagnosis import Diagnosis
from app.models.record_diagnosis import RecordDiagnosis

# Schemas Pydantic
from app.schemas.clinical import (
    PatientInfo,
    AppointmentDTO,
    MedicalRecordDTO,
    PrescriptionDTO,
    DiagnosisDTO,
    ClinicalRecords,
    ClinicalDataResult
)

logger = logging.getLogger(__name__)

# ============================================================================ 
# P2-2: Función para obtener paciente por documento
# ============================================================================

def get_patient_by_document(
    db: Session,
    document_type_id: int,
    document_number: str
) -> Optional[PatientInfo]:
    """
    Busca paciente por document_type_id y document_number.
    Devuelve PatientInfo si existe, o None si no se encuentra.
    """
    try:
        patient = (
            db.query(Patient)
            .filter(
                Patient.document_type_id == document_type_id,
                Patient.document_number == document_number
            )
            .one_or_none()
        )
    except Exception:
        logger.exception("Error ejecutando query get_patient_by_document")
        raise

    if not patient:
        return None

    # ✅ Mapear manualmente para manejar registration_date correctamente
    return PatientInfo(
        patient_id=patient.patient_id,
        first_name=patient.first_name,
        middle_name=patient.middle_name,
        first_surname=patient.first_surname,
        second_surname=patient.second_surname,
        birth_date=patient.birth_date,
        gender=patient.gender,
        email=patient.email,
        document_type_id=patient.document_type_id,
        document_number=patient.document_number,
        registration_date=patient.registration_date,  # Ya es datetime desde la BD
        active=patient.active,
        blood_type=patient.blood_type
    )


# ============================================================================ 
# P2-3: Funciones para obtener datos clínicos por paciente
# ============================================================================

def get_appointments_by_patient(db: Session, patient_id: int) -> List[AppointmentDTO]:
    """
    Obtiene todas las citas de un paciente con información del doctor,
    ordenadas por fecha descendente.
    """
    try:
        # Query optimizada con DISTINCT ON para evitar duplicados
        # Toma la primera especialidad activa si el doctor tiene varias
        query = text("""
            SELECT DISTINCT ON (a.appointment_id)
                a.appointment_id,
                a.patient_id,
                a.doctor_id,
                a.room_id,
                a.appointment_date,
                a.start_time,
                a.end_time,
                a.appointment_type,
                a.status,
                a.reason,
                a.creation_date,
                d.first_name || ' ' || d.last_name AS doctor_name,
                s.specialty_name,
                d.medical_license_number
            FROM smart_health.appointments a
            INNER JOIN smart_health.doctors d ON a.doctor_id = d.doctor_id
            LEFT JOIN smart_health.doctor_specialties ds ON d.doctor_id = ds.doctor_id AND ds.is_active = TRUE
            LEFT JOIN smart_health.specialties s ON ds.specialty_id = s.specialty_id
            WHERE a.patient_id = :patient_id
            ORDER BY a.appointment_id, ds.certification_date DESC NULLS LAST
        """)
        
        result = db.execute(query, {"patient_id": patient_id})
        rows = result.fetchall()
        
        # Convertir a DTOs
        appointments = []
        for row in rows:
            apt_dict = {
                'appointment_id': row.appointment_id,
                'patient_id': row.patient_id,
                'doctor_id': row.doctor_id,
                'room_id': row.room_id,
                'appointment_date': row.appointment_date,
                'start_time': row.start_time,
                'end_time': row.end_time,
                'appointment_type': row.appointment_type,
                'status': row.status,
                'reason': row.reason,
                'creation_date': row.creation_date,
                # Campos del doctor
                'doctor_name': row.doctor_name,
                'specialty_name': row.specialty_name,
                'medical_license_number': row.medical_license_number,
            }
            appointments.append(AppointmentDTO(**apt_dict))
        
        # Ordenar por fecha después de eliminar duplicados
        appointments.sort(key=lambda x: (x.appointment_date, x.start_time or x.creation_date), reverse=True)
        
        return appointments
        
    except Exception:
        logger.exception("Error ejecutando query get_appointments_by_patient")
        raise


def get_medical_records_by_patient(db: Session, patient_id: int) -> List[MedicalRecordDTO]:
    """
    Obtiene todos los registros médicos de un paciente, ordenados por fecha descendente.
    """
    try:
        records = (
            db.query(MedicalRecord)
            .filter(MedicalRecord.patient_id == patient_id)
            .order_by(MedicalRecord.registration_datetime.desc())
            .all()
        )
    except Exception:
        logger.exception("Error ejecutando query get_medical_records_by_patient")
        raise

    return [MedicalRecordDTO.from_orm(rec) for rec in records]


def get_prescriptions_by_patient(db: Session, patient_id: int) -> List[PrescriptionDTO]:
    """
    Obtiene todas las prescripciones de un paciente con el nombre del medicamento.
    """
    try:
        query = text("""
            SELECT 
                p.prescription_id,
                p.medical_record_id,
                p.medication_id,
                p.dosage,
                p.frequency,
                p.duration,
                p.instruction,
                p.prescription_date,
                p.alert_generated,
                COALESCE(m.commercial_name, 'Medicamento no especificado') AS medication_name,
                m.active_ingredient,
                m.presentation AS pharmaceutical_form
            FROM smart_health.prescriptions p
            INNER JOIN smart_health.medical_records mr 
                ON p.medical_record_id = mr.medical_record_id
            LEFT JOIN smart_health.medications m 
                ON p.medication_id = m.medication_id
            WHERE mr.patient_id = :patient_id
            ORDER BY p.prescription_date DESC
        """)
        
        result = db.execute(query, {"patient_id": patient_id})
        rows = result.fetchall()
        
        prescriptions = []
        for row in rows:
            presc_dict = {
                'prescription_id': row.prescription_id,
                'medical_record_id': row.medical_record_id,
                'medication_id': row.medication_id,
                'dosage': row.dosage,
                'frequency': row.frequency,
                'duration': row.duration,
                'instruction': row.instruction,
                'prescription_date': row.prescription_date,
                'alert_generated': row.alert_generated,
                'medication_name': row.medication_name,
                'active_ingredient': row.active_ingredient,
                'pharmaceutical_form': row.pharmaceutical_form,
            }
            prescriptions.append(PrescriptionDTO(**presc_dict))
        
        return prescriptions
        
    except Exception:
        logger.exception("Error ejecutando query get_prescriptions_by_patient")
        raise


def get_diagnoses_by_patient(db: Session, patient_id: int) -> List[DiagnosisDTO]:
    """
    Obtiene todos los diagnósticos de un paciente con la fecha del registro médico.
    """
    try:
        # ✅ Query con SQL directo para obtener la fecha del medical_record
        query = text("""
            SELECT 
                rd.record_diagnosis_id,
                d.diagnosis_id,
                d.icd_code,
                d.description,
                rd.diagnosis_type,
                rd.note,
                mr.registration_datetime AS diagnosis_date
            FROM smart_health.diagnoses d
            INNER JOIN smart_health.record_diagnoses rd 
                ON d.diagnosis_id = rd.diagnosis_id
            INNER JOIN smart_health.medical_records mr 
                ON rd.medical_record_id = mr.medical_record_id
            WHERE mr.patient_id = :patient_id
            ORDER BY mr.registration_datetime DESC
        """)
        
        result = db.execute(query, {"patient_id": patient_id})
        rows = result.fetchall()
        
        # Convertir a DTOs
        diagnoses = []
        for row in rows:
            diag_dict = {
                'record_diagnosis_id': row.record_diagnosis_id,
                'diagnosis_id': row.diagnosis_id,
                'icd_code': row.icd_code,
                'description': row.description,
                'diagnosis_type': row.diagnosis_type,
                'note': row.note,
                # ✅ Fecha del diagnóstico (del medical_record)
                'diagnosis_date': row.diagnosis_date,
            }
            diagnoses.append(DiagnosisDTO(**diag_dict))
        
        return diagnoses
        
    except Exception:
        logger.exception("Error ejecutando query get_diagnoses_by_patient")
        raise


# ============================================================================ 
# Función principal que integra todo (usada por P1)
# ============================================================================

def fetch_patient_and_records(
    db: Session,
    document_type_id: int,
    document_number: str
) -> Tuple[Optional[PatientInfo], ClinicalDataResult]:
    """
    Función principal que obtiene paciente + todos sus registros clínicos.

    Returns:
        Tupla con:
        - PatientInfo o None (si no existe el paciente)
        - ClinicalDataResult con todos los registros y flag has_data
    """
    # 1. Buscar paciente
    patient = get_patient_by_document(db, document_type_id, document_number)

    if not patient:
        # Paciente no encontrado
        return None, ClinicalDataResult(
            patient=None,
            records=ClinicalRecords(),
            has_data=False
        )

    # 2. Obtener todos los registros clínicos
    appointments = get_appointments_by_patient(db, patient.patient_id)
    medical_records = get_medical_records_by_patient(db, patient.patient_id)
    prescriptions = get_prescriptions_by_patient(db, patient.patient_id)
    diagnoses = get_diagnoses_by_patient(db, patient.patient_id)

    # 3. Agrupar en ClinicalRecords
    records = ClinicalRecords(
        appointments=appointments,
        medical_records=medical_records,
        prescriptions=prescriptions,
        diagnoses=diagnoses
    )

    # 4. Determinar si hay datos (P2-5)
    has_data = any([
        len(appointments) > 0,
        len(medical_records) > 0,
        len(prescriptions) > 0,
        len(diagnoses) > 0
    ])

    # 5. Retornar resultado completo
    return patient, ClinicalDataResult(
        patient=patient,
        records=records,
        has_data=has_data
    )