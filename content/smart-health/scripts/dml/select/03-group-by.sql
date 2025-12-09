SELECT
    COUNT(*)
FROM smart_health.patients T1
INNER JOIN smart_health.document_types T2
USING (document_type_id);

-- 1. Contar cuántos pacientes están registrados por cada tipo de documento,
-- mostrando el nombre del tipo de documento y la cantidad total de pacientes,
-- ordenados por cantidad de mayor a menor.

-- INNER JOIN
-- smart_health.patients: FK(document_type_id)
-- smart_health.document_types: PK(document_type_id)
-- AGREGATION FUNCTION: COUNT
SELECT
    T2.type_name AS tipo_documento,
    COUNT(*) AS total_documentos

FROM smart_health.patients T1
INNER JOIN smart_health.document_types T2
    ON T1.document_type_id = T2.document_type_id
GROUP BY T2.type_name
--ORDER BY COUNT(*) DESC;
ORDER BY total_documentos DESC;

--                            tipo_documento                            | total_documentos
-- ---------------------------------------------------------------------+------------------
--  Cédula de Ciudadanía                                                |             7630
--  Número Único de Identificación Personal (NUIP)                      |             7594
--  Registro Civil de Nacimiento                                        |             7490
--  Cédula de Extranjería / Identificación de Extranjería               |             7482
--  Tarjeta de Identidad                                                |             7481
--  Número de Identificación establecido por la Secretaría de Educación |             7457
--  Certificado Cabildo                                                 |             7450
--  Número de Identificación Personal (NIP)                             |             7416
-- (8 filas)



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
--           nombre_completo          | age
-- -----------------------------------+------
--  Carolina Del Pilar Rincón Ramírez | 2006
--  María Isabel Díaz León            | 2006
--  Rodrigo Carolina Martínez Torres  | 2006
--  Karen  Ortiz Pardo                | 2006
--  Tatiana Lucía Cabrera Ramírez     | 2006
-- (5 filas)





-- 2. Obtener la cantidad de citas programadas por cada médico,
-- mostrando el nombre completo del doctor y el total de citas,
-- filtrando solo médicos con más de 5 citas, ordenados por cantidad descendente.
SELECT
    T1.first_name||' '||T1.last_name AS doctor,
    COUNT(*) AS total_citas

FROM smart_health.doctors T1
INNER JOIN smart_health.appointments T2
    ON T1.doctor_id = T2.doctor_id
GROUP BY T1.doctor_id, T1.first_name, T1.last_name
HAVING COUNT(*) > 5
ORDER BY total_citas DESC
LIMIT 5;
--      doctor      | total_citas
-- -----------------+-------------
--  Carlos Ramírez  |          23
--  Vanessa Rojas   |          21
--  Pedro Gil       |          21
--  María Soto      |          20
--  Tatiana Salazar |          20
-- (5 filas)



-- 3. Contar cuántas especialidades tiene cada médico activo,
-- mostrando el nombre del doctor y el número total de especialidades,
-- ordenados por cantidad de especialidades de mayor a menor.
SELECT
    T1.first_name||' '||T1.last_name AS doctor,
    COUNT(*) AS total_especialidades
FROM smart_health.doctors T1
INNER JOIN smart_health.doctor_specialties T2
    ON T1.doctor_id = T2.doctor_id
WHERE T1.active = TRUE
GROUP BY T1.doctor_id, T1.first_name, T1.last_name
ORDER BY total_especialidades DESC
LIMIT 5;
--      doctor     | total_especialidades
-- ----------------+----------------------
--  Adriana Gómez  |                    6
--  Jorge Lozano   |                    5
--  Juan Salazar   |                    5
--  Luis Martínez  |                    5
--  Fernando Silva |                    5
-- (5 filas)



-- 4. Calcular cuántos pacientes residen en cada departamento,
-- mostrando el nombre del departamento y la cantidad total de pacientes,
-- filtrando solo departamentos con al menos 3 pacientes, ordenados alfabéticamente.
SELECT
    T5.department_name,
    COUNT(*) AS total_pacientes

FROM smart_health.patients T1
INNER JOIN smart_health.patient_addresses T2
    ON T1.patient_id = T2.patient_id
