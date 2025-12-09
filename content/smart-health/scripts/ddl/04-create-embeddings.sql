-- ##################################################
-- #     SMART HEALTH EMBEDDINGS CREATION SCRIPT   #
-- ##################################################
-- This script adds vector embedding columns and indexes for semantic search
-- capabilities across key tables in the Smart Health Hospital Management System.
-- Embeddings enable AI-powered natural language queries and similarity search
-- for improved user experience and clinical decision support.
-- Vector Dimension: 1536 (OpenAI text-embedding-ada-002)
-- Target DBMS: PostgreSQL with pgvector extension

-- ##################################################
-- #         EXTENSION INSTALLATION                 #
-- ##################################################

-- Install pgvector extension
-- Note: This requires that pgvector is already installed in your PostgreSQL instance
-- Installation instructions: https://github.com/pgvector/pgvector or https://www.youtube.com/watch?v=xvRwwAF_-X4
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension is installed
--SELECT * FROM pg_extension WHERE extname = 'vector';

-- ##################################################z
-- #    EMBEDDINGS FOR USER-FOCUSED LLM QUERIES    #
-- ##################################################

BEGIN;

-- ##################################################
-- #      STEP 1: ADD EMBEDDING COLUMNS             #
-- ##################################################

-- 1. AUDIT_LOGS: Historial de conversaciones de usuarios
-- Permite búsqueda semántica de preguntas similares previas
ALTER TABLE smart_health.audit_logs 
ADD COLUMN IF NOT EXISTS question_embedding vector(1536);

COMMENT ON COLUMN smart_health.audit_logs.question_embedding 
IS 'Vector embedding de la pregunta del usuario para búsqueda de conversaciones similares (OpenAI text-embedding-ada-002, 1536 dims)';

-- 2. MEDICAL_RECORDS: Historias clínicas y resúmenes médicos
-- Permite buscar síntomas, tratamientos y condiciones similares
ALTER TABLE smart_health.medical_records 
ADD COLUMN IF NOT EXISTS summary_embedding vector(1536);

COMMENT ON COLUMN smart_health.medical_records.summary_embedding 
IS 'Vector embedding del resumen médico para búsqueda semántica de síntomas, tratamientos y condiciones similares (OpenAI text-embedding-ada-002, 1536 dims)';

-- 3. PATIENTS: Información de pacientes
-- Permite búsqueda semántica por nombre completo
ALTER TABLE smart_health.patients 
ADD COLUMN IF NOT EXISTS fullname_embedding vector(1536);

COMMENT ON COLUMN smart_health.patients.fullname_embedding 
IS 'Vector embedding del nombre completo del paciente para búsqueda por similitud fonética y ortográfica (OpenAI text-embedding-ada-002, 1536 dims)';

-- 4. DOCTORS: Información de doctores
-- Permite búsqueda semántica por nombre de doctor
ALTER TABLE smart_health.doctors 
ADD COLUMN IF NOT EXISTS fullname_embedding vector(1536);

COMMENT ON COLUMN smart_health.doctors.fullname_embedding 
IS 'Vector embedding del nombre completo del doctor para búsqueda por similitud (OpenAI text-embedding-ada-002, 1536 dims)';

-- 5. APPOINTMENTS: Motivos de citas
-- Permite agrupar y buscar citas por motivos similares
ALTER TABLE smart_health.appointments 
ADD COLUMN IF NOT EXISTS reason_embedding vector(1536);

COMMENT ON COLUMN smart_health.appointments.reason_embedding 
IS 'Vector embedding del motivo de la cita para búsqueda semántica y agrupación por temas similares (OpenAI text-embedding-ada-002, 1536 dims)';

-- 6. DIAGNOSES: Descripciones de diagnósticos CIE-10
-- Permite búsqueda de diagnósticos en lenguaje natural
ALTER TABLE smart_health.diagnoses 
ADD COLUMN IF NOT EXISTS description_embedding vector(1536);

COMMENT ON COLUMN smart_health.diagnoses.description_embedding 
IS 'Vector embedding de la descripción del diagnóstico para búsqueda en lenguaje natural (OpenAI text-embedding-ada-002, 1536 dims)';

-- 7. MEDICATIONS: Información de medicamentos
-- Permite búsqueda de medicamentos por nombre comercial, principio activo o uso
ALTER TABLE smart_health.medications 
ADD COLUMN IF NOT EXISTS medication_embedding vector(1536);

