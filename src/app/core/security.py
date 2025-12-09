# app/core/security.py

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..models.user import User
from ..database.db_config import settings
import secrets

# SEGURIDAD: Usar variable de entorno en lugar de hardcodear
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Validar que SECRET_KEY sea suficientemente segura
if len(SECRET_KEY) < 32:
    raise ValueError("SECRET_KEY debe tener al menos 32 caracteres")

# Contexto de encriptación para passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuración de Bearer token
security = HTTPBearer()


# ============================================================
# FUNCIONES DE HASHING DE CONTRASEÑAS
# ============================================================

def hash_password(password: str) -> str:
    """
    Hashea una contraseña usando bcrypt.
    
    Args:
        password: Contraseña en texto plano
        
    Returns:
        Hash de la contraseña
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica que una contraseña coincida con su hash.
    
    Args:
        plain_password: Contraseña en texto plano
        hashed_password: Hash almacenado
        
    Returns:
        True si coinciden, False si no
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================
# FUNCIONES DE JWT
# ============================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT.
    
    Args:
        data: Datos a incluir en el token (típicamente {"sub": user_id})
        expires_delta: Tiempo de expiración opcional
        
    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodifica y valida un token JWT.
    
    Args:
        token: Token JWT a decodificar
        
    Returns:
        Payload del token si es válido, None si no
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ============================================================
# DEPENDENCY PARA OBTENER USUARIO ACTUAL
# ============================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency para obtener el usuario autenticado actual.
    Valida el token JWT y retorna el usuario correspondiente.
    
    Args:
        credentials: Credenciales del header Authorization
        db: Sesión de base de datos
        
    Returns:
        Usuario autenticado
        
    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"}
    )
    
    token = credentials.credentials
    
    # Decodificar token
    payload = decode_access_token(token)
    
    if payload is None:
        raise credentials_exception
    
    # Obtener user_id del payload
    user_id: str = payload.get("sub")
    
    if user_id is None:
        raise credentials_exception
    
    # Buscar usuario en la base de datos
    user = db.query(User).filter(User.user_id == int(user_id)).first()
    
    if user is None:
        raise credentials_exception
    
    # Verificar que el usuario esté activo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency adicional que verifica que el usuario esté activo.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    return current_user


# ============================================================
# FUNCIONES DE UTILIDAD PARA SEGURIDAD
# ============================================================

def generate_secure_token(length: int = 32) -> str:
    """
    Genera un token seguro aleatorio.
    
    Args:
        length: Longitud del token en bytes
        
    Returns:
        Token hexadecimal seguro
    """
    return secrets.token_hex(length)