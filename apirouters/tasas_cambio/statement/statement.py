"""
SQL del modulo Tasas de Cambio.
"""

INSERT_TASA = """
INSERT INTO tasas_cambio (moneda_id, fecha, tasa)
VALUES (:moneda_id, :fecha, :tasa)
RETURNING id, moneda_id, fecha, tasa;
"""

SELECT_TASA_BY_ID = """
SELECT id, moneda_id, fecha, tasa
FROM tasas_cambio
WHERE id = :tasa_id;
"""

SELECT_TASA_BY_MONEDA_FECHA = """
SELECT id, moneda_id, fecha, tasa
FROM tasas_cambio
WHERE moneda_id = :moneda_id AND fecha = :fecha;
"""

SELECT_TASA_BY_MONEDA = """
SELECT id, moneda_id, fecha, tasa
FROM tasas_cambio
WHERE moneda_id = :moneda_id
ORDER BY fecha DESC
LIMIT 1;
"""

SELECT_TASAS_PAGINATED = """
SELECT t.id, t.moneda_id, t.fecha, t.tasa, m.codigo_iso, m.nombre AS nombre_moneda
FROM tasas_cambio t
INNER JOIN monedas m ON m.id = t.moneda_id
ORDER BY t.fecha DESC, m.codigo_iso ASC
LIMIT :limit OFFSET :offset;
"""

SELECT_TASAS_COUNT = """
SELECT COUNT(*) AS total FROM tasas_cambio;
"""

UPDATE_TASA = """
UPDATE tasas_cambio SET tasa = :tasa
WHERE id = :tasa_id
RETURNING id, moneda_id, fecha, tasa;
"""

DELETE_TASA = """
DELETE FROM tasas_cambio WHERE id = :tasa_id
RETURNING id, moneda_id, fecha;
"""
