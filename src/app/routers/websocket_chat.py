# src/app/routers/websocket_chat.py
"""
WebSocket endpoint para chat en tiempo real con streaming de respuestas.
Permite consultas RAG con tokens generados en tiempo real.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from sqlalchemy.orm import Session
from typing import Optional, Dict
import json
import logging
import asyncio
from datetime import datetime
import uuid

from app.services.llm_service import llm_service
from app.services.clinical_service import fetch_patient_and_records
from app.services.vector_search import search_similar_chunks
from app.database.database import get_db
from app.services.auth_utils import verify_token  # ← CORREGIDO: auth_utils en vez de auth

router = APIRouter(prefix="/ws", tags=["WebSocket"])
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACIÓN DE TIMEOUTS
# ============================================================================
VECTOR_SEARCH_TIMEOUT = 10
LLM_TIMEOUT = 45
TOTAL_REQUEST_TIMEOUT = 60

# ============================================================================
# CONNECTION MANAGER
# ============================================================================

class ConnectionManager:
    """Gestiona conexiones WebSocket activas"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Acepta y registra una nueva conexión"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"✅ WebSocket conectado - Session: {session_id}")
    
    def disconnect(self, session_id: str):
        """Elimina una conexión del registro"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"🔌 WebSocket desconectado - Session: {session_id}")
    
    async def send_json(self, session_id: str, message: dict):
        """Envía mensaje JSON a una sesión específica"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error enviando mensaje a {session_id}: {e}")
    
    async def send_text(self, session_id: str, text: str):
        """Envía texto plano a una sesión específica"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_text(text)
            except Exception as e:
                logger.error(f"Error enviando texto a {session_id}: {e}")


manager = ConnectionManager()


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def get_document_type_name(document_type_id: int) -> str:
    """Mapea ID de tipo de documento a nombre"""
    types = {
        1: "CC", 2: "CE", 3: "TI", 4: "PA",
        5: "RC", 6: "MS", 7: "AS", 8: "CD",
    }
    return types.get(document_type_id, "CC")


def build_context_from_real_data(patient_info, clinical_records, similar_chunks) -> str:
    """
    Construye el contexto clínico de manera segura.
    Reutiliza la lógica de query.py pero simplificada.
    """
    from datetime import date, datetime

    # Calcular edad
    age = "No disponible"
    if patient_info.birth_date:
        try:
            birth_date = (
                patient_info.birth_date
                if isinstance(patient_info.birth_date, date)
                else datetime.strptime(patient_info.birth_date, "%Y-%m-%d").date()
            )
            today = date.today()
            age = today.year - birth_date.year - (
                (today.month, today.day) < (birth_date.month, birth_date.day)
            )
        except Exception as e:
            logger.warning(f"Error calculando edad: {e}")

    # Información básica
    first_name = getattr(patient_info, 'first_name', 'Nombre')
    first_surname = getattr(patient_info, 'first_surname', 'Apellido')
    document_number = getattr(patient_info, 'document_number', 'No disponible')
    gender = getattr(patient_info, 'gender', None) or "No registrado"

    context = f"""
### INFORMACIÓN BÁSICA DEL PACIENTE
Nombre: {first_name} {first_surname}
Edad: {age}
Documento: {document_number}
Género: {gender}

