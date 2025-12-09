from sqlalchemy import Column, Integer, Date, Time, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = {"schema": "smart_health"}

    appointment_id = Column(Integer, primary_key=True)
    patient_id = Column(Integer)
    doctor_id = Column(Integer)
    appointment_date = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)
    appointment_type = Column(String)
    status = Column(String)
    reason = Column(String)
    creation_date = Column(String)
