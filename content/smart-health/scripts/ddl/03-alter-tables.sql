-- ##################################################
-- #         SMART HEALTH ALTER TABLE SCRIPT        #
-- ##################################################
-- This script contains one alteration to enhance the Smart Health database structure,
-- including adding new columns, modifying constraints, and implementing additional
-- validation rules to better support healthcare management requirements and improve
-- data integrity across the system.

-- ##################################################
-- #                ALTERATIONS                     #
-- ##################################################

-- Add a 'blood_type' column to the PATIENTS table to store patient blood type
-- This is critical medical information needed for emergencies and transfusions
ALTER TABLE smart_health.patients 
ADD COLUMN blood_type VARCHAR(5) CHECK (blood_type IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'));

COMMENT ON COLUMN smart_health.patients.blood_type IS 'Tipo de sangre del paciente (A+, A-, B+, B-, AB+, AB-, O+, O-)';

-- ============================================
-- CONSTRAINTS PARA ALERGIAS
-- ============================================
ALTER TABLE smart_health.patient_allergies
ADD CONSTRAINT chk_patient_severity
CHECK (severity IN ('Leve', 'Moderada', 'Grave', 'Crítica', 'Letal'));

-- ============================================
-- CONSTRAINTS PARA TIPOS DE DIRECCIONES
-- ============================================

-- Constraint para tipos de direcciones de pacientes
ALTER TABLE smart_health.patient_addresses
ADD CONSTRAINT chk_patient_address_type 
CHECK (address_type IN ('Casa', 'Trabajo', 'Facturación', 'Temporal', 'Contacto Emergencia'));

-- Constraint para tipos de direcciones de doctores
ALTER TABLE smart_health.doctor_addresses
ADD CONSTRAINT chk_doctor_address_type 
CHECK (address_type IN ('Casa', 'Consultorio', 'Hospital', 'Clínica', 'Administrativa'));

-- ##################################################
-- #           VALIDATION CONSTRAINTS               #
-- ##################################################

-- Ensure sequence_chat_id is positive (message sequence starts at 1)
ALTER TABLE smart_health.audit_logs
ADD CONSTRAINT chk_sequence_chat_id_positive
CHECK (sequence_chat_id > 0);

-- Ensure email format is valid (basic validation)
ALTER TABLE smart_health.users
ADD CONSTRAINT chk_email_format
CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

ALTER TABLE smart_health.users 
ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE smart_health.payment_methods
ADD CONSTRAINT chk_payment_method_type
CHECK (payment_name IN ('Tarjeta de crédito', 'Efectivo', 'Transferencia', 'Tarjeta de débito', 'Bre-B'));


ALTER TABLE smart_health.payments
ADD CONSTRAINT chk_payments_amount CHECK (amount > 0);

ALTER TABLE smart_health.orders
ADD CONSTRAINT chk_orders_total_amount CHECK (total_amount >= 0);

ALTER TABLE smart_health.orders
ADD CONSTRAINT chk_orders_tax_amount CHECK (tax_amount >= 0);


ALTER TABLE smart_health.payments ADD CONSTRAINT fk_payments_orders
    FOREIGN KEY (order_id) REFERENCES smart_health.orders (order_id)
    ON UPDATE CASCADE ON DELETE CASCADE; 

ALTER TABLE smart_health.payments ADD CONSTRAINT fk_payment_methods_payments
    FOREIGN KEY (payment_method_id) REFERENCES smart_health.payment_methods(payment_method_id)
    ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE smart_health.orders
ALTER COLUMN appointment_id DROP NOT NULL;


-- ##################################################
-- #                 END OF SCRIPT                  #
-- ##################################################