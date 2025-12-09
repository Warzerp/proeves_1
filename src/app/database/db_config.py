import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Encontrar la raíz del proyecto (donde está el .env)
# Desde db_config.py -> database -> app -> src -> raíz
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    # === CONFIGURACIÓN DE BASE DE DATOS ===
    db_host: str
    db_port: int = 5432
    db_name: str
    db_user: str
    db_password: str
    
    # === CONFIGURACIÓN DE SEGURIDAD ===
    secret_key: str
    app_env: str = "production"
    
    # === CONFIGURACIÓN DEL LLM ===
    openai_api_key: str
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 500
    llm_timeout: int = 30
    
    model_config = SettingsConfigDict(
        # Usar la ruta absoluta al .env
        env_file=str(ENV_PATH) if ENV_PATH.exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @property
    def database_url(self) -> str:
        """Construye la URL de conexión a PostgreSQL"""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

# Mostrar advertencia si no encuentra el .env
if not ENV_PATH.exists():
    print(f"⚠️  Archivo .env no encontrado en: {ENV_PATH}")
    print(f"   Crea el archivo .env en la raíz del proyecto")

settings = Settings()

