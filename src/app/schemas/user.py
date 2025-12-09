# app/schemas/user.py

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Schema base con campos comunes de usuario"""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=50)
    middle_name: Optional[str] = Field(None, max_length=50)
    first_surname: str = Field(..., min_length=1, max_length=50)
    second_surname: Optional[str] = Field(None, max_length=50)


class UserCreate(UserBase):
    """Schema para crear un nuevo usuario"""
    password: str = Field(..., min_length=6, max_length=100, description="Contraseña del usuario")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "juan.perez@example.com",
                "first_name": "Juan",
                "middle_name": "Carlos",
                "first_surname": "Pérez",
                "second_surname": "González",
                "password": "password123"
            }
        }
    )


class UserUpdate(BaseModel):
    """
    Schema para actualizar un usuario existente.
    Todos los campos son opcionales.
    """
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    middle_name: Optional[str] = Field(None, max_length=50)
    first_surname: Optional[str] = Field(None, min_length=1, max_length=50)
    second_surname: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "first_name": "Juan",
                "middle_name": "Carlos",
                "first_surname": "Pérez",
                "second_surname": "González",
                "email": "nuevo.email@example.com"
            }
        }
    )


class UserResponse(BaseModel):
    """
    Schema para respuestas que incluyen datos del usuario.
    No incluye la contraseña por seguridad.
    """
    user_id: int
    email: EmailStr
    first_name: str
    middle_name: Optional[str] = None
    first_surname: str
    second_surname: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": 1,
                "email": "juan.perez@example.com",
                "first_name": "Juan",
                "middle_name": "Carlos",
                "first_surname": "Pérez",
                "second_surname": "González",
                "is_active": True,
                "created_at": "2025-11-22T14:30:00",
                "updated_at": "2025-11-22T14:30:00"
            }
        }
    )


class UserLogin(BaseModel):
    """Schema para login de usuario"""
    email: EmailStr
    password: str = Field(..., min_length=6)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "juan.perez@example.com",
                "password": "password123"
            }
        }
    )


class TokenResponse(BaseModel):
    """Schema para respuesta de autenticación con token"""
    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
    )