INNER JOIN smart_health.addresses T3
    ON T2.address_id = T3.address_id
INNER JOIN smart_health.municipalities T4
    ON T3.municipality_code = T4.municipality_code
INNER JOIN smart_health.departments T5
    ON T4.department_code = T5.department_code
GROUP BY T5.department_code, T5.department_name
HAVING COUNT(*) >= 3
ORDER BY T5.department_name;
--                      department_name                      | total_pacientes
-- ----------------------------------------------------------+-----------------
--  AMAZONAS                                                 |             146
--  ANTIOQUIA                                                |           10159
--  ARAUCA                                                   |             592
--  ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA |             136
--  ATLÁNTICO                                                |            1861
--  BOGOTÁ, D.C.                                             |              70
--  BOLÍVAR                                                  |            3783
--  BOYACÁ                                                   |            9884
--  CALDAS                                                   |            2209
--  CAQUETÁ                                                  |            1296
--  CASANARE                                                 |            1535
--  CAUCA                                                    |            3497
--  CESAR                                                    |            1963
--  CHOCÓ                                                    |            2602
--  CÓRDOBA                                                  |            2511
--  CUNDINAMARCA                                             |            9148
--  GUAINÍA                                                  |              83
--  GUAVIARE                                                 |             383
--  HUILA                                                    |            3127
--  LA GUAJIRA                                               |            1227
--  MAGDALENA                                                |            2414
--  META                                                     |            2396
--  NARIÑO                                                   |            5333
--  NORTE DE SANTANDER                                       |            3294
--  PUTUMAYO                                                 |            1142
--  QUINDIO                                                  |             982
--  RISARALDA                                                |            1184
--  SANTANDER                                                |            7083
--  SUCRE                                                    |            2094
--  TOLIMA                                                   |            3588
--  VALLE DEL CAUCA                                          |            3410
--  VAUPÉS                                                   |             221
--  VICHADA                                                  |             296
-- (33 filas)



-- 5. Contar cuántas citas ha tenido cada paciente por estado de cita,
-- mostrando el nombre del paciente, estado de la cita y cantidad,
-- ordenados por nombre de paciente y estado.
SELECT
    T1.first_name||' '||COALESCE(T1.middle_name, '')||' '||T1.first_surname||' '||COALESCE(T1.second_surname, '') AS paciente,
    T2.status,
    COUNT(*) AS total_citas

FROM smart_health.patients T1
INNER JOIN smart_health.appointments T2
    ON T1.patient_id = T2.patient_id
GROUP BY T1.first_name, T1.middle_name, T1.first_surname, T1.second_surname, T2.status
ORDER BY T1.first_name, T2.status;
--LIMIT 5;
--            paciente           |  status  | total_citas
-- ------------------------------+----------+-------------
--  Adriana  Mejía Hernández     | Attended |           1
--  Adriana  Soto Díaz           | Attended |           1
--  Adriana Lucía Álvarez Peña   | Attended |           1
--  Adriana  Pérez Rojas         | Attended |           1
--  Adriana Patricia Ruiz Lozano | Attended |           1
-- (5 filas)



-- 6. Calcular cuántos registros médicos ha realizado cada doctor,
-- mostrando el nombre del doctor y el total de registros,
-- filtrando solo doctores con más de 10 registros, ordenados por cantidad descendente.
SELECT
    T1.first_name||' '||T1.last_name AS doctor,
    COUNT(*) AS total_registros

FROM smart_health.doctors T1
INNER JOIN smart_health.medical_records T2
    ON T1.doctor_id = T2.doctor_id
GROUP BY T1.doctor_id, T1.first_name, T1.last_name
HAVING COUNT(*) > 10
ORDER BY total_registros DESC;
--  doctor | total_registros
-- --------+-----------------
-- (0 filas)



-- 7. Contar cuántas prescripciones se han emitido para cada medicamento,
-- mostrando el nombre comercial del medicamento y el total de prescripciones,
-- filtrando medicamentos con al menos 2 prescripciones, ordenados por cantidad descendente.
SELECT
    T2.commercial_name,
    COUNT(*) AS total_medicamentos

