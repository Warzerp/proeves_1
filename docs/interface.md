# – Interfaces para el endpoint `/query`

---

## `build_context(patient, records, similar_chunks, max_tokens=4000)`

**Propósito**: Construir el contexto en texto plano que se enviará al LLM (GPT-4o-mini).

**Parámetros**:
- `patient`: instancia de `PatientInfo` (de `src/app/schemas/clinical.py`)
- `records`: instancia de `ClinicalRecords` (de `src/app/schemas/clinical.py`)
- `similar_chunks`: lista de `SimilarChunk` (de `src/app/schemas/rag.py`)
- `max_tokens`: entero (por defecto 4000, límite seguro para GPT-4o-mini)

**Retorno**: `(str, int)` → `(contexto_listo_para_llm, número_de_tokens)`

---

## `build_sources(similar_chunks, records)`

**Propósito**: Generar la lista de fuentes estructuradas para el JSON de respuesta.

**Parámetros**:
- `similar_chunks`: lista de `SimilarChunk`
- `records`: instancia de `ClinicalRecords`

**Retorno**: `List[Dict[str, Any]]` → lista de objetos con:
- `type`: `"vector_search"` o `"clinical_record"`
- `source_type`: tipo de fuente (`"appointment"`, etc.)
- `source_id` / `appointment_id`
- `patient_id` (solo en vector search)
- `relevance_score` (solo en vector search)
- `date` (ISO string)
- `text_snippet`: resumen del contenido

---

## `build_metadata(records, similar_chunks, query_time_sec, context_tokens)`

**Propósito**: Calcular métricas de rendimiento y trazabilidad.

**Parámetros**:
- `records`: `ClinicalRecords`
- `similar_chunks`: `List[SimilarChunk]`
- `query_time_sec`: tiempo total de procesamiento (en segundos, desde que entra la petición hasta antes del LLM)
- `context_tokens`: número de tokens del contexto (salida de `build_context`)

**Retorno**: `Dict[str, Any]` con:
- `total_records_analyzed`: total de registros clínicos procesados
- `vector_chunks_retrieved`: número de chunks devueltos por Vector Search
- `query_time_ms`: tiempo en milisegundos
- `context_tokens`: tokens usados en el contexto
- `sources_used`: total de fuentes incluidas en `sources`

---

✅ Estas funciones están listas para ser llamadas