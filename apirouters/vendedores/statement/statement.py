"""
SQL del modulo Vendedores.
"""

INSERT_VENDEDOR = """
INSERT INTO vendedores (codigo, usuario_id, nombre, comision_pct, activo)
VALUES (:codigo, :usuario_id, :nombre, :comision_pct, :activo)
RETURNING id, codigo, usuario_id, nombre, comision_pct, activo;
"""

SELECT_VENDEDOR_BY_ID = """
SELECT id, codigo, usuario_id, nombre, comision_pct, activo
FROM vendedores
WHERE id = :vendedor_id;
"""

SELECT_VENDEDOR_BY_CODIGO = """
SELECT id, codigo, usuario_id, nombre, comision_pct, activo
FROM vendedores
WHERE codigo = :codigo;
"""

SELECT_VENDEDORES_PAGINATED = """
SELECT id, codigo, nombre, comision_pct, activo
FROM vendedores
WHERE activo = TRUE
ORDER BY nombre ASC
LIMIT :limit OFFSET :offset;
"""

SELECT_VENDEDORES_COUNT = """
SELECT COUNT(*) AS total FROM vendedores WHERE activo = TRUE;
"""

SEARCH_VENDEDORES_BY_KEYWORD = """
SELECT id, codigo, nombre, comision_pct, activo
FROM vendedores
WHERE activo = TRUE
  AND (
    LOWER(codigo) LIKE LOWER(:keyword)
    OR LOWER(nombre) LIKE LOWER(:keyword)
  )
ORDER BY nombre ASC
LIMIT 50;
"""

UPDATE_VENDEDOR = """
UPDATE vendedores SET
    codigo        = COALESCE(:codigo, codigo),
    usuario_id    = COALESCE(:usuario_id, usuario_id),
    nombre        = COALESCE(:nombre, nombre),
    comision_pct  = COALESCE(:comision_pct, comision_pct),
    activo        = COALESCE(:activo, activo)
WHERE id = :vendedor_id
RETURNING id, codigo, usuario_id, nombre, comision_pct, activo;
"""

DELETE_VENDEDOR = """
UPDATE vendedores SET activo = FALSE WHERE id = :vendedor_id
RETURNING id, codigo;
"""