FROM smart_health.prescriptions T1
INNER JOIN smart_health.medications T2
    ON T1.medication_id = T2.medication_id
GROUP BY T2.commercial_name
HAVING COUNT(*) >= 2
ORDER BY total_medicamentos DESC;
-- LIMIT 5;
--   commercial_name  | total_medicamentos
-- -------------------+--------------------
--  OXIMETAZOLINA MK  |                 77
--  METOCLOPRAMIDA MK |                 76
--  ACETILCISTEÍNA MK |                 72
--  DILTIAZEM MK      |                 64
--  DIGOXINA MK       |                 63
-- (5 filas)



-- 8. Calcular cuántos pacientes tienen alergias por cada medicamento,
-- mostrando el nombre del medicamento y la cantidad de pacientes alérgicos,
-- ordenados por cantidad de mayor a menor.
SELECT
    T3.commercial_name,
    COUNT(*) AS total_pacientes

FROM smart_health.patients T1
INNER JOIN smart_health.patient_allergies T2
    ON T1.patient_id = T2.patient_id
INNER JOIN smart_health.medications T3
    ON T2.medication_id = T3.medication_id
GROUP BY T3.commercial_name
ORDER BY total_pacientes DESC;
--LIMIT 5;
--   commercial_name  | total_pacientes
-- -------------------+-----------------
--  OXIMETAZOLINA MK  |             600
--  ENTACAPONA MK     |             461
--  METOCLOPRAMIDA MK |             455
--  OXITOCINA MK      |             444
--  DILTIAZEM MK      |             425
-- (5 filas)



-- 9. Contar cuántas direcciones tiene registrado cada paciente,
-- mostrando el nombre del paciente y el total de direcciones,
-- filtrando solo pacientes con más de 1 dirección, ordenados por cantidad descendente.
SELECT
    T1.first_name||' '||COALESCE(T1.middle_name, '')||' '||T1.first_surname||' '||COALESCE(T1.second_surname, '') AS paciente,
    COUNT(*) AS total_direcciones

FROM smart_health.patients T1
INNER JOIN smart_health.patient_addresses T2
    ON T1.patient_id = T2.patient_id
GROUP BY T1.first_name, T1.middle_name, T1.first_surname, T1.second_surname
HAVING COUNT(*) > 1
ORDER BY total_direcciones;
--LIMIT 5;
--            paciente           | total_direcciones
-- ------------------------------+-------------------
--  Felipe  Hernández Vargas     |                 2
--  Laura Paola Salazar Cárdenas |                 2
--  Valentina  Silva Soto        |                 2
--  Adriana Lucía Ruiz Vargas    |                 2
--  Luis Mauricio Gómez Vargas   |                 2
-- (5 filas)



-- 10. Calcular cuántas salas de cada tipo están activas en el hospital,
-- mostrando el tipo de sala y la cantidad total,
-- filtrando solo tipos con al menos 2 salas, ordenados por cantidad descendente.
SELECT
    room_type,
    COUNT(*) AS total_salas

FROM smart_health.rooms
WHERE active = TRUE
GROUP BY room_type
HAVING COUNT(*) >= 2
ORDER BY total_salas DESC;
--       room_type      | total_salas
-- ---------------------+-------------
--  Farmacia            |          19
--  Cardiología         |          19
--  Odontología         |          16
--  Cuidados Intensivos |          15
--  Pediatría           |          14
--  Consulta Externa    |          13
--  Traumatología       |          12
--  Cirugía             |          12
--  Radiología          |          12
--  Psiquiatría         |          11
--  Rehabilitación      |          11
--  Ginecología         |          10
--  Emergencia          |          10
--  Oncología           |           9
--  Hospitalización     |           8
--  Laboratorio         |           7
-- (16 filas)


-- 1. Contar cuántos pacientes están registrados por cada tipo de documento,
-- mostrando el nombre del tipo de documento y la cantidad total de pacientes,
-- ordenados por cantidad de mayor a menor.
-- Dificultad: BAJA

-- INNER JOIN
-- smart_health.patients: FK(document_type_id)
-- smart_health.document_types: PK(document_type_id)
-- AGREGATION FUNCTION: COUNT
SELECT
    T2.type_name AS tipo_documento,
    COUNT(*) AS total_documentos

