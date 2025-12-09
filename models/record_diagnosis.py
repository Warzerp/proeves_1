from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class RecordDiagnosis(Base):
    __tablename__ = "record_diagnoses"
    __table_args__ = {"schema": "smart_health"}

    record_diagnosis_id = Column(Integer, primary_key=True)
    medical_record_id = Column(Integer)
    diagnosis_id = Column(Integer)
    diagnosis_type = Column(String)
    note = Column(String)

