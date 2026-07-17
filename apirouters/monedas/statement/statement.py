"""
SQL del modulo Monedas.
"""

INSERT_MONEDA = """
INSERT INTO monedas (codigo_iso, nombre, simbolo, decimales, es_moneda_local, activo)
VALUES (:codigo_iso, :nombre, :simbolo, :decimales, :es_moneda_local, :activo)
RETURNING id, codigo_iso, nombre, simbolo, decimales, es_moneda_local, activo;
"""

SELECT_MONEDA_BY_ID = """
SELECT id, codigo_iso, nombre, simbolo, decimales, es_moneda_local, activo
FROM monedas
WHERE id = :moneda_id;
"""

SELECT_MONEDA_BY_ISO = """
SELECT id, codigo_iso, nombre, simbolo, decimales, es_moneda_local, activo
FROM monedas
WHERE codigo_iso = :codigo_iso;
"""

SELECT_MONEDAS_PAGINATED = """
SELECT id, codigo_iso, nombre, simbolo, decimales, es_moneda_local, activo
FROM monedas
WHERE activo = TRUE
ORDER BY codigo_iso ASC
LIMIT :limit OFFSET :offset;
"""

SELECT_MONEDAS_COUNT = """
SELECT COUNT(*) AS total FROM monedas WHERE activo = TRUE;
"""

SELECT_MONEDA_LOCAL = """
SELECT id, codigo_iso, nombre, simbolo, decimales, es_moneda_local, activo
FROM monedas
WHERE es_moneda_local = TRUE AND activo = TRUE
LIMIT 1;
"""

SEARCH_MONEDAS_BY_KEYWORD = """
SELECT id, codigo_iso, nombre, simbolo, decimales, es_moneda_local, activo
FROM monedas
WHERE activo = TRUE
  AND (
    LOWER(codigo_iso) LIKE LOWER(:keyword)
    OR LOWER(nombre) LIKE LOWER(:keyword)
  )
ORDER BY codigo_iso ASC
LIMIT 50;
"""

UPDATE_MONEDA = """
UPDATE monedas SET
    codigo_iso        = COALESCE(:codigo_iso, codigo_iso),
    nombre            = COALESCE(:nombre, nombre),
    simbolo           = COALESCE(:simbolo, simbolo),
    decimales         = COALESCE(:decimales, decimales),
    es_moneda_local   = COALESCE(:es_moneda_local, es_moneda_local),
    activo            = COALESCE(:activo, activo)
WHERE id = :moneda_id
RETURNING id, codigo_iso, nombre, simbolo, decimales, es_moneda_local, activo;
"""

DELETE_MONEDA = """
UPDATE monedas SET activo = FALSE WHERE id = :moneda_id
RETURNING id, codigo_iso;
"""
