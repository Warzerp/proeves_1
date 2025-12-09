"""
Generate Embeddings for Smart Health Database
==============================================
Este script genera embeddings reales usando OpenAI para todas las tablas
que requieren búsqueda semántica en la base de datos.
"""

import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path para imports
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

from openai import OpenAI
from sqlalchemy import text
from src.app.database.database import get_db
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Inicializar cliente de OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_embedding(text: str) -> list:
    """
    Genera un embedding usando OpenAI text-embedding-ada-002
    
    Args:
        text: Texto para generar el embedding
        
    Returns:
        Lista de floats representando el embedding (1536 dimensiones)
    """
    try:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ Error generando embedding: {e}")
        return None

def update_medical_records_embeddings(limit: int = 100):
    """Genera embeddings para medical_records.summary_text"""
    print("\n" + "="*60)
    print("📋 ACTUALIZANDO MEDICAL RECORDS")
    print("="*60)
    
    db = next(get_db())
    
    try:
        # Obtener registros sin embedding usando SQLAlchemy
        result = db.execute(text("""
            SELECT medical_record_id, summary_text 
            FROM smart_health.medical_records 
            WHERE summary_embedding IS NULL
            LIMIT :limit
        """), {"limit": limit})
        
        records = result.fetchall()
        total = len(records)
        print(f"📊 Encontrados {total} registros sin embedding\n")
        
        for i, record in enumerate(records, 1):
            record_id = record[0]
            summary_text = record[1]
            
            embedding = generate_embedding(summary_text)
            if embedding:
                db.execute(text("""
                    UPDATE smart_health.medical_records 
                    SET summary_embedding = :embedding 
                    WHERE medical_record_id = :record_id
                """), {"embedding": embedding, "record_id": record_id})
                db.commit()
                print(f"✅ [{i}/{total}] Medical record {record_id}: {summary_text[:50]}...")
        
        print(f"\n🎉 Completado: {total} registros médicos actualizados")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

def update_patients_embeddings(limit: int = 100):
    """Genera embeddings para nombres completos de pacientes"""
    print("\n" + "="*60)
    print("👥 ACTUALIZANDO PATIENTS")
    print("="*60)
    
    db = next(get_db())
    
    try:
        result = db.execute(text("""
            SELECT patient_id, first_name, middle_name, first_surname, second_surname
            FROM smart_health.patients 
            WHERE fullname_embedding IS NULL
            LIMIT :limit
        """), {"limit": limit})
        
        records = result.fetchall()
        total = len(records)
        print(f"📊 Encontrados {total} pacientes sin embedding\n")
        
        for i, record in enumerate(records, 1):
            patient_id = record[0]
            first_name = record[1]
            middle_name = record[2] or ''
            first_surname = record[3]
            second_surname = record[4] or ''
            
            full_name = f"{first_name} {middle_name} {first_surname} {second_surname}".strip()
            embedding = generate_embedding(full_name)
            if embedding:
                db.execute(text("""
                    UPDATE smart_health.patients 
                    SET fullname_embedding = :embedding 
                    WHERE patient_id = :patient_id
                """), {"embedding": embedding, "patient_id": patient_id})
                db.commit()
                print(f"✅ [{i}/{total}] Patient {patient_id}: {full_name}")
        
        print(f"\n🎉 Completado: {total} pacientes actualizados")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

def update_doctors_embeddings(limit: int = 100):
    """Genera embeddings para nombres de doctores"""
    print("\n" + "="*60)
    print("👨‍⚕️ ACTUALIZANDO DOCTORS")
    print("="*60)
    
    db = next(get_db())
    
    try:
        result = db.execute(text("""
            SELECT doctor_id, first_name, last_name
            FROM smart_health.doctors 
            WHERE fullname_embedding IS NULL
            LIMIT :limit
        """), {"limit": limit})
        
        records = result.fetchall()
        total = len(records)
        print(f"📊 Encontrados {total} doctores sin embedding\n")
        
        for i, record in enumerate(records, 1):
            doctor_id = record[0]
            first_name = record[1]
            last_name = record[2]
            
            full_name = f"{first_name} {last_name}"
            embedding = generate_embedding(full_name)
            if embedding:
                db.execute(text("""
                    UPDATE smart_health.doctors 
                    SET fullname_embedding = :embedding 
                    WHERE doctor_id = :doctor_id
                """), {"embedding": embedding, "doctor_id": doctor_id})
                db.commit()
                print(f"✅ [{i}/{total}] Doctor {doctor_id}: {full_name}")
        
        print(f"\n🎉 Completado: {total} doctores actualizados")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