"""

    # Citas médicas
    if clinical_records.appointments:
        context += "### CITAS MÉDICAS RECIENTES\n"
        for apt in clinical_records.appointments[:10]:
            apt_date = getattr(apt, 'appointment_date', 'Fecha no disponible')
            apt_status = getattr(apt, 'status', None) or 'No disponible'
            apt_reason = getattr(apt, 'reason', None) or 'No especificado'
            doctor_name = getattr(apt, 'doctor_name', None)
            
            context += f"**Cita {apt_date}**\n"
            context += f"- Estado: {apt_status}\n"
            context += f"- Motivo: {apt_reason}\n"
            if doctor_name:
                context += f"- Doctor: {doctor_name}\n"
            context += "\n"

    # Diagnósticos
    if clinical_records.diagnoses:
        context += "### DIAGNÓSTICOS\n"
        for diag in clinical_records.diagnoses[:15]:
            diag_desc = getattr(diag, 'description', 'Diagnóstico sin descripción')
            icd_code = getattr(diag, 'icd_code', 'Sin código')
            context += f"**{diag_desc}** (ICD-10: {icd_code})\n"

    # Prescripciones
    if clinical_records.prescriptions:
        context += "\n### MEDICAMENTOS\n"
        for presc in clinical_records.prescriptions[:15]:
            medication = getattr(presc, 'medication_name', 'Medicamento sin nombre')
            dosage = getattr(presc, 'dosage', '')
            frequency = getattr(presc, 'frequency', '')
            context += f"- {medication}"
            if dosage or frequency:
                context += f" ({dosage} {frequency})"
            context += "\n"

    # Búsqueda vectorial
    if similar_chunks:
        context += "\n### INFORMACIÓN ADICIONAL RELEVANTE\n"
        for chunk in similar_chunks[:5]:
            chunk_text = getattr(chunk, 'chunk_text', 'Texto no disponible')
            relevance = getattr(chunk, 'relevance_score', 0.0)
            context += f"[Relevancia: {relevance:.2f}] {chunk_text}\n\n"

    return context


async def authenticate_websocket(websocket: WebSocket) -> Optional[Dict]:
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
            logger.warning("WebSocket: No se encontró token")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None
        
        # Verificar token
        user_data = verify_token(token)
        if not user_data:
            logger.warning("WebSocket: Token inválido")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None
        
        logger.info(f"✅ Usuario autenticado: {user_data.get('user_id')}")
        return user_data
    
    except Exception as e:
        logger.error(f"Error en autenticación WebSocket: {type(e).__name__}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass
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
        logger.info(f"🎬 Iniciando streaming LLM - Session: {session_id}")
        
        # System prompt
        system_prompt = """Eres un asistente médico inteligente especializado en analizar historias clínicas.

Tu función es responder preguntas sobre pacientes basándote ÚNICAMENTE en la información proporcionada en el contexto clínico.

REGLAS DE FORMATO:
1. Usa formato Markdown para estructurar tu respuesta
2. Usa negritas (**texto**) para fechas, diagnósticos y medicamentos importantes
3. Enumera items cuando hay múltiples elementos (1., 2., 3.)
4. Usa viñetas (-) para sub-items y detalles
5. Incluye códigos ICD-10 cuando menciones diagnósticos
6. Organiza la información cronológicamente (más reciente primero)

