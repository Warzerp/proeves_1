-- Mostrar los pacientes (primer nombre, genero y correo y numero de telefono) y los datos del numero de telefono, para los siguientes pacientes. 
-- Filtrar por el campo numero_documento['30451580','1006631391','1009149871','1298083','1004928596','1008188849','1607132','30470003']

-- INNER JOIN

-- smart_health.patients : patient_id(PK)
-- smart_health.patient_phones : patient_id(FK)

-- primer nombre
-- genero
-- correo 
-- numero de telefono

--Pasos: from, joins, condiciones, ordenamiento, limites
SELECT
    A.first_name AS primer_nombre,
    A.gender AS genero,
    A.email AS correo,
    B.phone_number AS numero_telefono

FROM smart_health.patients A
INNER JOIN smart_health.patient_phones B 
    ON A.patient_id = B.patient_id
WHERE A.document_number IN 
(
    '1006631391',
    '1009149871',
    '1298083',
    '1004928596',
    '1008188849',
    '1607132',
    '30470003'
);

-- Obtener los pacientes (primer nombre, genero y correo y numero de telefono), para los siguientes pacientes. 
-- Filtrar por el campo numero_documento['30451580','1006631391','1009149871','1298083','1004928596','1008188849','1607132','30470003']

-- INNER JOIN

-- smart_health.patients : patient_id(PK)
-- smart_health.patient_phones : patient_id(FK)

-- primer nombre
-- genero
-- correo 
-- numero de telefono

--Pasos: from, joins, condiciones, ordenamiento, limites
SELECT
    B.first_name AS primer_nombre,
    B.gender AS genero,
    B.email AS correo,
    A.phone_number AS numero_telefono

FROM smart_health.patient_phones A
RIGHT JOIN smart_health.patients B 
    ON A.patient_id = B.patient_id
WHERE B.document_number IN 
(
    '30451580',
    '1006631391',
    '1009149871',
    '1298083',
    '1004928596',
    '1008188849',
    '1607132',
    '30470003'
);

-- Obtener cuantos medicos no tienen una direccion asociado
-- LEFT JOIN
-- smart_health.doctors: doctor_id(PK)
-- smart_health.doctor_adresses: doctor_id(PK)

SELECT 
    COUNT(*) AS total_doctores_sin_direccion

FROM smart_health.doctors A
LEFT JOIN smart_health.doctor_addresses B
    ON A.doctor_id = B.doctor_id
WHERE B.doctor_id IS NULL;

-- Mostrar el nombre completo del paciente, el genero, tipo de sangre, direccion, ciudad y departamento
-- De los pacientes que viven en Pamplona, Norte de Santander
-- Ordenar por el primer nombre de forma alfabetica 
-- Mostrar los primeros 5 resultados
-- COALESCE(campo, valor)
-- LEFT JOIN
-- smart_health.patients : patient_id(PK)
-- smart_health.patient_addresses : patient_id(FK); ; adress_id(FK)
-- smart_health.addresses : patient_id(FK); adress_id(PK)
-- smart_health.municipalities : municipality_code(PK)
-- smart_health.departements : department_code(PK)
-- nombre completo
-- genero
-- tipo de sangre
-- direccion
-- ciudad 
-- departamento
SELECT
    T1.first_name||' '||COALESCE(T1.middle_name, '')||' '||T1.first_surname||' '||COALESCE(T1.second_surname, '') AS nombre_completo,
    T1.gender,
    T1.blood_type,
    T2.address_type,
    T3.address_line,
    T3.postal_code,
    T4.municipality_name,
    T5.department_name

FROM smart_health.patients T1
INNER JOIN smart_health.patient_addresses T2
    ON T1.patient_id = T2.patient_id
INNER JOIN smart_health.addresses T3
    ON T3.address_id = T2.address_id
INNER JOIN smart_health.municipalities T4
    ON T4.municipality_code = T3.municipality_code
INNER JOIN smart_health.departments T5
    ON T5.department_code = T4.department_code
WHERE T4.municipality_name LIKE '%PAMPLONA%'
ORDER BY T1.first_name
LIMIT 5;

--         nombre_completo         | gender | blood_type | address_type |                        address_line                        | postal_code | municipality_name |  department_name
-- --------------------------------+--------+------------+--------------+------------------------------------------------------------+-------------+-------------------+--------------------
--  Adriana  Aguirre Rojas         | F      | O+         | Casa         | Limite Urbano - Urbano                                     | 251238      | PAMPLONA          | NORTE DE SANTANDER
--  Adriana  Ríos Cabrera          | F      | O+         | Casa         | Rural - Municipio Belén - Mpio. Onzaga Y Coromoro          | 852050      | PAMPLONA          | NORTE DE SANTANDER
--  Adriana Patricia Díaz Pérez    | F      | O+         | Casa         | Vía Ventaquemada-Tunja - Rural - Municipio Samacá          | 991058      | PAMPLONA          | NORTE DE SANTANDER
--  Adriana  León Rojas            | O      | A+         | Casa         | Rural - M. Fómeque Y San Juanito - Municipio Villavicencio | 540004      | PAMPLONA          | NORTE DE SANTANDER
--  Alejandro Ángel González Pérez | O      | O-         | Trabajo      | Rural - Municipio Jericó - Río Pauto Y (Permanente)        | 414047      | PAMPLONA          | NORTE DE SANTANDER
-- (5 filas)



