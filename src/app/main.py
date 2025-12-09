# src/app/main.py

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import time
from typing import Dict
import os

from .routers import auth, user, query, websocket_chat
from .database.database import Base, engine
from .database.db_config import settings

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear tablas en la base de datos
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Tablas de base de datos creadas exitosamente")
except Exception as e:
    logger.error(f"Error creando tablas: {str(e)}")
    raise

# Crear aplicación
app = FastAPI(
    title="SmartHealth API",
    description="API REST y WebSocket para sistema de gestión de salud con RAG",
    version="2.0.0",
    docs_url="/docs" if settings.app_env == "development" else None,
    redoc_url="/redoc" if settings.app_env == "development" else None,
    openapi_url="/openapi.json" if settings.app_env == "development" else None
)

# ============================================================
# MIDDLEWARES DE SEGURIDAD
# ============================================================

# 1. CORS - Configuración restrictiva
if settings.app_env == "production":
    # En producción, especificar dominios exactos
    allowed_origins = os.getenv("CORS_ORIGINS", "").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
        max_age=3600
    )
else:
    # En desarrollo, permitir todos los orígenes
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 2. Trusted Host Middleware (protección contra host header poisoning)
if settings.app_env == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=os.getenv("ALLOWED_HOSTS", "localhost").split(",")
    )

# 3. Rate Limiting Middleware (simple)
class RateLimitMiddleware:
    def __init__(self, app, max_requests: int = 100, window: int = 60):
        self.app = app
        self.max_requests = max_requests
        self.window = window
        self.requests: Dict[str, list] = {}
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Obtener IP del cliente
        client_ip = scope.get("client")[0] if scope.get("client") else "unknown"
        
        # Limpiar requests antiguas
        current_time = time.time()
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if current_time - req_time < self.window
            ]
        else:
            self.requests[client_ip] = []
        
        # Verificar límite
        if len(self.requests[client_ip]) >= self.max_requests:
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests"}
            )
            await response(scope, receive, send)
            return
        
        # Agregar request actual
        self.requests[client_ip].append(current_time)
        
        await self.app(scope, receive, send)

# Solo en producción
if settings.app_env == "production":
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=int(os.getenv("GLOBAL_RATE_LIMIT", "100")),
        window=60
    )

# 4. Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Headers de seguridad
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    return response

# 5. Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        f"Response: {response.status_code} "
        f"Time: {process_time:.3f}s "
        f"Path: {request.url.path}"
    )
    
    return response

# ============================================================
# EXCEPTION HANDLERS
# ============================================================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Maneja excepciones HTTP de forma segura"""
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail
            }
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Maneja errores de validación de Pydantic"""
    logger.warning(f"Validation Error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Error de validación en los datos enviados",
                "details": exc.errors()
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Maneja excepciones generales sin exponer detalles internos"""
    logger.error(f"Unhandled Exception: {type(exc).__name__}: {str(exc)}", exc_info=True)
    
    # En desarrollo, mostrar más detalles
    if settings.app_env == "development":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": str(exc),
                    "type": type(exc).__name__
                }
            }
        )
    
    # En producción, mensaje genérico
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Error interno del servidor"
            }
        }
    )

# ============================================================
# ROUTERS
# ============================================================

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(query.router)
app.include_router(websocket_chat.router)

# ============================================================
# ENDPOINTS PRINCIPALES
# ============================================================

@app.get("/", tags=["Root"])
def root():
    """Endpoint raíz con información de la API"""
    return {
        "message": "API SmartHealth funcionando correctamente",
        "version": "2.0.0",
        "environment": settings.app_env,
        "features": {
            "rest_api": True,
            "websocket": True,
            "rag_enabled": True,
            "streaming": True,
            "authentication": True,
            "rate_limiting": settings.app_env == "production"
        },
        "endpoints": {
            "docs": "/docs" if settings.app_env == "development" else None,
            "redoc": "/redoc" if settings.app_env == "development" else None,
            "websocket": "ws://localhost:8088/ws/chat",
            "health": "/health"
        }
    }

@app.get("/health", tags=["Health"])
def health():
    """Health check endpoint"""
    try:
        # Verificar conexión a base de datos
        from .database.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "disconnected"
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "timestamp": time.time(),
        "environment": settings.app_env,
        "services": {
            "database": db_status,
            "llm": "ready",
            "vector_search": "ready",
            "websocket": "enabled"
        }
    }

@app.get("/version", tags=["Info"])
def version():
    """Información de versión"""
    return {
        "version": "2.0.0",
        "python_version": os.sys.version,
        "environment": settings.app_env
    }

# ============================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Eventos al iniciar la aplicación"""
    logger.info("=" * 60)
    logger.info("SmartHealth API iniciando")
    logger.info(f"Entorno: {settings.app_env}")
    logger.info(f"Modelo LLM: {settings.llm_model}")
    logger.info(f"Base de datos: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    logger.info("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    """Eventos al cerrar la aplicación"""
    logger.info("SmartHealth API cerrando")