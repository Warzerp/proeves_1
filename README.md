# BACKEND-FAPI-BDI-SMART_HEALTH
# 🏥 SmartHealth - Clinical Query System with RAG

**Desarrolladores**: Ivan Ospino, Gisell Anaya, Jhoan Smith, Jeison Mendez,Jhon Mantilla
**Creado**: 22-Noviembre-2025  
**Última actualización**: Diciembre-2025

## Descripción 🗓️  
Este proyecto es un backend desarrollado en **FastAPI** para la consulta inteligente de información clínica de pacientes utilizando el patrón **RAG (Retrieval-Augmented Generation)**. Utiliza **PostgreSQL con pgvector** como base de datos vectorial y está diseñado con una arquitectura modular que facilita la escalabilidad y el mantenimiento.

### ✨ Características principales

- 🔐 **Autenticación JWT** con registro y login seguros
- 💬 **Chat en tiempo real vía WebSocket** con streaming de respuestas
- 🧠 **RAG con búsqueda vectorial** usando pgvector y OpenAI embeddings
- 📊 **Consultas inteligentes** sobre historias clínicas completas
- 🔍 **Búsqueda semántica** en citas, diagnósticos, prescripciones y registros médicos
- 📡 **API REST + WebSocket** para máxima flexibilidad

Las contribuciones y los comentarios siempre son bienvenidos. ¡Explora y descubre la magia en el directorio `/src`! ⚡

---

## Estructura del Proyecto

**Contenido raíz**:
- `README.md`: Documentación general del proyecto
- `requirements.txt`: Dependencias de Python
- `.env`: Variables de entorno (no incluido en Git)
- `.gitignore`: Archivos ignorados por Git

---

### 📁 [src/app/](./src/app/)
**Propósito**: Contiene el código fuente principal del proyecto.

#### 🗄️ [database/](./src/app/database/)
Configuración de la base de datos.
- `database.py`: Conexión a PostgreSQL con pgvector
- `db_config.py`: Gestión de configuración mediante variables de entorno

#### 📊 [models/](./src/app/models/)
Definición de modelos SQLAlchemy (ORM).
- `user.py`: Usuarios del sistema
- `patient.py`: Pacientes
- `appointment.py`: Citas médicas
- `diagnosis.py`: Diagnósticos
- `prescription.py`: Prescripciones médicas
- `medical_record.py`: Registros médicos
- `record_diagnosis.py`: Relación entre registros y diagnósticos
- `audit_logs.py`: Logs de auditoría de consultas

#### 🛣️ [routers/](./src/app/routers/)
Endpoints de las APIs (REST y WebSocket).
- `auth.py`: Registro y login con JWT
- `user.py`: Gestión de usuarios (CRUD)
- `query.py`: Consultas RAG con búsqueda vectorial
- `websocket_chat.py`: **Chat en tiempo real con streaming** 🆕

#### 📋 [schemas/](./src/app/schemas/)
Esquemas Pydantic para validación.
- `user.py`: Validación de usuarios
- `clinical.py`: DTOs para datos clínicos (pacientes, citas, diagnósticos)
- `rag.py`: Esquemas para chunks similares y resultados de búsqueda
- `llm_schemas.py`: Request/Response del LLM
- `audit_logs.py`: Logs de auditoría

#### ⚙️ [services/](./src/app/services/)
Lógica de negocio.
- `auth_service.py`: Autenticación y registro
- `auth_utils.py`: Utilidades de verificación de tokens
- `user.py`: Operaciones CRUD de usuarios
- `clinical_service.py`: Gestión de información clínica
- `llm_client.py`: Cliente para OpenAI API
- `llm_service.py`: Generación de respuestas inteligentes
- `vector_search.py`: Búsqueda vectorial con pgvector
- `rag_context.py`: Construcción de contexto para RAG
- `generate_embeddings.py`: Generación de embeddings para la BD

#### 🔒 [core/](./src/app/core/)
Funcionalidades core.
- `security.py`: JWT, hashing de contraseñas, middleware de autenticación

#### 📄 Archivo Principal
- `main.py`: Punto de entrada de FastAPI

---

## 🚀 Requisitos

- **Python 3.9+**
- **PostgreSQL 16** con extensión **pgvector**
- **Cuenta de OpenAI** (para embeddings y GPT)
- **Git**

---

## 📦 Instalación

### 1. Clonar el Repositorio

```bash
git clone git@github.com:Ospino89/-backend-fapi-bdi-smart_health.git
cd -backend-fapi-bdi-smart_health
```

### 2. Crear un Entorno Virtual

```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Instalar las Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar las Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
# === BASE DE DATOS ===
DB_HOST=localhost
DB_PORT=5432
DB_NAME=smarthealth
DB_USER=postgres
DB_PASSWORD=tu_password

# === SEGURIDAD ===
SECRET_KEY=tu_clave_secreta_muy_segura_de_al_menos_32_caracteres
APP_ENV=development

# === OPENAI ===
OPENAI_API_KEY=sk-tu-api-key-de-openai

# === CONFIGURACIÓN LLM ===
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=500
LLM_TIMEOUT=30
```