FROM smart_health.patients T1
INNER JOIN smart_health.document_types T2
    ON T1.document_type_id = T2.document_type_id
GROUP BY T2.type_name
--ORDER BY COUNT(*) DESC;
ORDER BY total_documentos DESC;

--                            tipo_documento                            | total_documentos
-- ---------------------------------------------------------------------+------------------
--  Cédula de Ciudadanía                                                |             7630
--  Número Único de Identificación Personal (NUIP)                      |             7594
--  Registro Civil de Nacimiento                                        |             7490
--  Cédula de Extranjería / Identificación de Extranjería               |             7482
--  Tarjeta de Identidad                                                |             7481
--  Número de Identificación establecido por la Secretaría de Educación |             7457
--  Certificado Cabildo                                                 |             7450
--  Número de Identificación Personal (NIP)                             |             7416
-- (8 filas)



-- 2. Mostrar el número de citas programadas por cada médico,
-- incluyendo el nombre completo del doctor y el total de citas,
-- ordenadas alfabéticamente por apellido del médico.
-- Dificultad: BAJA
SELECT
    T1.first_name||' '||T1.last_name AS doctor,
    COUNT(*) AS total_citas

FROM smart_health.doctors T1
INNER JOIN smart_health.appointments T2
    ON T1.doctor_id = T2.doctor_id
GROUP BY T1.doctor_id, T1.first_name, T1.last_name
ORDER BY T1.last_name
LIMIT 5;


-- 3. Calcular el promedio de edad de los pacientes agrupados por género,
-- mostrando el género y la edad promedio redondeada a dos decimales.
-- Dificultad: INTERMEDIA
SELECT
    gender,
    ROUND(AVG(EXTRACT(YEAR FROM AGE(birth_date))),2) AS promedio_edad

FROM smart_health.patients
GROUP BY gender;
--  gender | promedio_edad
-- --------+-------
--  M      | 41.90
--  O      | 41.87
--  F      | 41.96
-- (3 filas)



-- 4. Obtener el número total de prescripciones realizadas por cada medicamento,
-- mostrando el nombre comercial del medicamento, el principio activo,
-- y la cantidad de veces que ha sido prescrito, solo para aquellos medicamentos
-- que tengan al menos 5 prescripciones.
-- Dificultad: INTERMEDIA
SELECT
    T2.commercial_name,
    T2.active_ingredient,
    COUNT(*) AS total_prescripciones

FROM smart_health.prescriptions T1
INNER JOIN smart_health.medications T2
    ON T1.medication_id = T2.medication_id
GROUP BY T2.commercial_name, T2.active_ingredient
HAVING COUNT(*) >= 5
ORDER BY total_prescripciones DESC;
--LIMIT 5;
--   commercial_name  | active_ingredient | total_prescripciones
-- -------------------+-------------------+----------------------
--  OXIMETAZOLINA MK  | OXIMETAZOLINA     |                   77
--  METOCLOPRAMIDA MK | METOCLOPRAMIDA    |                   76
--  ACETILCISTEÍNA MK | ACETILCISTEÍNA    |                   72
--  DILTIAZEM MK      | DILTIAZEM         |                   64
--  DIGOXINA MK       | DIGOXINA          |                   63
-- (5 filas)



-- 5. Listar el número de citas por estado y tipo de cita,
-- mostrando cuántas citas existen para cada combinación de estado y tipo,
-- ordenadas primero por estado y luego por la cantidad de citas de mayor a menor,
-- incluyendo solo aquellas combinaciones que tengan más de 3 citas.
-- Dificultad: INTERMEDIA-ALTA
SELECT
    status,
    appointment_type,
    COUNT(*) AS total_citas

FROM smart_health.appointments
GROUP BY status, appointment_type
HAVING COUNT(*) >= 3
ORDER BY status, 
total_citas DESC;
--LIMIT 5;

--   status  | appointment_type | total_citas
-- ----------+------------------+-------------
--  Attended | Examen Médico    |        2189
--  Attended | Consulta General |        2183
--  Attended | Nutrición        |        2162
--  Attended | Teleconsulta     |        2152
--  Attended | Control          |        2150
-- (5 filas)