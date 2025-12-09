@echo off
chcp 65001 >nul
cls
echo ╔════════════════════════════════════════════╗
echo ║   🏥 SmartHealth WebSocket Setup          ║
echo ║   Configuración Automática                ║
echo ╚════════════════════════════════════════════╝
echo.

echo [1/6] Limpiando caché de Python...
cd src
for /d /r . %%d in (__pycache__) do @if exist "%%d" (
    rd /s /q "%%d" 2>nul
)
cd ..
echo ✅ Caché limpiado
echo.

echo [2/6] Verificando estructura de directorios...
if not exist "src\app\services" (
    echo ❌ ERROR: Directorio src\app\services no existe
    pause
    exit /b 1
)
echo ✅ Directorios OK
echo.

echo [3/6] Verificando archivos críticos...
set "ERRORS=0"

if not exist "src\app\services\auth_service.py" (
    echo ❌ Falta: auth_service.py
    set /a ERRORS+=1
)

if not exist "src\app\services\auth_utils.py" (
    echo ⚠️  Falta: auth_utils.py - DEBES CREARLO
    set /a ERRORS+=1
)

if not exist "src\app\routers\websocket_chat.py" (
    echo ❌ Falta: websocket_chat.py
    set /a ERRORS+=1
)

if %ERRORS% GTR 0 (
    echo.
    echo ❌ Faltan %ERRORS% archivos críticos
    echo    Por favor créalos según las instrucciones
    pause
    exit /b 1
)
echo ✅ Todos los archivos existen
echo.

echo [4/6] Verificando dependencias...
pip show websockets >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Instalando websockets...
    pip install websockets
)
echo ✅ Dependencias OK
echo.

echo [5/6] Verificando variables de entorno...
if not exist ".env" (
    echo ❌ ERROR: Archivo .env no existe
    echo    Crea el archivo .env con:
    echo    - OPENAI_API_KEY
    echo    - DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
    echo    - SECRET_KEY
    pause
    exit /b 1
)
echo ✅ .env existe
echo.

echo [6/6] Iniciando servidor...
echo.
echo ╔════════════════════════════════════════════╗
echo ║  Servidor iniciando en:                   ║
echo ║  http://127.0.0.1:8088                    ║
echo ║                                            ║
echo ║  WebSocket:                                ║
echo ║  ws://127.0.0.1:8088/ws/chat              ║
echo ║                                            ║
echo ║  Presiona CTRL+C para detener             ║
echo ╚════════════════════════════════════════════╝
echo.
timeout /t 2 >nul

cd src
uvicorn app.main:app --reload --port 8088
