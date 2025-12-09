# src/app/services/auth_service.py

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, Dict

from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token


class AuthService:
    """
    Servicio de autenticación que maneja toda la lógica de negocio
    relacionada con registro, login y validación de usuarios.
    """

    @staticmethod
    def register_user(db: Session, user_data) -> User:
        """
        Registra un nuevo usuario en el sistema.
        
        Args:
            db: Sesión de base de datos
            user_data: Esquema UserCreate con los datos del usuario
            
        Returns:
            User: Usuario creado
            
        Raises:
            ValueError: Si el email ya está registrado o la contraseña es inválida
            Exception: Para otros errores de base de datos
        """
        # Validar longitud de contraseña
        if len(user_data.password) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        
        # Verificar si el email ya existe
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ValueError("El correo electrónico ya está registrado")
        
        # Hashear contraseña
        hashed_password = hash_password(user_data.password)
        
        # Crear nuevo usuario
        new_user = User(
            first_name=user_data.first_name,
            middle_name=user_data.middle_name,
            first_surname=user_data.first_surname,
            second_surname=user_data.second_surname,
            email=user_data.email,
            password_hash=hashed_password
        )
        
        try:
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return new_user
        except IntegrityError:
            db.rollback()
            raise ValueError("Error de integridad: el correo ya existe")
        except Exception as e:
            db.rollback()
            raise Exception(f"Error al crear usuario: {str(e)}")

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """
        Autentica un usuario validando email y contraseña.
        
        Args:
            db: Sesión de base de datos
            email: Email del usuario
            password: Contraseña en texto plano
            
        Returns:
            User si las credenciales son correctas, None si no
        """
        # Buscar usuario por email
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            return None
        
        # Verificar contraseña
        if not verify_password(password, user.password_hash):
            return None
        
        return user

    @staticmethod
    def login(db: Session, email: str, password: str) -> Dict[str, str]:
        """
        Procesa el login y genera el token JWT.
        
        Args:
            db: Sesión de base de datos
            email: Email del usuario
            password: Contraseña del usuario
            
        Returns:
            Dict con access_token y token_type
            
        Raises:
            ValueError: Si las credenciales son incorrectas o el usuario está inactivo
        """
        # Autenticar usuario
        user = AuthService.authenticate_user(db, email, password)
        
        if not user:
            raise ValueError("Credenciales incorrectas")
        
        # Verificar que el usuario esté activo
        if not user.is_active:
            raise ValueError("Usuario inactivo. Contacte al administrador")
        
        # Generar token JWT
        token_data = {"sub": str(user.user_id)}
        access_token = create_access_token(token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

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