def update_appointments_embeddings(limit: int = 100):
    """Genera embeddings para motivos de citas"""
    print("\n" + "="*60)
    print("📅 ACTUALIZANDO APPOINTMENTS")
    print("="*60)
    
    db = next(get_db())
    
    try:
        result = db.execute(text("""
            SELECT appointment_id, reason
            FROM smart_health.appointments 
            WHERE reason_embedding IS NULL 
              AND reason IS NOT NULL
            LIMIT :limit
        """), {"limit": limit})
        
        records = result.fetchall()
        total = len(records)
        print(f"📊 Encontrados {total} citas sin embedding\n")
        
        for i, record in enumerate(records, 1):
            appointment_id = record[0]
            reason = record[1]
            
            embedding = generate_embedding(reason)
            if embedding:
                db.execute(text("""
                    UPDATE smart_health.appointments 
                    SET reason_embedding = :embedding 
                    WHERE appointment_id = :appointment_id
                """), {"embedding": embedding, "appointment_id": appointment_id})
                db.commit()
                print(f"✅ [{i}/{total}] Appointment {appointment_id}: {reason[:50]}...")
        
        print(f"\n🎉 Completado: {total} citas actualizadas")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

def update_diagnoses_embeddings(limit: int = 100):
    """Genera embeddings para descripciones de diagnósticos"""
    print("\n" + "="*60)
    print("🩺 ACTUALIZANDO DIAGNOSES")
    print("="*60)
    
    db = next(get_db())
    
    try:
        result = db.execute(text("""
            SELECT diagnosis_id, description
            FROM smart_health.diagnoses 
            WHERE description_embedding IS NULL
            LIMIT :limit
        """), {"limit": limit})
        
        records = result.fetchall()
        total = len(records)
        print(f"📊 Encontrados {total} diagnósticos sin embedding\n")
        
        for i, record in enumerate(records, 1):
            diagnosis_id = record[0]
            description = record[1]
            
            embedding = generate_embedding(description)
            if embedding:
                db.execute(text("""
                    UPDATE smart_health.diagnoses 
                    SET description_embedding = :embedding 
                    WHERE diagnosis_id = :diagnosis_id
                """), {"embedding": embedding, "diagnosis_id": diagnosis_id})
                db.commit()
                print(f"✅ [{i}/{total}] Diagnosis {diagnosis_id}: {description[:50]}...")
        
        print(f"\n🎉 Completado: {total} diagnósticos actualizados")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

def update_medications_embeddings(limit: int = 100):
    """Genera embeddings para medicamentos"""
    print("\n" + "="*60)
    print("💊 ACTUALIZANDO MEDICATIONS")
    print("="*60)
    
    db = next(get_db())
    
    try:
        result = db.execute(text("""
            SELECT medication_id, commercial_name, active_ingredient, presentation
            FROM smart_health.medications 
            WHERE medication_embedding IS NULL
            LIMIT :limit
        """), {"limit": limit})
        
        records = result.fetchall()
        total = len(records)
        print(f"📊 Encontrados {total} medicamentos sin embedding\n")
        
        for i, record in enumerate(records, 1):
            med_id = record[0]
            commercial_name = record[1]
            active_ingredient = record[2]
            presentation = record[3]
            
            combined_text = f"{commercial_name} {active_ingredient} {presentation}"
            embedding = generate_embedding(combined_text)
            if embedding:
                db.execute(text("""
                    UPDATE smart_health.medications 
                    SET medication_embedding = :embedding 
                    WHERE medication_id = :med_id
                """), {"embedding": embedding, "med_id": med_id})
                db.commit()
                print(f"✅ [{i}/{total}] Medication {med_id}: {commercial_name}")
        
        print(f"\n🎉 Completado: {total} medicamentos actualizados")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

def generate_all_embeddings(limit: int = 100):
    """
    Genera embeddings para todas las tablas
    
    Args:
        limit: Número máximo de registros a procesar por tabla
    """
    print("\n" + "="*60)
    print("🚀 INICIANDO GENERACIÓN DE EMBEDDINGS")
    print("="*60)
    print(f"📌 Límite por tabla: {limit} registros")
    print(f"🔑 OpenAI API Key: {'✅ Configurada' if os.getenv('OPENAI_API_KEY') else '❌ NO configurada'}")
    
    if not os.getenv('OPENAI_API_KEY'):
        print("\n❌ ERROR: OPENAI_API_KEY no está configurada en .env")
        return
    
    try:
        # Actualizar cada tabla
        update_medical_records_embeddings(limit)
        update_patients_embeddings(limit)
        update_doctors_embeddings(limit)
        update_appointments_embeddings(limit)
        update_diagnoses_embeddings(limit)
        update_medications_embeddings(limit)
        
        print("\n" + "="*60)
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error general: {e}")

if __name__ == "__main__":
    # Ejecutar con límite de 100 registros por tabla
    # Puedes cambiar este número según necesites
    generate_all_embeddings(limit=100)