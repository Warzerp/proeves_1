from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Diagnosis(Base):
    __tablename__ = "diagnoses"
    __table_args__ = {"schema": "smart_health"}

    diagnosis_id = Column(Integer, primary_key=True)
    icd_code = Column(String)
    description = Column(String)

