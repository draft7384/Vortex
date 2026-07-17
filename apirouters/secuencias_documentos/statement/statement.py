"""
SQL del modulo Secuencias de Documentos.
NOTA: para facturacion, el incremento del correlativo se hace con FOR UPDATE
para evitar condiciones de carrera. Aqui se exponen queries CRUD basicas.
"""

INSERT_SECUENCIA = """
INSERT INTO secuencias_documentos (
    punto_emision_id, tipo_documento, prefijo, proximo_numero, numero_actual, activo
) VALUES (
    :punto_emision_id, CAST(:tipo_documento AS tipo_documento_venta), :prefijo, :proximo_numero, :numero_actual, :activo
)
RETURNING id, punto_emision_id, tipo_documento, prefijo, proximo_numero, numero_actual, activo;
"""

SELECT_SECUENCIA_BY_ID = """
SELECT id, punto_emision_id, tipo_documento, prefijo, proximo_numero, numero_actual, activo
FROM secuencias_documentos
WHERE id = :secuencia_id;
"""

SELECT_SECUENCIA_BY_PUNTO_TIPO = """
SELECT id, punto_emision_id, tipo_documento, prefijo, proximo_numero, numero_actual, activo
FROM secuencias_documentos
WHERE punto_emision_id = :punto_emision_id AND tipo_documento = CAST(:tipo_documento AS tipo_documento_venta);
"""

SELECT_SECUENCIAS_PAGINATED = """
SELECT s.id, s.punto_emision_id, s.tipo_documento, s.prefijo, s.proximo_numero, s.numero_actual, s.activo,
       p.codigo AS punto_codigo, p.nombre AS punto_nombre
FROM secuencias_documentos s
INNER JOIN puntos_emision p ON p.id = s.punto_emision_id
ORDER BY p.codigo ASC, s.tipo_documento ASC
LIMIT :limit OFFSET :offset;
"""

SELECT_SECUENCIAS_COUNT = """
SELECT COUNT(*) AS total FROM secuencias_documentos WHERE activo = TRUE;
"""

SELECT_SECUENCIAS_BY_PUNTO = """
SELECT id, punto_emision_id, tipo_documento, prefijo, proximo_numero, numero_actual, activo
FROM secuencias_documentos
WHERE punto_emision_id = :punto_emision_id
ORDER BY tipo_documento ASC;
"""

UPDATE_SECUENCIA = """
UPDATE secuencias_documentos SET
    prefijo        = COALESCE(:prefijo, prefijo),
    proximo_numero = COALESCE(:proximo_numero, proximo_numero),
    numero_actual  = COALESCE(:numero_actual, numero_actual),
    activo         = COALESCE(:activo, activo)
WHERE id = :secuencia_id
RETURNING id, punto_emision_id, tipo_documento, prefijo, proximo_numero, numero_actual, activo;
"""

DELETE_SECUENCIA = """
UPDATE secuencias_documentos SET activo = FALSE WHERE id = :secuencia_id
RETURNING id, tipo_documento;
"""

# Para uso interno del modulo de facturacion
INCREMENTAR_SECUENCIA = """
SELECT id, punto_emision_id, tipo_documento, prefijo, proximo_numero, numero_actual
FROM secuencias_documentos
WHERE punto_emision_id = :punto_emision_id
  AND tipo_documento = CAST(:tipo_documento AS tipo_documento_venta)
  AND activo = TRUE
FOR UPDATE;
"""

UPDATE_INCREMENTAR_SECUENCIA = """
UPDATE secuencias_documentos SET
    numero_actual = numero_actual + 1,
    proximo_numero = numero_actual + 2
WHERE id = :secuencia_id
RETURNING numero_actual, prefijo;
"""
