"""
Script de prueba para WebSocket de SmartHealth
Ejecutar desde la raíz del proyecto: python test_websocket.py

Requisitos:
pip install websockets
"""

import asyncio
import websockets
import json
from datetime import datetime
import sys

# ===============================
# CONFIGURACIÓN
# ===============================
WS_URL = "ws://localhost:8088/ws/chat"

# ⚠️ IMPORTANTE: Reemplaza este token con uno real obtenido de /auth/login
TOKEN = "colocar_tu_token"

# Datos de prueba
TEST_QUERY = {
    "type": "query",
    "session_id": "test-session-python-123",
    "document_type_id": 8,  # CD
    "document_number": "30995750",
    "question": "¿que medico le ha hecho la consulta?"
}


def print_separator(char="=", length=70):
    """Imprime una línea separadora"""
    print(char * length)


def print_header(text):
    """Imprime un encabezado destacado"""
    print_separator()
    print(f"  {text}")
    print_separator()


async def test_websocket():
    """Prueba completa del WebSocket con streaming"""
    
    print_header("🧪 TEST WEBSOCKET - SmartHealth")
    print(f"📡 URL: {WS_URL}")
    print(f"🔑 Token: {TOKEN[:20]}..." if len(TOKEN) > 20 else "⚠️  Token no configurado")
    print()
    
    if TOKEN == "TU_TOKEN_JWT_AQUI":
        print("❌ ERROR: Debes configurar un TOKEN válido")
        print("   1. Haz login: POST http://localhost:8088/auth/login")
        print("   2. Copia el access_token")
        print("   3. Reemplaza TOKEN en este script")
        return
    
    try:
        # Conectar con token en la URL
        url_with_token = f"{WS_URL}?token={TOKEN}"
        
        print("🔌 Conectando al WebSocket...")
        async with websockets.connect(url_with_token) as websocket:
            print("✅ Conectado exitosamente\n")
            
            # Esperar mensaje de bienvenida
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            print(f"📩 Bienvenida: {welcome_data.get('message')}")
            print(f"👤 User ID: {welcome_data.get('user_id')}\n")
            
            # Enviar query
            print_header("📤 ENVIANDO PREGUNTA")
            print(f"Pregunta: {TEST_QUERY['question']}")
            print(f"Documento: {TEST_QUERY['document_type_id']} - {TEST_QUERY['document_number']}")
            print()
            
            await websocket.send(json.dumps(TEST_QUERY))
            print("✅ Pregunta enviada\n")
            
            # Variables para el streaming
            full_response = ""
            streaming = False
            start_time = datetime.now()
            
            print_header("📡 RECIBIENDO RESPUESTA EN TIEMPO REAL")
            
            # Recibir respuestas
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=60)
                    data = json.loads(message)
                    
                    msg_type = data.get("type")
                    
                    # STATUS: Actualizaciones de progreso
                    if msg_type == "status":
                        print(f"⏳ {data.get('message')}")
                    
                    # STREAM_START: Inicio del streaming
                    elif msg_type == "stream_start":
                        print("\n🎬 Inicio del streaming de tokens")
                        print("-" * 70)
                        streaming = True
                    
                    # TOKEN: Cada token individual
                    elif msg_type == "token":
                        token = data.get("token", "")
                        print(token, end="", flush=True)
                        full_response += token
                    
                    # STREAM_END: Fin del streaming
                    elif msg_type == "stream_end":
                        streaming = False
                        print("\n" + "-" * 70)
                        print("🏁 Fin del streaming\n")
                    
                    # COMPLETE: Respuesta completa con metadata
                    elif msg_type == "complete":
                        elapsed = (datetime.now() - start_time).total_seconds()
                        
                        print_header("✅ RESPUESTA COMPLETA RECIBIDA")
                        print(f"📊 Paciente: {data['patient_info']['full_name']}")
                        print(f"📄 Documento: {data['patient_info']['document_type']} {data['patient_info']['document_number']}")
                        print(f"⏱️  Tiempo total: {elapsed:.2f}s")
                        print(f"📚 Registros analizados: {data['metadata']['total_records_analyzed']}")
                        print(f"🔍 Chunks vectoriales: {data['metadata']['vector_chunks_used']}")
                        print(f"🤖 Modelo: {data['answer']['model_used']}")
                        print(f"📊 Confianza: {data['answer']['confidence']:.2%}")
                        print()
                        print_header("📝 RESPUESTA FINAL")
                        print(data['answer']['text'])
                        print_separator()
                        break
                    
                    # ERROR: Manejo de errores
                    elif msg_type == "error":
                        print(f"\n❌ ERROR RECIBIDO:")
                        print(f"   Código: {data['error'].get('code')}")
                        print(f"   Mensaje: {data['error'].get('message')}")
                        break
                    
                    # PONG: Respuesta a ping
                    elif msg_type == "pong":
                        print("🏓 Pong recibido (keep-alive)")
                
                except asyncio.TimeoutError:
                    print("\n⏱️  Timeout esperando respuesta del servidor")
                    break
                except json.JSONDecodeError as e:
                    print(f"\n❌ Error decodificando JSON: {e}")
                    break
                except Exception as e:
                    print(f"\n❌ Error procesando mensaje: {type(e).__name__}: {e}")
                    break
            
            print("\n🔌 Cerrando conexión...")
            await websocket.close()
            print("✅ Test completado exitosamente\n")
    
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Error de autenticación HTTP {e.status_code}")
        print("   Posibles causas:")
        print("   - Token inválido o expirado")
        print("   - Token mal formateado")
        print("   - Usuario no autorizado")
        print("\n   Solución:")
        print("   1. Obtén un nuevo token: POST /auth/login")
        print("   2. Verifica que el token sea válido")
    
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ Error de WebSocket: {e}")
    
    except Exception as e:
        print(f"❌ Error inesperado: {type(e).__name__}: {e}")


