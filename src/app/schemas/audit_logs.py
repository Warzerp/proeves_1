from pydantic import BaseModel, EmailStr
from typing import Optional, Any
from uuid import UUID
from datetime import datetime

class AuditLogBase(BaseModel):
    session_id: UUID
    sequence_chat_id: int
    document_type_id: int
    document_number: str
    question: str
    response_json: Any  # JSONB
    


class AuditLogCreate(AuditLogBase):
    user_id: int


class AuditLogResponse(AuditLogBase):
    audit_log_id: int
    created_at: datetime

    class Config:
        from_attributes = True