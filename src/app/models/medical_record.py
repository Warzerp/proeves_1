from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class MedicalRecord(Base):
    __tablename__ = "medical_records"
    __table_args__ = {"schema": "smart_health"}

    medical_record_id = Column(Integer, primary_key=True)
    patient_id = Column(Integer)
    doctor_id = Column(Integer)
    primary_diagnosis_id = Column(Integer)
    registration_datetime = Column(DateTime)
    record_type = Column(String)
    summary_text = Column(String)
    vital_signs = Column(String)
