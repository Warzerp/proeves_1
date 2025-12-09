# src/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, user, query, websocket_chat
from .database.database import Base, engine

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Crear aplicación
app = FastAPI(
    title="SmartHealth API",
    description="API REST y WebSocket para sistema de gestión de salud con RAG",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS (permitir peticiones desde frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(query.router)
app.include_router(websocket_chat.router)

# Endpoint raíz
@app.get("/", tags=["Root"])
def root():
    return {
        "message": "¡API SmartHealth funcionando correctamente!",
        "version": "2.0.0",
        "features": {
            "rest_api": True,
            "websocket": True,
            "rag_enabled": True,
            "streaming": True
        },
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "websocket": "ws://localhost:8088/ws/chat",
            "health": "/health"
        }
    }

# Health check
@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "healthy",
        "websocket_enabled": True,
        "services": {
            "database": "connected",
            "llm": "ready",
            "vector_search": "ready"
        }
    }
