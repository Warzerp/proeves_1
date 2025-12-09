from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database.database import Base



class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {"schema": "smart_health"}

    audit_log_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("smart_health.users.user_id"), nullable=False)
    session_id = Column(UUID(as_uuid=True), nullable=False)
    sequence_chat_id = Column(Integer, nullable=False)
    document_type_id = Column(Integer, nullable=False)
    document_number = Column(String(30), nullable=False)
    question = Column(Text, nullable=False)
    response_json = Column(JSONB, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # relación con users
    user = relationship("User", back_populates="audit_logs")