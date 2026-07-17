"""
SQL del modulo Parametros del Sistema.
Los valores se serializan a JSON via :valor::jsonb.
"""

INSERT_PARAMETRO = """
INSERT INTO parametros_sistema (clave, valor, descripcion)
VALUES (:clave, CAST(:valor AS jsonb), :descripcion)
RETURNING clave, valor, descripcion, actualizado_en;
"""

SELECT_PARAMETRO_BY_CLAVE = """
SELECT clave, valor, descripcion, actualizado_en
FROM parametros_sistema
WHERE clave = :clave;
"""

SELECT_PARAMETROS_PAGINATED = """
SELECT clave, valor, descripcion, actualizado_en
FROM parametros_sistema
ORDER BY clave ASC
LIMIT :limit OFFSET :offset;
"""

SELECT_PARAMETROS_COUNT = """
SELECT COUNT(*) AS total FROM parametros_sistema;
"""

SEARCH_PARAMETROS_BY_KEYWORD = """
SELECT clave, valor, descripcion, actualizado_en
FROM parametros_sistema
WHERE LOWER(clave) LIKE LOWER(:keyword)
   OR LOWER(COALESCE(descripcion, '')) LIKE LOWER(:keyword)
ORDER BY clave ASC
LIMIT 50;
"""

UPDATE_PARAMETRO = """
UPDATE parametros_sistema SET
    valor         = CAST(:valor AS jsonb),
    descripcion   = COALESCE(:descripcion, descripcion),
    actualizado_en = CURRENT_TIMESTAMP
WHERE clave = :clave
RETURNING clave, valor, descripcion, actualizado_en;
"""

DELETE_PARAMETRO = """
DELETE FROM parametros_sistema WHERE clave = :clave
RETURNING clave;
"""