REGLAS DE CONTENIDO:
1. Responde SOLO con información que esté explícitamente en el contexto
2. Si no hay información suficiente, indícalo claramente
3. Usa un lenguaje claro, profesional y preciso
4. NO inventes información
5. Sé conciso pero completo"""

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
            stream=True
        )
        
        full_response = ""
        
        # Enviar inicio del stream
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
        
        logger.info(f"✅ Streaming completado - Session: {session_id}")
        return full_response
    
    except asyncio.TimeoutError:
        logger.error(f"⏱️ Timeout en streaming LLM - Session: {session_id}")
        await websocket.send_json({
            "type": "error",
            "error": {
                "code": "LLM_TIMEOUT",
                "message": "El modelo tardó demasiado en responder"
            }
        })
        return None
    
    except Exception as e:
        logger.error(f"❌ Error en streaming LLM: {type(e).__name__}: {e}")
        await websocket.send_json({
            "type": "error",
            "error": {
                "code": "LLM_ERROR",
                "message": f"Error generando respuesta: {str(e)}"
            }
        })
        return None


# ============================================================================
# ENDPOINT WEBSOCKET PRINCIPAL
# ============================================================================

@router.websocket("/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint para chat con streaming token por token.
    
    **Autenticación:** 
    - Enviar JWT en query param: `?token=...`
    - O en header: `Authorization: Bearer ...`
    
    **Formato de mensajes enviados por el cliente:**
    ```json
    {
        "type": "query",
        "session_id": "uuid",
        "document_type_id": 1,
        "document_number": "123456",
        "question": "¿Cuáles son las últimas citas?"
    }
    ```
    
    **Formato de mensajes recibidos del servidor:**
    - `connected`: Conexión exitosa
    - `status`: Actualización de estado del proceso
    - `stream_start`: Inicio del streaming de tokens
    - `token`: Cada token individual del LLM
    - `stream_end`: Fin del streaming
    - `complete`: Respuesta completa con metadata
    - `error`: Errores durante el proceso
    - `pong`: Respuesta a ping (keep-alive)
    """
    
    session_id = None
    temp_session = f"temp_{uuid.uuid4().hex[:8]}"
    
    try:
        # 1. AUTENTICAR
        user_data = await authenticate_websocket(websocket)
        if not user_data:
            return
        
        # 2. CONECTAR
        await manager.connect(websocket, temp_session)
        
        # 3. ENVIAR MENSAJE DE BIENVENIDA
        await websocket.send_json({
            "type": "connected",
            "user_id": user_data.get("user_id"),
            "message": "✅ Conectado exitosamente al chat médico"
        })
        
        # 4. LOOP PRINCIPAL: ESCUCHAR MENSAJES
        while True:
            # Recibir mensaje del cliente
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=300  # 5 minutos de inactividad máxima
                )
            except asyncio.TimeoutError:
                logger.info(f"⏱️ Timeout de inactividad - Session: {session_id or temp_session}")
                break
            
            message = json.loads(data)
            message_type = message.get("type")
            
            # ============================================================
            # MENSAJE TIPO: QUERY
            # ============================================================
            if message_type == "query":
                session_id = message.get("session_id", temp_session)
                document_type_id = message.get("document_type_id")
                document_number = message.get("document_number")
                question = message.get("question")
                
                # Validar campos requeridos
                if not all([document_type_id, document_number, question]):
                    await websocket.send_json({
                        "type": "error",
                        "error": {
                            "code": "INVALID_REQUEST",
                            "message": "Faltan campos requeridos (document_type_id, document_number, question)"
                        }
                    })
                    continue
                
                # Actualizar session_id en el manager
                if temp_session in manager.active_connections:
                    manager.active_connections[session_id] = manager.active_connections.pop(temp_session)
                    temp_session = session_id
                
                logger.info(f"📩 Query recibida - Session: {session_id}")
                
                try:
                    # PASO 1: Buscar paciente
                    await websocket.send_json({
                        "type": "status",
                        "status": "searching_patient",
                        "message": "🔍 Buscando datos del paciente..."
                    })
                    
                    # Obtener sesión de DB dentro del contexto
                    db: Session = next(get_db())
                    
                    try:
                        patient_info, clinical_data = fetch_patient_and_records(
                            db=db,
                            document_type_id=document_type_id,
                            document_number=document_number
                        )
                    finally:
                        db.close()
                    
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
                    
                    # PASO 2: Vector search
                    await websocket.send_json({
                        "type": "status",
                        "status": "vector_search",
                        "message": "🔎 Buscando información relevante..."
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
                        logger.warning(f"⏱️ Vector search timeout - Session: {session_id}")
                    except Exception as e:
                        logger.warning(f"⚠️ Vector search falló: {type(e).__name__}")
                    
                    # PASO 3: Construir contexto
                    await websocket.send_json({
                        "type": "status",
                        "status": "building_context",
                        "message": "📝 Preparando contexto clínico..."
                    })
                    
                    context = build_context_from_real_data(
                        patient_info=patient_info,
                        clinical_records=clinical_data.records,
                        similar_chunks=similar_chunks
                    )
                    
                    # PASO 4: Generar respuesta con streaming
                    await websocket.send_json({
                        "type": "status",
                        "status": "generating",
                        "message": "🤖 Generando respuesta..."
                    })
                    
                    full_response = await asyncio.wait_for(
                        stream_llm_response(websocket, question, context, session_id),
                        timeout=LLM_TIMEOUT
                    )
                    
                    if not full_response:
                        continue
                    
                    # PASO 5: Enviar respuesta completa con metadata
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
                    
                    logger.info(f"✅ Query completada - Session: {session_id}")
                
                except asyncio.TimeoutError:
                    logger.error(f"⏱️ Timeout total del request - Session: {session_id}")
                    await websocket.send_json({
                        "type": "error",
                        "error": {
                            "code": "REQUEST_TIMEOUT",
                            "message": "La solicitud excedió el tiempo máximo permitido"
                        }
                    })
                
                except Exception as e:
                    logger.error(f"❌ Error procesando query: {type(e).__name__}: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "error": {
                            "code": "PROCESSING_ERROR",
                            "message": f"Error procesando solicitud: {str(e)}"
                        }
                    })
            
            # ============================================================
            # MENSAJE TIPO: PING (KEEP-ALIVE)
            # ============================================================
            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
            
            # ============================================================
            # MENSAJE TIPO: DESCONOCIDO
            # ============================================================
            else:
                await websocket.send_json({
                    "type": "error",
                    "error": {
                        "code": "UNKNOWN_MESSAGE_TYPE",
                        "message": f"Tipo de mensaje desconocido: {message_type}"
                    }
                })
    
    except WebSocketDisconnect:
        logger.info(f"👋 Cliente desconectado voluntariamente - Session: {session_id or temp_session}")
    
    except Exception as e:
        logger.error(f"❌ Error inesperado en WebSocket: {type(e).__name__}: {e}")
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
        # Limpiar conexión
        manager.disconnect(session_id or temp_session)
