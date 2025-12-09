# src/app/models/patient.py
from sqlalchemy import Column, Integer, String, Date, Boolean, TIMESTAMP, CheckConstraint
from sqlalchemy.orm import relationship
from app.database.database import Base
from datetime import datetime

class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = {"schema": "smart_health"}

    patient_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    middle_name = Column(String(50))
    first_surname = Column(String(50), nullable=False)
    second_surname = Column(String(50))
    birth_date = Column(Date, nullable=False)
    gender = Column(String(1), CheckConstraint("gender IN ('M', 'F', 'O')"), nullable=False)
    email = Column(String(100), unique=True)
    document_type_id = Column(Integer, nullable=False)
    document_number = Column(String(50), nullable=False)
    registration_date = Column(TIMESTAMP, default=datetime.utcnow)  # ✅ TIMESTAMP no DATE
    active = Column(Boolean, default=True)
    blood_type = Column(String(5))

    # ✅ Relationships usando strings para evitar imports circulares
    # appointments = relationship("Appointment", back_populates="patient")
    # medical_records = relationship("MedicalRecord", back_populates="patient")