### 5. Inicializar la Base de Datos

Asegúrate de que PostgreSQL esté corriendo y ejecuta los scripts DDL en `content/smart-health/scripts/ddl/`.

```bash
# Conéctate a PostgreSQL
psql -U postgres

# Crea la base de datos y ejecuta los scripts
\i content/smart-health/scripts/ddl/01-create-database.sql
\i content/smart-health/scripts/ddl/02-create-tables.sql
\i content/smart-health/scripts/ddl/03-insert-sample-data.sql
\i content/smart-health/scripts/ddl/04-create-embeddings.sql
```

### 6. Generar Embeddings (Opcional)

Si quieres poblar la base de datos con embeddings reales:

```bash
cd src
python -m app.services.generate_embeddings
```

### 7. Ejecutar el Servidor

**Desarrollo** (con auto-reload):
```bash
cd src
uvicorn app.main:app --reload --port 8088
```

**Producción**:
```bash
cd src
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8088
```

### 8. Acceder a la API

- **API Base**: http://localhost:8088
- **Documentación Swagger**: http://localhost:8088/docs
- **Documentación ReDoc**: http://localhost:8088/redoc
- **Health Check**: http://localhost:8088/health

---

## 🔌 WebSocket - Chat en Tiempo Real

### Características del WebSocket

- ✅ **Autenticación JWT** obligatoria
- ✅ **Streaming token por token** de las respuestas
- ✅ **Búsqueda vectorial** en tiempo real
- ✅ **Validación de pacientes** antes de consultar
- ✅ **Manejo de errores** robusto
- ✅ **Keep-alive** con ping/pong

### Endpoint WebSocket

```
ws://localhost:8088/ws/chat?token=<JWT_TOKEN>
```

### Flujo de Uso

1. **Obtener token JWT**:
   ```bash
   curl -X POST "http://localhost:8088/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"email": "usuario@ejemplo.com", "password": "password123"}'
   ```

2. **Conectar al WebSocket**:
   ```javascript
   const ws = new WebSocket('ws://localhost:8088/ws/chat?token=YOUR_JWT_TOKEN');
   ```

3. **Enviar una consulta**:
   ```javascript
   ws.send(JSON.stringify({
     type: "query",
     session_id: "session-123",
     document_type_id: 1,  // 1=CC, 2=CE, 3=TI, 4=PA, 8=CD
     document_number: "1234567890",
     question: "¿Qué medicamentos tiene prescritos el paciente?"
   }));
   ```

4. **Recibir respuesta en streaming**:
   ```javascript
   ws.onmessage = (event) => {
     const data = JSON.parse(event.data);
     
     switch(data.type) {
       case 'connected':
         console.log('✅ Conectado');
         break;
       case 'status':
         console.log('⏳', data.message);
         break;
       case 'stream_start':
         console.log('🎬 Iniciando respuesta...');
         break;
       case 'token':
         process.stdout.write(data.token); // Streaming token por token
         break;
       case 'complete':
         console.log('\n✅ Respuesta completa:', data);
         break;
       case 'error':
         console.error('❌ Error:', data.error);
         break;
     }
   };
   ```

### Cliente HTML de Prueba

Incluimos un cliente HTML completo para probar el WebSocket:

```bash
# Abre el archivo en tu navegador
open smart_health_chat.html
```

---

## 🧪 Testing

### 1. Test WebSocket con Python

```bash
# Configura tu token en test_websocket.py
python test_websocket.py
```

### 2. Test de consumo de OpenAI

```bash
python test_llm_real.py
```

### 3. Setup automático (Windows)

```bash
setup_websocket.bat
```

---

## 📡 API Endpoints

### Autenticación

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/auth/register` | Registrar nuevo usuario | No |
| POST | `/auth/login` | Iniciar sesión (obtener JWT) | No |

### Usuarios

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/users/me` | Obtener perfil del usuario actual | Sí |
| GET | `/users/` | Listar todos los usuarios | Sí |
| GET | `/users/{id}` | Obtener usuario por ID | Sí |
| PUT | `/users/{id}` | Actualizar usuario | Sí |
| DELETE | `/users/{id}` | Desactivar usuario | Sí |

### Consultas RAG

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/query/` | Realizar consulta inteligente | No |

### WebSocket

| Protocolo | Endpoint | Descripción | Auth |
|-----------|----------|-------------|------|
| WS | `/ws/chat?token=<JWT>` | Chat en tiempo real | Sí |

### Salud del Sistema

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/` | Información general de la API | No |
| GET | `/health` | Estado de los servicios | No |

---

## 🔐 Autenticación

Todos los endpoints protegidos requieren un token JWT en el header:

