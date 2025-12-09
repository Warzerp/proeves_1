# test_consumo_real.py
import sys
sys.path.append('src')

import asyncio
from openai import AsyncOpenAI
from app.database.db_config import settings

async def test_consumo():
    print("🔍 Test de consumo REAL de API...\n")
    
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    print(f"📌 Modelo: {settings.llm_model}")
    print(f"📌 API Key: {settings.openai_api_key[:20]}...\n")
    
    try:
        # Hacer 3 llamadas cortas
        for i in range(1, 4):
            print(f"Llamada {i}...")
            response = await client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "user", "content": f"Di solo el número {i}"}
                ]
            )
            
            print(f"  ✅ Respuesta: {response.choices[0].message.content}")
            print(f"  🔢 Tokens: {response.usage.total_tokens}")
            print(f"  💰 Costo aprox: ${response.usage.total_tokens * 0.0000015:.6f}")
            print()
        
        print("="*60)
        print("✅ Las llamadas funcionaron. Los créditos SE ESTÁN GASTANDO.")
        print("⏰ El dashboard puede tardar hasta 1 hora en actualizarse.")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_consumo())