async def test_ping_pong():
    """Prueba simple de ping/pong para verificar keep-alive"""
    
    print_header("🏓 TEST PING/PONG")
    
    if TOKEN == "TU_TOKEN_JWT_AQUI":
        print("❌ Configura un TOKEN válido primero")
        return
    
    try:
        url_with_token = f"{WS_URL}?token={TOKEN}"
        
        async with websockets.connect(url_with_token) as websocket:
            print("✅ Conectado")
            
            # Esperar bienvenida
            await websocket.recv()
            
            # Enviar ping
            await websocket.send(json.dumps({"type": "ping"}))
            print("📤 Ping enviado")
            
            # Esperar pong
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(response)
            
            if data.get("type") == "pong":
                print("✅ Pong recibido - Conexión funcional")
            else:
                print(f"⚠️  Respuesta inesperada: {data}")
            
            await websocket.close()
    
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")


async def test_invalid_token():
    """Prueba con token inválido para verificar autenticación"""
    
    print_header("🔒 TEST AUTENTICACIÓN (TOKEN INVÁLIDO)")
    
    try:
        invalid_url = f"{WS_URL}?token=token_invalido_123"
        
        print("🔌 Intentando conectar con token inválido...")
        async with websockets.connect(invalid_url) as websocket:
            print("❌ ERROR: Conexión aceptada con token inválido!")
    
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"✅ Autenticación funcionando correctamente")
        print(f"   Rechazado con código: {e.status_code}")
    
    except Exception as e:
        print(f"⚠️  Comportamiento inesperado: {type(e).__name__}")


def print_menu():
    """Muestra el menú de opciones"""
    print("\n" + "="*70)
    print("  MENÚ DE TESTS")
    print("="*70)
    print("1. Test completo (Query con streaming)")
    print("2. Test Ping/Pong (keep-alive)")
    print("3. Test autenticación (token inválido)")
    print("4. Ejecutar todos los tests")
    print("0. Salir")
    print("="*70)


async def main():
    """Función principal con menú interactivo"""
    
    print("\n" + "🏥 " * 15)
    print("  SMARTHEALTH - WEBSOCKET TEST SUITE")
    print("🏥 " * 15)
    
    while True:
        print_menu()
        choice = input("\n👉 Selecciona una opción: ").strip()
        
        if choice == "1":
            await test_websocket()
        elif choice == "2":
            await test_ping_pong()
        elif choice == "3":
            await test_invalid_token()
        elif choice == "4":
            await test_websocket()
            await test_ping_pong()
            await test_invalid_token()
        elif choice == "0":
            print("\n👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción inválida")
        
        input("\n⏸️  Presiona Enter para continuar...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrumpido por el usuario")
        sys.exit(0)