-- 1. Obtener los nombres, apellidos y número de documento de los pacientes junto con el nombre del tipo de documento al que pertenecen.

SELECT
    A.first_name||' '||COALESCE(A.middle_name, '') AS nombres,
    A.first_surname||' '||COALESCE(A.second_surname, '') AS apellidos,
    A.document_number,
    B.type_name
FROM smart_health.patients A 
JOIN smart_health.document_types B
    ON A.document_type_id = B.document_type_id
LIMIT 5;
--     nombres     |    apellidos    | document_number |                              type_name
-- ----------------+-----------------+-----------------+---------------------------------------------------------------------
--  Manuel Natalia | Montoya Torres  | 1009634800      | Número de Identificación Personal (NIP)
--  Juliana        | López Cabrera   | 1007542468      | Número de Identificación establecido por la Secretaría de Educación
--  Diego          | Pérez Pineda    | 30163023        | Tarjeta de Identidad
--  Laura          | Morales León    | 30995750        | Certificado Cabildo
--  Gabriela       | López Cifuentes | 1461283         | Cédula de Extranjería / Identificación de Extranjería
-- (5 filas)



-- 2. Listar los nombres de los municipios y las direcciones registradas en cada uno, de manera que se muestren todos los municipios, incluso los que no tengan direcciones asociadas.
SELECT
    A.municipality_name,
    B.address_line

FROM smart_health.municipalities A
LEFT JOIN smart_health.addresses B
    ON A.municipality_code = B.municipality_code
--ORDER BY A.municipality_name, B.address_line
LIMIT 5;
--  municipality_name |                           address_line
-- -------------------+-------------------------------------------------------------------
--  ITAGÜÍ            | Limite Urbano - Limite Urbano
--  MACARAVITA        | Municipio Simacota - M. Contratación Y Guadalupe - Rural
--  ISTMINA           | Rural - Mpio. Colombia Y Dolores
--  JERICÓ            | Municipio Leguizamo - Mpio. Pto. Caicedo Y Pto. Guzmán
--  ELÍAS             | Alto Del Boquerón Y Relieve Mon. - Rural - Municipio San Jeronimo
-- (5 filas)



-- 3. Consultar las citas médicas junto con el nombre y apellido del médico asignado, filtrando solo las citas con estado “Confirmed”.
SELECT
    A.appointment_type,
    B.first_name,
    B.last_name

FROM smart_health.appointments A 
INNER JOIN smart_health.doctors B
    ON A.doctor_id = B.doctor_id
WHERE A.status = 'Confirmed'
--ORDER BY B.last_name
LIMIT 5;
--  appointment_type | first_name | last_name
-- ------------------+------------+-----------
--  Nutrición        | Cristian   | Suárez
--  Nutrición        | Andrea     | Lozano
--  Vacunación       | Sara       | Pérez
--  Consulta General | Andrea     | Soto
--  Vacunación       | Camila     | Álvarez
-- (5 filas)



-- 4. Mostrar los nombres y apellidos de los pacientes junto con su dirección principal, de forma que aparezcan también los pacientes sin dirección registrada.
SELECT
    A.first_name||' '||COALESCE(A.middle_name, '') AS nombres,
    A.first_surname||' '||COALESCE(A.second_surname, '') AS apellidos,
    C.address_line

FROM smart_health.patients A
LEFT JOIN smart_health.patient_addresses B
    ON A.patient_id = B.patient_id
    AND B.is_primary = TRUE
LEFT JOIN smart_health.addresses C
    ON B.address_id = C.address_id
LIMIT 5;
--     nombres     |    apellidos    |                              address_line
-- ----------------+-----------------+------------------------------------------------------------------------
--  Manuel Natalia | Montoya Torres  |
--  Juliana        | López Cabrera   | Arroyo San Vicente - Mpio. Sahagún Y La Unión - Rural
--  Diego          | Pérez Pineda    |
--  Laura          | Morales León    | Rural - M. Garagoa, Miraflo., Berbeo Y San Edu. - Mpio. Rondón Y Pesca
--  Gabriela       | López Cifuentes | Via Cucun.-Lenguaz.-Turmeque - Municipio Chocontá
-- (5 filas)


-- 5. Agrupar los pacientes por tipo de sangre y mostrar la cantidad de tipos de sangre que tienen cada uno.
SELECT   
    blood_type,
    COUNT(*) AS cantidad
FROM smart_health.patients
GROUP BY blood_type
ORDER BY cantidad DESC;

--  blood_type | cantidad
-- ------------+----------
--  O+         |    32502
--  O-         |    10193
--  A+         |     8167
--  AB+        |     3960
--  A-         |     3158
--  B+         |     2011
--  B-         |        5
--  AB-        |        4
-- (8 filas)