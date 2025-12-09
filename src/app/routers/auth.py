# src/app/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from app.database.database import get_db
from app.services.auth_service import AuthService  # ← Import directo

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
    description="Crea un nuevo usuario en el sistema con los datos proporcionados"
)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo usuario en el sistema.
    
    - **first_name**: Primer nombre (requerido)
    - **middle_name**: Segundo nombre (opcional)
    - **first_surname**: Primer apellido (requerido)
    - **second_surname**: Segundo apellido (opcional)
    - **email**: Correo electrónico único (requerido)
    - **password**: Contraseña (requerido, mínimo 6 caracteres)
    
    Returns:
        UserResponse: Datos del usuario creado (sin contraseña)
    
    Raises:
        HTTPException 400: Si el email ya está registrado o la contraseña es inválida
        HTTPException 500: Error interno del servidor
    """
    try:
        new_user = AuthService.register_user(db, user_data)
        return new_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
    description="Autentica al usuario y devuelve un token JWT"
)
def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Inicia sesión y devuelve un token de acceso.
    
    - **email**: Correo electrónico del usuario
    - **password**: Contraseña del usuario
    
    Returns:
        TokenResponse: Token JWT y tipo de token
        
    Raises:
        HTTPException 401: Si las credenciales son incorrectas o el usuario está inactivo
        HTTPException 500: Error interno del servidor
    
    El token JWT debe incluirse en el header Authorization de peticiones subsecuentes:
    ```
    Authorization: Bearer <token>
    ```
    """
    try:
        token_data = AuthService.login(db, login_data.email, login_data.password)
        return TokenResponse(**token_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )