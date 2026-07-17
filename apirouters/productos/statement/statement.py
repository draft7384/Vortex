"""
SQL del modulo Productos.
"""

INSERT_PRODUCTO = """
INSERT INTO productos (
    codigo, descripcion, unidad_medida, precio_base, impuesto_pct,
    existencia, es_servicio, activo,
    shopify_id, shopify_handle, shopify_status,
    shopify_product_type, shopify_tags, shopify_image_url
) VALUES (
    :codigo, :descripcion, :unidad_medida, :precio_base, :impuesto_pct,
    :existencia, :es_servicio, :activo,
    :shopify_id, :shopify_handle, :shopify_status,
    :shopify_product_type, :shopify_tags, :shopify_image_url
)
RETURNING id, codigo, descripcion, unidad_medida, precio_base, impuesto_pct,
          existencia, es_servicio, activo,
          shopify_id, shopify_handle, shopify_status,
          shopify_product_type, shopify_tags, shopify_image_url, actualizado_en;
"""

SELECT_PRODUCTO_BY_ID = """
SELECT id, codigo, descripcion, unidad_medida, precio_base, impuesto_pct,
       existencia, es_servicio, activo,
       shopify_id, shopify_handle, shopify_status,
       shopify_product_type, shopify_tags, shopify_image_url, actualizado_en
FROM productos
WHERE id = :producto_id;
"""

SELECT_PRODUCTO_BY_CODIGO = """
SELECT id, codigo, descripcion, precio_base, impuesto_pct, existencia, es_servicio, activo
FROM productos
WHERE codigo = :codigo;
"""

SELECT_PRODUCTOS_PAGINATED = """
SELECT id, codigo, descripcion, precio_base, impuesto_pct, existencia, es_servicio, activo
FROM productos
WHERE activo = TRUE
ORDER BY descripcion ASC
LIMIT :limit OFFSET :offset;
"""

SELECT_PRODUCTOS_COUNT = """
SELECT COUNT(*) AS total FROM productos WHERE activo = TRUE;
"""

SEARCH_PRODUCTOS_BY_KEYWORD = """
SELECT id, codigo, descripcion, precio_base, impuesto_pct, existencia, es_servicio, activo
FROM productos
WHERE activo = TRUE
  AND (
    LOWER(codigo) LIKE LOWER(:keyword)
    OR LOWER(descripcion) LIKE LOWER(:keyword)
  )
ORDER BY descripcion ASC
LIMIT 50;
"""

SELECT_PRODUCTOS_BAJO_STOCK = """
SELECT id, codigo, descripcion, existencia, es_servicio, precio_base
FROM productos
WHERE activo = TRUE
  AND es_servicio = FALSE
  AND existencia <= :umbral
ORDER BY existencia ASC;
"""

UPDATE_PRODUCTO = """
UPDATE productos SET
    codigo              = COALESCE(:codigo, codigo),
    descripcion         = COALESCE(:descripcion, descripcion),
    unidad_medida       = COALESCE(:unidad_medida, unidad_medida),
    precio_base         = COALESCE(:precio_base, precio_base),
    impuesto_pct        = COALESCE(:impuesto_pct, impuesto_pct),
    existencia          = COALESCE(:existencia, existencia),
    es_servicio         = COALESCE(:es_servicio, es_servicio),
    activo              = COALESCE(:activo, activo),
    shopify_id          = COALESCE(:shopify_id, shopify_id),
    shopify_handle      = COALESCE(:shopify_handle, shopify_handle),
    shopify_status      = COALESCE(:shopify_status, shopify_status),
    shopify_product_type = COALESCE(:shopify_product_type, shopify_product_type),
    shopify_tags        = COALESCE(:shopify_tags, shopify_tags),
    shopify_image_url   = COALESCE(:shopify_image_url, shopify_image_url),
    actualizado_en      = CURRENT_TIMESTAMP
WHERE id = :producto_id
RETURNING id, codigo, descripcion, precio_base, impuesto_pct, existencia,
          es_servicio, activo, shopify_id, shopify_handle, shopify_status,
          shopify_product_type, shopify_tags, shopify_image_url, actualizado_en;
"""

# Para facturacion: descuento de existencia con control de stock
UPDATE_DESCONTAR_EXISTENCIA = """
UPDATE productos
SET existencia = existencia - :cantidad, actualizado_en = CURRENT_TIMESTAMP
WHERE id = :producto_id AND es_servicio = FALSE AND existencia >= :cantidad
RETURNING id, codigo, existencia;
"""

# Para anulacion: devuelve existencia
UPDATE_DEVOLVER_EXISTENCIA = """
UPDATE productos
SET existencia = existencia + :cantidad, actualizado_en = CURRENT_TIMESTAMP
WHERE id = :producto_id
RETURNING id, codigo, existencia;
"""

DELETE_PRODUCTO = """
UPDATE productos SET activo = FALSE WHERE id = :producto_id
RETURNING id, codigo;
"""
