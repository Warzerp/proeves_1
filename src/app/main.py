# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, user
from .database.database import Base, engine
from .routers import query

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Crear aplicación
app = FastAPI(
    title="SmartHealth API - Sprint 1",
    description="API REST para sistema de gestión de salud",
    version="1.0.0"
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

# Endpoint raíz
@app.get("/", tags=["Root"])
def root():
    return {
        "message": "¡API SmartHealth funcionando correctamente!",
        "docs": "/docs"
    }

# Health check
@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}

@app.get("/")
def root():
    return {"message": "Smart Health RAG API - Running ✅"}