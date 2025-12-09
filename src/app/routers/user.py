# src/app/routers/user.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.schemas.user import UserResponse, UserUpdate
from app.database.database import get_db
from app.services.user import UserService  # ← Import directo
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="Listar todos los usuarios"
)
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lista todos los usuarios con paginación.
    
    - **skip**: Número de registros a saltar (default: 0)
    - **limit**: Número máximo de registros (default: 100, max: 100)
    """
    if limit > 100:
        limit = 100
    
    users = UserService.get_all_users(db, skip=skip, limit=limit)
    return users


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Obtener perfil del usuario actual"
)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Obtiene el perfil del usuario autenticado actualmente.
    Requiere token JWT válido en el header Authorization.
    """
    return current_user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Obtener usuario por ID"
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene la información de un usuario específico por su ID.
    Requiere autenticación.
    """
    user = UserService.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return user


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario"
)
def update_user(
    user_id: int,
    update_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualiza la información de un usuario.
    Solo el mismo usuario o un administrador pueden actualizar.
    """
    # Verificar que el usuario solo pueda actualizar su propio perfil
    if current_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para actualizar este usuario"
        )
    
    try:
        # Convertir el schema a dict, excluyendo valores None
        update_dict = update_data.model_dump(exclude_unset=True)
        
        updated_user = UserService.update_user(db, user_id, update_dict)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        return updated_user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar usuario: {str(e)}"
        )


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar parcialmente un usuario"
)
def partial_update_user(
    user_id: int,
    update_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualiza parcialmente la información de un usuario (PATCH).
    Solo el mismo usuario o un administrador pueden actualizar.
    """
    if current_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para actualizar este usuario"
        )
    
    try:
        update_dict = update_data.model_dump(exclude_unset=True)
        updated_user = UserService.update_user(db, user_id, update_dict)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        return updated_user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar usuario: {str(e)}"
        )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar usuario"
)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Desactiva un usuario (soft delete).
    El usuario seguirá en la base de datos pero no podrá iniciar sesión.
    """
    # Verificar permisos
    if current_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para desactivar este usuario"
        )
    
    try:
        success = UserService.deactivate_user(db, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        return None
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al desactivar usuario: {str(e)}"
        )