```bash
Authorization: Bearer <tu_token_jwt>
```

Obtén el token mediante el endpoint `/auth/login`.

---

## 🗂️ Tipos de Documento Soportados

| ID | Tipo | Descripción |
|----|------|-------------|
| 1 | CC | Cédula de Ciudadanía |
| 2 | CE | Cédula de Extranjería |
| 3 | TI | Tarjeta de Identidad |
| 4 | PA | Pasaporte |
| 5 | RC | Registro Civil |
| 6 | MS | Menor sin Identificación |
| 7 | AS | Adulto sin Identificación |
| 8 | CD | Carné Diplomático |

---

## 🧠 Cómo Funciona el RAG

1. **Recepción de consulta**: Usuario pregunta sobre un paciente
2. **Búsqueda del paciente**: Se obtienen todos los datos clínicos
3. **Búsqueda vectorial**: Se buscan fragmentos similares usando embeddings
4. **Construcción del contexto**: Se combina información directa + vectorial
5. **Generación con LLM**: GPT-4o-mini genera respuesta basada en el contexto
6. **Streaming de respuesta**: Tokens enviados en tiempo real (WebSocket)

---

## 📊 Formato de Respuesta

### Query REST (POST /query/)

```json
{
  "status": "success",
  "session_id": "session-123",
  "sequence_chat_id": 1,
  "timestamp": "2025-12-09T10:30:00Z",
  "patient_info": {
    "patient_id": 42,
    "full_name": "Juan Pérez González",
    "document_type": "CC",
    "document_number": "1234567890"
  },
  "answer": {
    "text": "El paciente tiene prescritos los siguientes medicamentos...",
    "confidence": 0.92,
    "model_used": "gpt-4o-mini"
  },
  "sources": [
    {
      "source_id": 1,
      "type": "prescription",
      "medication": "Ibuprofeno 400mg",
      "relevance_score": 0.95
    }
  ],
  "metadata": {
    "total_records_analyzed": 45,
    "query_time_ms": 1250,
    "sources_used": 8,
    "context_tokens": 2340
  }
}
```

### WebSocket - Mensajes

**Mensaje de consulta**:
```json
{
  "type": "query",
  "session_id": "session-123",
  "document_type_id": 1,
  "document_number": "1234567890",
  "question": "¿Cuál es el diagnóstico más reciente?"
}
```

**Mensaje de estado**:
```json
{
  "type": "status",
  "message": "Buscando información del paciente..."
}
```

**Token de respuesta**:
```json
{
  "type": "token",
  "token": "El "
}
```

**Respuesta completa**:
```json
{
  "type": "complete",
  "patient_info": { ... },
  "answer": { ... },
  "sources": [ ... ],
  "metadata": { ... }
}
```

---

## 🛠️ Troubleshooting

### Error: "Token inválido"
- Verifica que el token JWT no haya expirado (30 min por defecto)
- Asegúrate de incluir el prefijo `Bearer` en REST
- En WebSocket, pasa el token en la URL

### Error: "Paciente no encontrado"
- Verifica el `document_type_id` y `document_number`
- Asegúrate de que el paciente exista en la BD

### Error: "OpenAI API key inválida"
- Verifica tu clave en el archivo `.env`
- Asegúrate de tener créditos en tu cuenta de OpenAI

### WebSocket no conecta
- Verifica que FastAPI esté corriendo
- Revisa que el puerto sea el correcto (8088)
- Asegúrate de estar usando `ws://` y no `http://`

---

## 🚢 Despliegue

### Docker

```bash
# Construir imagen
docker build -t smarthealth-api .

# Ejecutar contenedor
docker run -p 8088:8088 --env-file .env smarthealth-api
```

### Render / Railway / Fly.io

1. Configura las variables de entorno en la plataforma
2. Asegúrate de tener PostgreSQL con pgvector
3. Ejecuta las migraciones de base de datos
4. Deploy automático desde GitHub

---

## 📚 Recursos Adicionales

- [Documentación FastAPI](https://fastapi.tiangolo.com/)
- [Documentación pgvector](https://github.com/pgvector/pgvector)
- [Documentación OpenAI](https://platform.openai.com/docs)
- [WebSocket Protocol](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)

---

## 👥 Contribuidores

- **Ivan Ospino** - Backend & RAG Implementation
- **Gisell Anaya** - Database Design & Models
- **Jhoan Smith** - WebSocket & Real-time Features
- **Jeison Mendez** - Authentication & Security

---

## 📄 Licencia

Este proyecto es privado y pertenece al equipo de desarrollo de SmartHealth.

---

## 🆘 Soporte

Para reportar bugs o solicitar features, crea un issue en el repositorio de GitHub.

**Repositorio**: https://github.com/Ospino89/-backend-fapi-bdi-smart_health

---

**¡Gracias por usar SmartHealth! 🏥💙**
