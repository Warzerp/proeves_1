# src/app/routers/websocket_chat.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import json
import logging
import asyncio
from datetime import datetime

from app.services.llm_service import llm_service
from app.services.clinical_service import fetch_patient_and_records
from app.services.vector_search import search_similar_chunks
from app.database.database import get_db
from app.routers.query import build_context_from_real_data, get_document_type_name
from app.services.auth import verify_token

router = APIRouter(prefix="/ws", tags=["WebSocket"])
logger = logging.getLogger(__name__)
security = HTTPBearer()

# Timeout configuration
VECTOR_SEARCH_TIMEOUT = 10
LLM_TIMEOUT = 30


class ConnectionManager:
    """Gestiona conexiones WebSocket activas"""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket conectado - Session: {session_id}")
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket desconectado - Session: {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_json(message)
    
    async def send_text(self, session_id: str, text: str):
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_text(text)


manager = ConnectionManager()


async def authenticate_websocket(websocket: WebSocket) -> Optional[dict]:
    """
    Autentica WebSocket usando JWT del query parameter o header.
    Retorna user_data si es válido, None si no.
    """
    try:
        # Intentar obtener token de query params
        token = websocket.query_params.get("token")
        
        if not token:
            # Intentar obtener de headers
            auth_header = websocket.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None
        
        # Verificar token
        user_data = verify_token(token)
        if not user_data:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None
        
        return user_data
    
    except Exception as e:
        logger.error(f"Error en autenticación WebSocket: {type(e).__name__}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return None


async def stream_llm_response(
    websocket: WebSocket,
    question: str,
    context: str,
    session_id: str
) -> Optional[str]:
    """
    Genera respuesta del LLM con streaming token por token.
    Retorna el texto completo al final.
    """
    try:
        logger.info(f"Iniciando streaming LLM - Session: {session_id}")
        
        # Construir mensajes para OpenAI
        system_prompt = """Eres un asistente médico inteligente especializado en analizar historias clínicas.

Tu función es responder preguntas sobre pacientes basándote ÚNICAMENTE en la información proporcionada en el contexto clínico.

REGLAS DE FORMATO IMPORTANTES:
1. Usa formato Markdown para estructurar tu respuesta
2. Usa negritas (**texto**) para fechas, nombres de diagnósticos y medicamentos importantes
3. Enumera items cuando hay múltiples elementos (1., 2., 3.)
4. Usa viñetas (-) para sub-items y detalles
5. Incluye códigos ICD-10 cuando menciones diagnósticos
6. Especifica dosis y frecuencia cuando menciones medicamentos
7. Organiza la información cronológicamente (más reciente primero)

REGLAS DE CONTENIDO:
1. Responde SOLO con información que esté explícitamente en el contexto
2. Si no hay información suficiente, indícalo claramente
3. Usa un lenguaje claro, profesional y preciso
4. Menciona fechas en formato DD/MM/YYYY cuando sean relevantes
5. NO inventes información
6. Sé conciso pero completo"""

        user_message = f"""CONTEXTO CLÍNICO:
{context}

PREGUNTA DEL USUARIO:
{question}

Por favor, responde basándote únicamente en la información del contexto clínico proporcionado."""

        # Llamada a OpenAI con streaming
        stream = await llm_service.client.chat.completions.create(
            model=llm_service.model,
            max_completion_tokens=2000,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            stream=True  # Habilitar streaming
        )
        
        full_response = ""
        
        # Enviar tipo de mensaje: inicio del stream
        await websocket.send_json({
            "type": "stream_start",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
        # Procesar stream token por token
        async for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                
                if hasattr(delta, 'content') and delta.content:
                    token = delta.content
                    full_response += token
                    
                    # Enviar token individual
                    await websocket.send_json({
                        "type": "token",
                        "token": token,
                        "session_id": session_id
                    })
        
        # Enviar fin del stream
        await websocket.send_json({
            "type": "stream_end",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
        logger.info(f"Streaming completado - Session: {session_id}")
        return full_response
    
    except asyncio.TimeoutError:
        logger.error(f"Timeout en streaming LLM - Session: {session_id}")
        await websocket.send_json({
            "type": "error",
            "error": {
                "code": "LLM_TIMEOUT",
                "message": "El modelo tardó demasiado en responder"
            }
        })
        return None
    
    except Exception as e:
        logger.error(f"Error en streaming LLM: {type(e).__name__}")
        await websocket.send_json({
            "type": "error",
            "error": {
                "code": "LLM_ERROR",
                "message": "Error generando respuesta"
            }
        })
        return None


@router.websocket("/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint para chat con streaming token por token.
    
    Autenticación: Enviar JWT en query param ?token=... o header Authorization: Bearer ...
    
    Formato de mensajes recibidos:
    {
        "type": "query",
        "session_id": "uuid",
        "document_type_id": 1,
        "document_number": "123456",
        "question": "¿Cuáles son las últimas citas?"
    }
    
    Formato de mensajes enviados:
    - stream_start: Indica inicio del streaming
    - token: Cada token individual del LLM
    - stream_end: Indica fin del streaming
    - complete: Respuesta completa con metadata
    - error: Errores durante el proceso
    """
    
    session_id = None
    
    try:
        # 1. Autenticar WebSocket
        user_data = await authenticate_websocket(websocket)
        if not user_data:
            return
        
        # Conectar WebSocket
        temp_session = "temp_" + str(id(websocket))
        await manager.connect(websocket, temp_session)
        
        # Enviar mensaje de bienvenida
        await websocket.send_json({
            "type": "connected",
            "user_id": user_data.get("user_id"),
            "message": "Conectado exitosamente"
        })
        
        # 2. Loop principal: escuchar mensajes
        while True:
            # Recibir mensaje del cliente
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            
            if message_type == "query":
                session_id = message.get("session_id", temp_session)
                document_type_id = message.get("document_type_id")
                document_number = message.get("document_number")
                question = message.get("question")
                
                if not all([document_type_id, document_number, question]):
                    await websocket.send_json({
                        "type": "error",
                        "error": {
                            "code": "INVALID_REQUEST",
                            "message": "Faltan campos requeridos"
                        }
                    })
                    continue
                
                # Actualizar session_id en el manager
                if temp_session in manager.active_connections:
                    manager.active_connections[session_id] = manager.active_connections.pop(temp_session)
                    temp_session = session_id
                
                # 3. Buscar paciente
                await websocket.send_json({
                    "type": "status",
                    "status": "searching_patient",
                    "message": "Buscando datos del paciente..."
                })
                
                try:
                    patient_info, clinical_data = fetch_patient_and_records(
                        db=db,
                        document_type_id=document_type_id,
                        document_number=document_number
                    )
                except Exception as e:
                    logger.error(f"Error buscando paciente: {type(e).__name__}")
                    await websocket.send_json({
                        "type": "error",
                        "error": {
                            "code": "DATABASE_ERROR",
                            "message": "Error al buscar datos del paciente"
                        }
                    })
                    continue
                
                if not patient_info:
                    doc_type = get_document_type_name(document_type_id)
                    await websocket.send_json({
                        "type": "error",
                        "error": {
                            "code": "PATIENT_NOT_FOUND",
                            "message": f"No se encontró paciente con documento {doc_type} {document_number}"
                        }
                    })
                    continue
                
                # 4. Vector search
                await websocket.send_json({
                    "type": "status",
                    "status": "vector_search",
                    "message": "Buscando información relevante..."
                })
                
                similar_chunks = []
                try:
                    similar_chunks = await asyncio.wait_for(
                        search_similar_chunks(
                            patient_id=patient_info.patient_id,
                            question=question,
                            k=15,
                            min_score=0.3
                        ),
                        timeout=VECTOR_SEARCH_TIMEOUT
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"Vector search timeout - Session: {session_id}")
                except Exception as e:
                    logger.warning(f"Vector search falló: {type(e).__name__}")
                
                # 5. Construir contexto
                await websocket.send_json({
                    "type": "status",
                    "status": "building_context",
                    "message": "Preparando contexto clínico..."
                })
                
                try:
                    context = build_context_from_real_data(
                        patient_info=patient_info,
                        clinical_records=clinical_data.records,
                        similar_chunks=similar_chunks
                    )
                except Exception as e:
                    logger.error(f"Error construyendo contexto: {type(e).__name__}")
                    await websocket.send_json({
                        "type": "error",
                        "error": {
                            "code": "CONTEXT_ERROR",
                            "message": "Error al preparar el contexto"
                        }
                    })
                    continue
                
                # 6. Generar respuesta con streaming
                await websocket.send_json({
                    "type": "status",
                    "status": "generating",
                    "message": "Generando respuesta..."
                })
                
                full_response = await asyncio.wait_for(
                    stream_llm_response(websocket, question, context, session_id),
                    timeout=LLM_TIMEOUT
                )
                
                if not full_response:
                    continue
                
                # 7. Enviar respuesta completa con metadata
                full_name = f"{patient_info.first_name} {patient_info.first_surname}"
                if patient_info.second_surname:
                    full_name += f" {patient_info.second_surname}"
                
                await websocket.send_json({
                    "type": "complete",
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "patient_info": {
                        "patient_id": patient_info.patient_id,
                        "full_name": full_name,
                        "document_type": get_document_type_name(document_type_id),
                        "document_number": document_number
                    },
                    "answer": {
                        "text": full_response,
                        "confidence": 0.85,
                        "model_used": llm_service.model
                    },
                    "metadata": {
                        "total_records_analyzed": (
                            len(clinical_data.records.appointments) +
                            len(clinical_data.records.medical_records) +
                            len(clinical_data.records.prescriptions) +
                            len(clinical_data.records.diagnoses)
                        ),
                        "vector_chunks_used": len(similar_chunks)
                    }
                })
            
            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "error": {
                        "code": "UNKNOWN_MESSAGE_TYPE",
                        "message": f"Tipo de mensaje desconocido: {message_type}"
                    }
                })
    
    except WebSocketDisconnect:
        logger.info(f"Cliente desconectado - Session: {session_id or 'unknown'}")
        if session_id:
            manager.disconnect(session_id)
    
    except Exception as e:
        logger.error(f"Error en WebSocket: {type(e).__name__}")
        try:
            await websocket.send_json({
                "type": "error",
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Error interno del servidor"
                }
            })
        except:
            pass
        finally:
            if session_id:
                manager.disconnect(session_id)