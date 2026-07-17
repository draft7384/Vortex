"""
SQL del modulo Puntos de Emision.
"""

INSERT_PUNTO_EMISION = """
INSERT INTO puntos_emision (codigo, nombre, tipo, direccion, telefono, activo)
VALUES (:codigo, :nombre, CAST(:tipo AS tipo_punto_emision), :direccion, :telefono, :activo)
RETURNING id, codigo, nombre, tipo, direccion, telefono, activo, creado_en;
"""

SELECT_PUNTO_EMISION_BY_ID = """
SELECT id, codigo, nombre, tipo, direccion, telefono, activo, creado_en
FROM puntos_emision
WHERE id = :punto_id;
"""

SELECT_PUNTO_EMISION_BY_CODIGO = """
SELECT id, codigo, nombre, tipo, direccion, telefono, activo, creado_en
FROM puntos_emision
WHERE codigo = :codigo;
"""

SELECT_PUNTOS_EMISION_PAGINATED = """
SELECT id, codigo, nombre, tipo, direccion, telefono, activo, creado_en
FROM puntos_emision
WHERE activo = TRUE
ORDER BY codigo ASC
LIMIT :limit OFFSET :offset;
"""

SELECT_PUNTOS_EMISION_COUNT = """
SELECT COUNT(*) AS total FROM puntos_emision WHERE activo = TRUE;
"""

SEARCH_PUNTOS_EMISION_BY_KEYWORD = """
SELECT id, codigo, nombre, tipo, direccion, telefono, activo
FROM puntos_emision
WHERE activo = TRUE
  AND (
    LOWER(codigo) LIKE LOWER(:keyword)
    OR LOWER(nombre) LIKE LOWER(:keyword)
  )
ORDER BY codigo ASC
LIMIT 50;
"""

UPDATE_PUNTO_EMISION = """
UPDATE puntos_emision SET
    codigo    = COALESCE(:codigo, codigo),
    nombre    = COALESCE(:nombre, nombre),
    tipo      = COALESCE(CAST(:tipo AS tipo_punto_emision), tipo),
    direccion = COALESCE(:direccion, direccion),
    telefono  = COALESCE(:telefono, telefono),
    activo    = COALESCE(:activo, activo)
WHERE id = :punto_id
RETURNING id, codigo, nombre, tipo, direccion, telefono, activo, creado_en;
"""

DELETE_PUNTO_EMISION = """
UPDATE puntos_emision SET activo = FALSE WHERE id = :punto_id
RETURNING id, codigo;
"""
