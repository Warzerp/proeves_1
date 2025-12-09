# src/app/services/llm_client.py
from openai import AsyncOpenAI
from typing import Dict, List
import logging
from app.database.db_config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    """Cliente para interactuar con OpenAI GPT"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.llm_timeout
        )
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
    
    async def generate(self, prompt: str, system_prompt: str) -> Dict:
        """
        Genera respuesta del LLM.
        """
        try:
            # Preparar parámetros base
            params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
            }
            
            # gpt-5-nano solo acepta temperature=1 (default)
            # Para otros modelos, usar el configurado
            if not self.model.startswith("gpt-5"):
                params["temperature"] = self.temperature
            
            # Usar el parámetro correcto según el modelo
            if self.model.startswith(("gpt-5", "gpt-4.1", "gpt-4o")):
                params["max_completion_tokens"] = self.max_tokens
            else:
                params["max_tokens"] = self.max_tokens
            
            response = await self.client.chat.completions.create(**params)
            
            result = {
                "text": response.choices[0].message.content,
                "model_used": response.model,
                "tokens_used": response.usage.total_tokens
            }
            
            logger.info(f"✅ LLM generó respuesta. Tokens usados: {result['tokens_used']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en LLM: {str(e)}")
            from app.schemas.llm_schemas import LLMError
            raise LLMError(
                message="Error al generar respuesta del LLM",
                details={"error": str(e), "model": self.model}
            )

# Instancia global del cliente
llm_client = LLMClient()


# ============================================================================
# FUNCIÓN PARA VECTOR SEARCH (Persona 3)
# ============================================================================

async def get_embedding(text: str) -> List[float]:
    """
    Genera embedding de un texto usando OpenAI.
    Usado por vector_search.py para convertir la pregunta en vector.
    
    Args:
        text: Texto a convertir en embedding
        
    Returns:
        Lista de floats representando el vector embedding
    """
    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        response = await client.embeddings.create(
            model="text-embedding-3-small",  # Modelo de embeddings de OpenAI
            input=text
        )
        
        embedding = response.data[0].embedding
        logger.info(f"🔢 Embedding generado: {len(embedding)} dimensiones")
        
        return embedding
        
    except Exception as e:
        logger.error(f"❌ Error generando embedding: {str(e)}")
        raise Exception(f"Error al generar embedding: {str(e)}")