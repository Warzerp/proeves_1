# app/services/user_service.py

from sqlalchemy.orm import Session
from ..models.user import User
from typing import Optional, List


class UserService:
    """
    Servicio que maneja operaciones relacionadas con usuarios.
    """

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """
        Obtiene un usuario por su ID.
        
        Args:
            db: Sesión de base de datos
            user_id: ID del usuario
            
        Returns:
            User si existe, None si no
        """
        return db.query(User).filter(User.user_id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """
        Obtiene un usuario por su email.
        
        Args:
            db: Sesión de base de datos
            email: Email del usuario
            
        Returns:
            User si existe, None si no
        """
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Obtiene todos los usuarios con paginación.
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de usuarios
        """
        return db.query(User).offset(skip).limit(limit).all()

    @staticmethod
    def update_user(db: Session, user_id: int, update_data: dict) -> Optional[User]:
        """
        Actualiza los datos de un usuario.
        
        Args:
            db: Sesión de base de datos
            user_id: ID del usuario a actualizar
            update_data: Diccionario con los campos a actualizar
            
        Returns:
            User actualizado o None si no existe
            
        Raises:
            ValueError: Si hay error en la validación
            Exception: Para otros errores
        """
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return None
        
        # Actualizar solo los campos proporcionados
        for field, value in update_data.items():
            if value is not None and hasattr(user, field):
                setattr(user, field, value)
        
        try:
            db.commit()
            db.refresh(user)
            return user
        except Exception as e:
            db.rollback()
            raise Exception(f"Error al actualizar usuario: {str(e)}")

    @staticmethod
    def deactivate_user(db: Session, user_id: int) -> bool:
        """
        Desactiva un usuario (soft delete).
        
        Args:
            db: Sesión de base de datos
            user_id: ID del usuario
            
        Returns:
            True si se desactivó correctamente, False si no existe
        """
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return False
        
        user.is_active = False
        
        try:
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise Exception(f"Error al desactivar usuario: {str(e)}")

    @staticmethod
    def activate_user(db: Session, user_id: int) -> bool:
        """
        Activa un usuario previamente desactivado.
        
        Args:
            db: Sesión de base de datos
            user_id: ID del usuario
            
        Returns:
            True si se activó correctamente, False si no existe
        """
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return False
        
        user.is_active = True
        
        try:
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise Exception(f"Error al activar usuario: {str(e)}")

    @staticmethod
    def delete_user_permanently(db: Session, user_id: int) -> bool:
        """
        Elimina permanentemente un usuario de la base de datos.
        ADVERTENCIA: Esta operación no se puede deshacer.
        
        Args:
            db: Sesión de base de datos
            user_id: ID del usuario
            
        Returns:
            True si se eliminó, False si no existe
        """
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return False
        
        try:
            db.delete(user)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise Exception(f"Error al eliminar usuario: {str(e)}")