COMMENT ON COLUMN smart_health.medications.medication_embedding 
IS 'Vector embedding combinando nombre comercial, principio activo y presentación para búsqueda semántica (OpenAI text-embedding-ada-002, 1536 dims)';

-- ##################################################
-- #      STEP 2: CREATE INDEXES FOR FAST SEARCH    #
-- ##################################################

-- Índice IVFFlat para búsqueda rápida de similitud coseno
-- lists = 100 es apropiado para datasets pequeños-medianos (< 1M registros)
-- Para datasets más grandes, usar lists = sqrt(num_rows)

-- Index 1: audit_logs
CREATE INDEX IF NOT EXISTS idx_audit_logs_question_embedding 
ON smart_health.audit_logs 
USING ivfflat (question_embedding vector_cosine_ops)
WITH (lists = 100);

COMMENT ON INDEX smart_health.idx_audit_logs_question_embedding 
IS 'Índice IVFFlat para búsqueda rápida de similitud coseno en preguntas de usuarios';

-- Index 2: medical_records
CREATE INDEX IF NOT EXISTS idx_medical_records_summary_embedding 
ON smart_health.medical_records 
USING ivfflat (summary_embedding vector_cosine_ops)
WITH (lists = 100);

COMMENT ON INDEX smart_health.idx_medical_records_summary_embedding 
IS 'Índice IVFFlat para búsqueda rápida de similitud coseno en resúmenes médicos';

-- Index 3: patients
CREATE INDEX IF NOT EXISTS idx_patients_fullname_embedding 
ON smart_health.patients 
USING ivfflat (fullname_embedding vector_cosine_ops)
WITH (lists = 100);

COMMENT ON INDEX smart_health.idx_patients_fullname_embedding 
IS 'Índice IVFFlat para búsqueda rápida de similitud en nombres de pacientes';

-- Index 4: doctors
CREATE INDEX IF NOT EXISTS idx_doctors_fullname_embedding 
ON smart_health.doctors 
USING ivfflat (fullname_embedding vector_cosine_ops)
WITH (lists = 100);

COMMENT ON INDEX smart_health.idx_doctors_fullname_embedding 
IS 'Índice IVFFlat para búsqueda rápida de similitud en nombres de doctores';

-- Index 5: appointments
CREATE INDEX IF NOT EXISTS idx_appointments_reason_embedding 
ON smart_health.appointments 
USING ivfflat (reason_embedding vector_cosine_ops)
WITH (lists = 100);

COMMENT ON INDEX smart_health.idx_appointments_reason_embedding 
IS 'Índice IVFFlat para búsqueda rápida de similitud en motivos de citas';

-- Index 6: diagnoses
CREATE INDEX IF NOT EXISTS idx_diagnoses_description_embedding 
ON smart_health.diagnoses 
USING ivfflat (description_embedding vector_cosine_ops)
WITH (lists = 100);

COMMENT ON INDEX smart_health.idx_diagnoses_description_embedding 
IS 'Índice IVFFlat para búsqueda rápida de similitud en descripciones de diagnósticos';

-- Index 7: medications
CREATE INDEX IF NOT EXISTS idx_medications_embedding 
ON smart_health.medications 
USING ivfflat (medication_embedding vector_cosine_ops)
WITH (lists = 100);

COMMENT ON INDEX smart_health.idx_medications_embedding 
IS 'Índice IVFFlat para búsqueda rápida de similitud en medicamentos';

-- ##################################################
-- #      STEP 3: UTILITY FUNCTIONS                 #
-- ##################################################

