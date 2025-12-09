# src/app/routers/websocket_chat.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from typing import Optional
import json
import logging
import asyncio
from datetime import datetime, timezone

from app.services.auth_utils import verify_token
from app.services.clinical_service import fetch_patient_and_records
from app.services.vector_search import search_similar_chunks
from app.services.llm_service import llm_service
from app.database.database import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter()

# Configuración de timeouts
STREAMING_CHUNK_DELAY = 0.05
MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10MB
WEBSOCKET_TIMEOUT = 300  # 5 minutos


class ConnectionManager:
    """Gestor de conexiones WebSocket con control de rate limiting"""
    
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}
        self.message_counts: dict[int, list] = {}
        self.max_messages_per_minute = 20
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Conecta un WebSocket y lo asocia a un usuario"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.message_counts[user_id] = []
        logger.info(f"Usuario {user_id} conectado via WebSocket")
    
    def disconnect(self, user_id: int):
        """Desconecta un usuario"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.message_counts:
            del self.message_counts[user_id]
        logger.info(f"Usuario {user_id} desconectado")
    
    def check_rate_limit(self, user_id: int) -> bool:
        """Verifica si el usuario ha excedido el rate limit"""
        now = datetime.now()
        one_minute_ago = now.timestamp() - 60
        
        # Limpiar mensajes antiguos
        if user_id in self.message_counts:
            self.message_counts[user_id] = [
                ts for ts in self.message_counts[user_id] 
                if ts > one_minute_ago
            ]
            
            # Verificar límite
            if len(self.message_counts[user_id]) >= self.max_messages_per_minute:
                return False
            
            # Agregar nuevo mensaje
            self.message_counts[user_id].append(now.timestamp())
        
        return True
    
    async def send_json(self, websocket: WebSocket, data: dict):
        """Envía datos JSON de forma segura"""
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"Error enviando JSON: {str(e)}")
            raise


manager = ConnectionManager()


def get_iso_timestamp() -> str:
    """Retorna timestamp en formato ISO 8601"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitiza el input del usuario.
    
    Args:
        text: Texto a sanitizar
        max_length: Longitud máxima permitida
        
    Returns:
        Texto sanitizado
    """
    # Eliminar caracteres de control excepto saltos de línea
    sanitized = ''.join(char for char in text if char.isprintable() or char in '\n\r')
    
    # Truncar si es muy largo
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()


async def validate_query_message(data: dict) -> tuple[bool, Optional[str]]:
    """
    Valida el mensaje de query recibido.
    
    Returns:
        Tuple (es_valido, mensaje_error)
    """
    required_fields = ["type", "session_id", "document_type_id", "document_number", "question"]
    
    for field in required_fields:
        if field not in data:
            return False, f"Campo requerido faltante: {field}"
    
    # Validar tipos
    if not isinstance(data["document_type_id"], int):
        return False, "document_type_id debe ser un entero"
    
    if not isinstance(data["document_number"], str):
        return False, "document_number debe ser una cadena"
    
    if not isinstance(data["question"], str):
        return False, "question debe ser una cadena"
    
    # Validar rangos
    if data["document_type_id"] not in [1, 2, 3, 4, 5, 6, 7, 8]:
        return False, "document_type_id inválido"
    
    if len(data["question"].strip()) < 5:
        return False, "La pregunta debe tener al menos 5 caracteres"
    
    if len(data["question"]) > 1000:
        return False, "La pregunta no puede exceder 1000 caracteres"
    
    return True, None


@router.websocket("/ws/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="Token JWT de autenticación")
):
    """
    WebSocket endpoint para chat en tiempo real con streaming.
    
    Requiere autenticación JWT via query parameter.
    """
    user_id = None
    
    try:
        # SEGURIDAD: Validar token antes de aceptar conexión
        token_data = verify_token(token)
        
        if not token_data:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token inválido")
            logger.warning("Intento de conexión WebSocket con token inválido")
            return
        
        user_id = token_data["user_id"]
        
        # Conectar usuario
        await manager.connect(websocket, user_id)
        
        # Enviar mensaje de bienvenida
        await manager.send_json(websocket, {
            "type": "connected",
            "message": "Conexión establecida exitosamente",
            "user_id": user_id,
            "timestamp": get_iso_timestamp()
        })
        
        # Loop principal
        while True:
            try:
                # Recibir mensaje con timeout
                raw_data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=WEBSOCKET_TIMEOUT
                )
                
                # Verificar tamaño del mensaje
                if len(raw_data) > MAX_MESSAGE_SIZE:
                    await manager.send_json(websocket, {
                        "type": "error",
                        "error": {
                            "code": "MESSAGE_TOO_LARGE",
                            "message": "El mensaje es demasiado grande"
                        }
                    })
                    continue
                
                # Parsear JSON
                try:
                    data = json.loads(raw_data)
                except json.JSONDecodeError:
                    await manager.send_json(websocket, {
                        "type": "error",
                        "error": {
                            "code": "INVALID_JSON",
                            "message": "Formato JSON inválido"
                        }
                    })
                    continue
                
                msg_type = data.get("type")
                
                # Manejar ping
                if msg_type == "ping":
                    await manager.send_json(websocket, {
                        "type": "pong",
                        "timestamp": get_iso_timestamp()
                    })
                    continue
                
                # Manejar query
                if msg_type == "query":
                    # Rate limiting
                    if not manager.check_rate_limit(user_id):
                        await manager.send_json(websocket, {
                            "type": "error",
                            "error": {
                                "code": "RATE_LIMIT_EXCEEDED",
                                "message": "Has excedido el límite de mensajes por minuto"
                            }
                        })
                        continue
                    
                    # Validar mensaje
                    is_valid, error_msg = await validate_query_message(data)
                    if not is_valid:
                        await manager.send_json(websocket, {
                            "type": "error",
                            "error": {
                                "code": "INVALID_REQUEST",
                                "message": error_msg
                            }
                        })
                        continue
                    
                    # Procesar query
                    await process_query(websocket, data, user_id)
                
                else:
                    await manager.send_json(websocket, {
                        "type": "error",
                        "error": {
                            "code": "UNKNOWN_MESSAGE_TYPE",
                            "message": f"Tipo de mensaje desconocido: {msg_type}"
                        }
                    })
            
            except asyncio.TimeoutError:
                logger.info(f"Timeout WebSocket para usuario {user_id}")
                break
            
            except WebSocketDisconnect:
                logger.info(f"Cliente {user_id} desconectado normalmente")
                break
            
            except Exception as e:
                logger.error(f"Error procesando mensaje de usuario {user_id}: {str(e)}")
                await manager.send_json(websocket, {
                    "type": "error",
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "Error interno del servidor"
                    }
                })
                break
    
    except Exception as e:
        logger.error(f"Error en WebSocket: {str(e)}")
    
    finally:
        if user_id:
            manager.disconnect(user_id)


async def process_query(websocket: WebSocket, data: dict, user_id: int):
    """
    Procesa una query y envía la respuesta con streaming.
    """
    db = SessionLocal()
    
    try:
        # Sanitizar inputs
        question = sanitize_input(data["question"], max_length=1000)
        document_number = sanitize_input(data["document_number"], max_length=50)
        session_id = sanitize_input(data["session_id"], max_length=100)
        
        # Status: Buscando paciente
        await manager.send_json(websocket, {
            "type": "status",
            "message": "Buscando información del paciente"
        })
        
        # Buscar paciente
        patient_info, clinical_data = fetch_patient_and_records(
            db=db,
            document_type_id=data["document_type_id"],
            document_number=document_number
        )
        
        if not patient_info:
            await manager.send_json(websocket, {
                "type": "error",
                "error": {
                    "code": "PATIENT_NOT_FOUND",
                    "message": "Paciente no encontrado"
                }
            })
            return
        
        # Status: Búsqueda vectorial
        await manager.send_json(websocket, {
            "type": "status",
            "message": "Analizando registros médicos"
        })
        
        # Búsqueda vectorial
        similar_chunks = await search_similar_chunks(
            patient_id=patient_info.patient_id,
            question=question,
            k=15,
            min_score=0.3
        )
        
        # Construir contexto
        from app.routers.query import build_context_from_real_data
        context = build_context_from_real_data(
            patient_info=patient_info,
            clinical_records=clinical_data.records,
            similar_chunks=similar_chunks
        )
        
        # Status: Generando respuesta
        await manager.send_json(websocket, {
            "type": "status",
            "message": "Generando respuesta"
        })
        
        # Inicio de streaming
        await manager.send_json(websocket, {
            "type": "stream_start"
        })
        
        # Llamar al LLM
        llm_response = await llm_service.run_llm(
            question=question,
            context=context
        )
        
        # Enviar tokens uno por uno
        if llm_response and llm_response.text:
            words = llm_response.text.split()
            for word in words:
                await manager.send_json(websocket, {
                    "type": "token",
                    "token": word + " "
                })
                await asyncio.sleep(STREAMING_CHUNK_DELAY)
        
        # Fin de streaming
        await manager.send_json(websocket, {
            "type": "stream_end"
        })
        
        # Construir sources
        from app.routers.query import build_sources_from_real_data
        sources = build_sources_from_real_data(
            clinical_data.records,
            similar_chunks,
            sequence_counter=1
        )
        
        # Respuesta completa
        await manager.send_json(websocket, {
            "type": "complete",
            "session_id": session_id,
            "timestamp": get_iso_timestamp(),
            "patient_info": {
                "patient_id": patient_info.patient_id,
                "full_name": f"{patient_info.first_name} {patient_info.first_surname}",
                "document_type": "CC",
                "document_number": document_number
            },
            "answer": {
                "text": llm_response.text,
                "confidence": llm_response.confidence,
                "model_used": llm_response.model_used
            },
            "sources": sources,
            "metadata": {
                "total_records_analyzed": len(clinical_data.records.appointments) + 
                                        len(clinical_data.records.diagnoses) +
                                        len(clinical_data.records.prescriptions),
                "vector_chunks_used": len(similar_chunks),
                "query_time_ms": 0
            }
        })
    
    except Exception as e:
        logger.error(f"Error procesando query: {str(e)}")
        await manager.send_json(websocket, {
            "type": "error",
            "error": {
                "code": "PROCESSING_ERROR",
                "message": "Error procesando la solicitud"
            }
        })
    
    finally:
        db.close()