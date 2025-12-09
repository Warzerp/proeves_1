from sqlalchemy import Column, Integer, Date, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Prescription(Base):
    __tablename__ = "prescriptions"
    __table_args__ = {"schema": "smart_health"}

    prescription_id = Column(Integer, primary_key=True)
    medical_record_id = Column(Integer)
    medication_id = Column(Integer)
    dosage = Column(String)
    frequency = Column(String)
    duration = Column(String)
    instruction = Column(String)
    prescription_date = Column(Date)
    alert_generated = Column(Integer)
