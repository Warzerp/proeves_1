SELECT
    first_name
FROM smart_health.patients
WHERE UPPER(first_name) = UPPER('julIANA')
LIMIT 5;

SELECT CONCAT(first_name, ' ', middle_name) AS name
FROM smart_health.patients
LIMIT 5;

SELECT
    first_name,
    LENGHT(first_name)

FROM smart_health


-- Top 5 de personas, con los nombres de mayor longitud

SELECT
    first_name,
    LENGHT(first_name) AS total_lenght
FROM smart_health.patients
GROUP BY first_name
ORDER BY total_lenght DESC
LIMIT 5;

SELECT 
    AVG(LENGTH(first_name)) AS promedio
FROM smart_health.patients
WHERE LENGTH(first_name) > AVG(LENGTH(first_name))
ORDER BY total_lenght
LIMIT 5;





SELECT
    sq.first_name,
    sq.total_lenght

FROM(
SELECT
    first_name,
    LENGTH(first_name) AS total_lenght
FROM smart_health.patients
GROUP BY first_name
HAVING LENGTH(first_name) > (
    SELECT ROUND(AVG(LENGTH(first_name)))
    FROM smart_health.patients
)sq
GROUP BY sq.first_name, sq.total_lenght
ORDER BY total_lenght
LIMIT 5;


SELECT
    SPLIT_PART('Alejandro Jaimes', ' ', 2) AS sr;

SELECT DISTINCT email FROM smart_health.patients;



SELECT email,
SPLIT_PART(email, '@', 2) AS domain_email
FROM smart_health.patients
LIMIT 5;




-- CONSULTA
-- DOMINIOS Y CANTIDAD DE VECES

SELECT
    COUNT(*) AS total,
    SPLIT_PART(email, '@', 2) AS domain_email
FROM smart_health.patients
GROUP BY domain_email;
--ORDER BY total DESC; 

SELECT SUM(sq.total_emails) AS (
    SELECT
    COUNT(*) AS total
    SPLIT_PART(email, '@', 2) AS domain_email
FROM smart_health.patients
WHERE SPLIT_PART(email, '@', 2) IN ('gmail.com', 'hotmail.com', 'yahoo.com')
);
SELECT SUBSTRING('HOLA', 1, 1);

SELECT SUBSTRING('HOLA', 2, LENGTH('HOLA') - 1);

-- G. A. Santafe
SELECT 
    CONCAT(SUBSTRING(SPLIT_PART('Gisell Anaya', ' ', 1), 1, 1 ),
    SUBSTRING(SPLIT_PART('Gisell Anaya', ' ', 2), 1, 1),
    SPLIT_PART('Gisell Anaya', ' ', 3)) AS report_name;

-- EL nombre completo mas largo de los pacientes
-- Desempate por primer_nombre

SELECT
    CONCAT(first_name, ' ', middle_name)
FROM smart_health.patients 
WHERE first_name LIKE 'Adriana%'
LIMIT 5;


SELECT
    CONCAT(first_name, ' ', middle_name)
FROM smart_health.patients 
WHERE CONCAT(first_name, ' ', middle_name) LIKE 'Adriana%'
LIMIT 5;

SELECT DISTINCT
    first_name
FROM smart_health.patients 
WHERE first_name LIKE 'A%'
LIMIT 5;

SELECT DISTINCT
    first_name
FROM smart_health.patients
WHERE first_name LIKE 'Andr__'
LIMIT 5;

SELECT DISTINCT
    first_name
FROM smart_health.patients
WHERE first_name LIKE 'S%a'
LIMIT 5;



-- El nombre completo más largo de los pacientes
-- Desempate por primer_nombre

SELECT
    sq.nombre_completo,
    sq.longitud,
    sq.first_name
FROM (
    SELECT
        first_name||' '||COALESCE(middle_name, '')||' '||
        first_surname||' '||COALESCE(second_surname, '') AS nombre_completo,
        LENGTH(
            first_name||' '||COALESCE(middle_name, '')||' '||
            first_surname||' '||COALESCE(second_surname, '')
        ) AS longitud,
        first_name
    FROM smart_health.patients
) sq
ORDER BY sq.longitud DESC, sq.first_name ASC
LIMIT 1;

-- El nombre completo más corto de los pacientes
-- Desempate por primer apellido

SELECT
    sq.nombre_completo,
    sq.longitud,
    sq.first_surname
FROM (
    SELECT
        first_name||' '||COALESCE(middle_name, '')||' '||
        first_surname||' '||COALESCE(second_surname, '') AS nombre_completo,
        LENGTH(
            first_name||' '||COALESCE(middle_name, '')||' '||
            first_surname||' '||COALESCE(second_surname, '')
        ) AS longitud,
        first_surname
    FROM smart_health.patients
) sq
ORDER BY sq.longitud ASC, sq.first_surname ASC
LIMIT 1;
