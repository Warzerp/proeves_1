# src/app/services/auth_utils.py
"""
Utilidades de autenticación para WebSocket y otros usos.
"""

from typing import Optional, Dict
from jose import jwt, JWTError
from app.core.security import SECRET_KEY, ALGORITHM
import logging

logger = logging.getLogger(__name__)


def verify_token(token: str) -> Optional[Dict]:
    """
    Verifica y decodifica un token JWT.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            logger.warning("Token sin campo 'sub'")
            return None
        
        return {
            "user_id": int(user_id),
            "exp": payload.get("exp")
        }
        
    except JWTError as e:
        logger.warning(f"Token JWT inválido: {type(e).__name__}")
        return None
    except ValueError as e:
        logger.warning(f"Error convirtiendo user_id: {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado verificando token: {type(e).__name__}: {e}")
        return None