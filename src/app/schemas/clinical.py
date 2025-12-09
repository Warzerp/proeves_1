# src/app/schemas/clinical.py
from pydantic import BaseModel, Field
from typing import Optional, List, Union
from datetime import date, time, datetime

# ============================================================================
# P2-1: PatientInfo - InformaciÃ³n bÃ¡sica del paciente
# ============================================================================

class PatientInfo(BaseModel):
    patient_id: int
    first_name: str
    middle_name: Optional[str] = None
    first_surname: str
    second_surname: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    document_type_id: int
    document_number: str
    registration_date: Optional[datetime] = None  # ✅ Cambiar de date a datetime
    active: bool = True
    blood_type: Optional[str] = None

    class Config:
        from_attributes = True  # Antes era orm_mode = True


# ============================================================================
# P2-3: DTOs para registros clÃ­nicos
# ============================================================================

class AppointmentDTO(BaseModel):
    """DTO para citas mÃ©dicas con informaciÃ³n del doctor"""
    appointment_id: int
    patient_id: int
    doctor_id: int
    room_id: Optional[int] = None
    appointment_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    appointment_type: Optional[str] = None
    status: str
    reason: Optional[str] = None
    creation_date: Optional[datetime] = None
    
    # âœ… Campos del doctor (agregados mediante JOIN)
    doctor_name: Optional[str] = None
    specialty_name: Optional[str] = None
    medical_license_number: Optional[str] = None

    class Config:
        from_attributes = True


class MedicalRecordDTO(BaseModel):
    """DTO para registros médicos"""
    medical_record_id: int
    patient_id: int
    doctor_id: int
    primary_diagnosis_id: Optional[int] = None
    registration_datetime: datetime
    record_type: Optional[str] = None
    summary_text: Optional[str] = None
    vital_signs: Optional[Union[dict, str]] = None  # ✅ Esto debe estar exactamente así

    class Config:
        from_attributes = True


class PrescriptionDTO(BaseModel):
    """DTO para prescripciones con informaciÃ³n del medicamento"""
    prescription_id: int
    medical_record_id: int
    medication_id: int
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instruction: Optional[str] = None
    prescription_date: Optional[datetime] = None
    alert_generated: Optional[bool] = False
    
    # âœ… Campos del medicamento (agregados mediante JOIN)
    medication_name: Optional[str] = "Medicamento no especificado"
    active_ingredient: Optional[str] = None
    pharmaceutical_form: Optional[str] = None

    class Config:
        from_attributes = True


class DiagnosisDTO(BaseModel):
    """DTO para diagnÃ³sticos"""
    record_diagnosis_id: int
    diagnosis_id: int
    icd_code: str
    description: str
    diagnosis_type: Optional[str] = None
    note: Optional[str] = None
    
    # âœ… Fecha del diagnÃ³stico (del medical_record)
    diagnosis_date: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# P2-4: Agrupador de todos los registros clÃ­nicos
# ============================================================================

class ClinicalRecords(BaseModel):
    """Agrupa todos los registros clÃ­nicos de un paciente"""
    appointments: List[AppointmentDTO] = Field(default_factory=list)
    medical_records: List[MedicalRecordDTO] = Field(default_factory=list)
    prescriptions: List[PrescriptionDTO] = Field(default_factory=list)
    diagnoses: List[DiagnosisDTO] = Field(default_factory=list)


# ============================================================================
# P2-5: Resultado completo con flag has_data
# ============================================================================

class ClinicalDataResult(BaseModel):
    """Resultado completo de la bÃºsqueda de datos clÃ­nicos"""
    patient: Optional[PatientInfo] = None
    records: ClinicalRecords
    has_data: bool = False