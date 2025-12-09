# P4 – Interfaces para el endpoint `/query`

Este documento describe las funciones que Persona 4 expone para la integración con Persona 1.

---

## `build_context(patient, records, similar_chunks, max_tokens=4000)`

**Propósito**: Construir el contexto en texto plano que se enviará al LLM (GPT-4o-mini).

**Parámetros**:
- `patient`: instancia de `PatientInfo` (de `src/app/schemas/clinical.py`)
- `records`: instancia de `ClinicalRecords` (de `src/app/schemas/clinical.py`)
- `similar_chunks`: lista de `SimilarChunk` (de `src/app/schemas/rag.py`)
- `max_tokens`: entero (por defecto 4000)

**Retorno**: `(str, int)` → `(contexto, tokens_usados)`

---

## `build_sources(similar_chunks, records)`

**Propósito**: Generar la lista de fuentes para el JSON de respuesta.

**Retorno**: `List[Dict]` con campos como `type`, `source_type`, `relevance_score`, `text_snippet`, etc.

---

## `build_metadata(records, similar_chunks, query_time_sec, context_tokens)`

**Propósito**: Calcular métricas de rendimiento.

**Retorno**: `Dict` con `total_records_analyzed`, `query_time_ms`, `context_tokens`, etc.

---

✅ Estas funciones están listas para ser llamadas por P1 en `P1-5`.