-- Function 1: Buscar preguntas similares en audit_logs
CREATE OR REPLACE FUNCTION smart_health.find_similar_questions(
    query_embedding vector(1536),
    similarity_threshold float DEFAULT 0.7,
    max_results int DEFAULT 5
)
RETURNS TABLE (
    audit_log_id INTEGER,
    user_id INTEGER,
    question TEXT,
    response_json JSONB,
    similarity_score FLOAT,
    created_at TIMESTAMP
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        al.audit_log_id,
        al.user_id,
        al.question,
        al.response_json,
        (1 - (al.question_embedding <=> query_embedding))::FLOAT as similarity_score,
        al.created_at
    FROM smart_health.audit_logs al
    WHERE al.question_embedding IS NOT NULL
      AND (1 - (al.question_embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY al.question_embedding <=> query_embedding
    LIMIT max_results;
END;
$$;

COMMENT ON FUNCTION smart_health.find_similar_questions IS 
'Busca preguntas similares en el historial de audit_logs usando similitud coseno. 
Parámetros: query_embedding (vector a buscar), similarity_threshold (umbral mínimo 0-1), max_results (máximo de resultados)';

-- Function 2: Buscar registros médicos similares
CREATE OR REPLACE FUNCTION smart_health.find_similar_medical_records(
    query_embedding vector(1536),
    patient_id_filter INTEGER DEFAULT NULL,
    similarity_threshold float DEFAULT 0.7,
    max_results int DEFAULT 10
)
RETURNS TABLE (
    medical_record_id INTEGER,
    patient_id INTEGER,
    doctor_id INTEGER,
    summary_text TEXT,
    similarity_score FLOAT,
    registration_datetime TIMESTAMP
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        mr.medical_record_id,
        mr.patient_id,
        mr.doctor_id,
        mr.summary_text,
        (1 - (mr.summary_embedding <=> query_embedding))::FLOAT as similarity_score,
        mr.registration_datetime
    FROM smart_health.medical_records mr
    WHERE mr.summary_embedding IS NOT NULL
      AND (patient_id_filter IS NULL OR mr.patient_id = patient_id_filter)
      AND (1 - (mr.summary_embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY mr.summary_embedding <=> query_embedding
    LIMIT max_results;
END;
$$;

COMMENT ON FUNCTION smart_health.find_similar_medical_records IS 
'Busca registros médicos similares usando similitud coseno.
Parámetros: query_embedding (vector), patient_id_filter (opcional), similarity_threshold (0-1), max_results';

-- Function 3: Buscar pacientes por nombre similar
CREATE OR REPLACE FUNCTION smart_health.find_similar_patients(
    query_embedding vector(1536),
    similarity_threshold float DEFAULT 0.8,
    max_results int DEFAULT 10
)
RETURNS TABLE (
    patient_id INTEGER,
    full_name TEXT,
    document_number VARCHAR(50),
    similarity_score FLOAT
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.patient_id,
        CONCAT(p.first_name, ' ', COALESCE(p.middle_name, ''), ' ', p.first_surname, ' ', COALESCE(p.second_surname, ''))::TEXT as full_name,
        p.document_number,
        (1 - (p.fullname_embedding <=> query_embedding))::FLOAT as similarity_score
    FROM smart_health.patients p
    WHERE p.fullname_embedding IS NOT NULL
      AND (1 - (p.fullname_embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY p.fullname_embedding <=> query_embedding
    LIMIT max_results;
END;
$$;

COMMENT ON FUNCTION smart_health.find_similar_patients IS 
'Busca pacientes por similitud de nombre usando embeddings.
Parámetros: query_embedding (vector), similarity_threshold (0-1), max_results';

-- Function 4: Buscar doctores por nombre similar
CREATE OR REPLACE FUNCTION smart_health.find_similar_doctors(
    query_embedding vector(1536),
    similarity_threshold float DEFAULT 0.8,
    max_results int DEFAULT 10
)
RETURNS TABLE (
    doctor_id INTEGER,
    full_name TEXT,
    medical_license_number VARCHAR(50),
    similarity_score FLOAT
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.doctor_id,
        CONCAT(d.first_name, ' ', d.last_name)::TEXT as full_name,
        d.medical_license_number,
        (1 - (d.fullname_embedding <=> query_embedding))::FLOAT as similarity_score
    FROM smart_health.doctors d
    WHERE d.fullname_embedding IS NOT NULL
      AND (1 - (d.fullname_embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY d.fullname_embedding <=> query_embedding
    LIMIT max_results;
END;
$$;

COMMENT ON FUNCTION smart_health.find_similar_doctors IS 
'Busca doctores por similitud de nombre usando embeddings.
Parámetros: query_embedding (vector), similarity_threshold (0-1), max_results';

-- Function 5: Buscar diagnósticos por descripción similar
CREATE OR REPLACE FUNCTION smart_health.find_similar_diagnoses(
    query_embedding vector(1536),
    similarity_threshold float DEFAULT 0.7,
    max_results int DEFAULT 10
)
RETURNS TABLE (
    diagnosis_id INTEGER,
    icd_code VARCHAR(10),
    description VARCHAR(500),
    similarity_score FLOAT
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.diagnosis_id,
        d.icd_code,
        d.description,
        (1 - (d.description_embedding <=> query_embedding))::FLOAT as similarity_score
    FROM smart_health.diagnoses d
    WHERE d.description_embedding IS NOT NULL
      AND (1 - (d.description_embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY d.description_embedding <=> query_embedding
    LIMIT max_results;
END;
$$;

COMMENT ON FUNCTION smart_health.find_similar_diagnoses IS 
'Busca diagnósticos por similitud de descripción en lenguaje natural.
Parámetros: query_embedding (vector), similarity_threshold (0-1), max_results';

-- Function 6: Buscar medicamentos por similitud
CREATE OR REPLACE FUNCTION smart_health.find_similar_medications(
    query_embedding vector(1536),
    similarity_threshold float DEFAULT 0.7,
    max_results int DEFAULT 10
)
RETURNS TABLE (
    medication_id INTEGER,
    commercial_name VARCHAR(200),
    active_ingredient VARCHAR(200),
    atc_code VARCHAR(10),
    similarity_score FLOAT
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.medication_id,
        m.commercial_name,
        m.active_ingredient,
        m.atc_code,
        (1 - (m.medication_embedding <=> query_embedding))::FLOAT as similarity_score
    FROM smart_health.medications m
    WHERE m.medication_embedding IS NOT NULL
      AND (1 - (m.medication_embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY m.medication_embedding <=> query_embedding
    LIMIT max_results;
END;
$$;

COMMENT ON FUNCTION smart_health.find_similar_medications IS 
'Busca medicamentos por similitud usando embeddings de nombre comercial y principio activo.
Parámetros: query_embedding (vector), similarity_threshold (0-1), max_results';

-- Function 7: Buscar citas por motivo similar
CREATE OR REPLACE FUNCTION smart_health.find_similar_appointments(
    query_embedding vector(1536),
    patient_id_filter INTEGER DEFAULT NULL,
    similarity_threshold float DEFAULT 0.7,
    max_results int DEFAULT 10
)
RETURNS TABLE (
    appointment_id INTEGER,
    patient_id INTEGER,
    doctor_id INTEGER,
    reason TEXT,
    appointment_date DATE,
    similarity_score FLOAT
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.appointment_id,
        a.patient_id,
        a.doctor_id,
        a.reason,
        a.appointment_date,
        (1 - (a.reason_embedding <=> query_embedding))::FLOAT as similarity_score
    FROM smart_health.appointments a
    WHERE a.reason_embedding IS NOT NULL
      AND (patient_id_filter IS NULL OR a.patient_id = patient_id_filter)
      AND (1 - (a.reason_embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY a.reason_embedding <=> query_embedding
    LIMIT max_results;
END;
$$;

COMMENT ON FUNCTION smart_health.find_similar_appointments IS 
'Busca citas por similitud de motivo usando embeddings.
Parámetros: query_embedding (vector), patient_id_filter (opcional), similarity_threshold (0-1), max_results';

COMMIT;

-- ##################################################
-- #              VERIFICATION QUERIES              #
-- ##################################################

-- Verificar que las columnas se crearon correctamente
-- SELECT 
--     table_name,
--     column_name,
--     data_type
-- FROM information_schema.columns
-- WHERE table_schema = 'smart_health'
--   AND column_name LIKE '%embedding%'
-- ORDER BY table_name, column_name;

-- -- Verificar que los índices se crearon correctamente
-- SELECT 
--     schemaname,
--     tablename,
--     indexname,
--     indexdef
-- FROM pg_indexes
-- WHERE schemaname = 'smart_health'
--   AND indexname LIKE '%embedding%'
-- ORDER BY tablename, indexname;

-- -- Verificar que las funciones se crearon correctamente
-- SELECT 
--     routine_name,
--     routine_type,
--     data_type
-- FROM information_schema.routines
-- WHERE routine_schema = 'smart_health'
--   AND routine_name LIKE 'find_similar%'
-- ORDER BY routine_name;

-- ##################################################
-- #                 END OF SCRIPT                  #
-- ##################################################