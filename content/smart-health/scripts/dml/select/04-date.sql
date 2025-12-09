SELECT AGE(NOW(), DATE '2007-10-30') AS AGE;

SELECT
    AVG(EXTRACT(YEAR FROM AGE(birth_date))) AS avg_years
FROM smart_health.patients;

SELECT
    MAX(appointment_date) 
FROM smart_health.appointments;

    MIN(appointment_date) 
FROM smart_health.appointments;

-- Obtener la cita maxima y minima con el nombre de sus pacientes
SELECT
    T1.first_name||' '||COALESCE(T1.middle_name,'')||' '||T1.first_surname||' '||COALESCE(T1.second_surname,'') AS Paciente,
    T2.appointment_date AS FECHA_MIN

FROM smart_health.patients T1
INNER JOIN smart_health.appointments T2
    ON T1.patient_id = T2.patient_id
WHERE T2.appointment_date = (
    SELECT MIN(appointment_date) FROM smart_health.appointments
)
LIMIT 1;

SELECT
    T1.first_name||' '||COALESCE(T1.middle_name,'')||' '||T1.first_surname||' '||COALESCE(T1.second_surname,'') AS Paciente,
    T2.appointment_date AS FECHA_MAX

FROM smart_health.patients T1
INNER JOIN smart_health.appointments T2
    ON T1.patient_id = T2.patient_id
WHERE T2.appointment_date = (
    SELECT MAX(appointment_date) FROM smart_health.appointments
)
LIMIT 1;



-- Top 5 de los pacientes mas viejos
SELECT
    first_name||' '||COALESCE(middle_name, '')||' '||first_surname||' '||COALESCE(second_surname, '') AS nombre_completo,
    EXTRACT(YEAR FROM birth_date) AS age

FROM smart_health.patients
GROUP BY first_name, middle_name, first_surname, second_surname, birth_date
ORDER BY age DESC
LIMIT 5;

-- 1. Obtener todos los pacientes que nacieron en el mes actual,
-- mostrando su nombre completo, fecha de nacimiento y edad actual en años.
-- Dificultad: BAJA
SELECT
    first_name||' '||COALESCE(middle_name, '')||' '||first_surname||' '||COALESCE(second_surname, '') AS nombre_completo,
    birth_date,
    EXTRACT(MONTH FROM CURRENT_DATE) AS mes_actual
    
FROM smart_health.patients
WHERE EXTRACT(MONTH FROM birth_date) = EXTRACT(MONTH FROM CURRENT_DATE);


-- 2. Listar todas las citas programadas para los próximos 7 días,
-- mostrando la fecha de la cita, el nombre del paciente, el nombre del doctor,
-- y cuántos días faltan desde hoy hasta la cita.
-- Dificultad: BAJA


-- 3. Mostrar todos los médicos que ingresaron al hospital hace más de 5 años,
-- incluyendo su nombre completo, fecha de ingreso, y la cantidad exacta de años,
-- meses y días que han trabajado en el hospital.
-- Dificultad: BAJA-INTERMEDIA


-- 4. Obtener las prescripciones emitidas en el último mes,
-- mostrando la fecha de prescripción, el nombre del medicamento,
-- el nombre del paciente, cuántos días han pasado desde la prescripción,
-- y el día de la semana en que fue prescrito.
-- Dificultad: INTERMEDIA


-- 5. Listar todos los pacientes registrados en el sistema durante el trimestre actual,
-- mostrando su nombre completo, fecha de registro, edad actual,
-- el trimestre de registro, y cuántas semanas han pasado desde su registro,
-- ordenados por fecha de registro más reciente primero.
-- Dificultad: INTERMEDIA