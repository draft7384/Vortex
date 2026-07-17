"""
SQL crudo del modulo Documentos de Venta.
Cada constante es un query nombrado semanticamente, ejecutado con `text(...)` desde use_case.
"""

# ============================================================
# VALIDACIONES Y REGLAS DE NEGOCIO
# ============================================================

SELECT_PARAMETRO_BLOQUEO_CREDITO = """
SELECT valor
FROM parametros_sistema
WHERE clave = 'cxc_bloquear_limite_credito';
"""

SELECT_DOCUMENTO_REFERENCIA_VALIDO = """
SELECT id, tipo, estado, cliente_id, total_neto
FROM documentos_ventas
WHERE id = :documento_referencia_id;
"""

SELECT_MOVIMIENTO_CXC_BY_DOCUMENTO = """
SELECT id, tipo_movimiento, estado, saldo_original, saldo_local, tasa_cambio
FROM movimientos_cxc
WHERE documento_venta_id = :documento_venta_id;
"""

SELECT_DOCUMENTO_TIENE_APLICACIONES = """
SELECT COUNT(*) AS total
FROM aplicaciones_cxc a
INNER JOIN movimientos_cxc m ON m.id = a.movimiento_deuda_id
WHERE m.documento_venta_id = :documento_venta_id;
"""


# ============================================================
# INSERTS
# ============================================================

INSERT_DOCUMENTO_VENTA = """
INSERT INTO documentos_ventas (
    codigo, numero_control, tipo, cliente_id, vendedor_id, punto_emision_id,
    documento_referencia_id, motivo, fecha_emision, fecha_vencimiento,
    moneda_id, tasa_cambio, subtotal, total_impuestos, total_descuentos,
    total_neto, total_neto_local, estado, observaciones, creado_por
) VALUES (
    :codigo, :numero_control, CAST(:tipo AS tipo_documento_venta), :cliente_id,
    :vendedor_id, :punto_emision_id, :documento_referencia_id, :motivo,
    :fecha_emision, :fecha_vencimiento, :moneda_id, :tasa_cambio,
    :subtotal, :total_impuestos, :total_descuentos, :total_neto,
    :total_neto_local, CAST(:estado AS estado_documento), :observaciones, :creado_por
)
RETURNING id, codigo, numero_control, tipo, fecha_emision, fecha_vencimiento,
          cliente_id, estado, creado_en;
"""

INSERT_DOCUMENTO_DETALLE = """
INSERT INTO documentos_ventas_detalle (
    documento_id, producto_id, nro_renglon, descripcion,
    cantidad, precio_unitario, descuento_pct, impuesto_pct, total_renglon
) VALUES (
    :documento_id, :producto_id, :nro_renglon, :descripcion,
    :cantidad, :precio_unitario, :descuento_pct, :impuesto_pct, :total_renglon
)
RETURNING id, nro_renglon, total_renglon;
"""

INSERT_MOVIMIENTO_CXC_FACTURA = """
INSERT INTO movimientos_cxc (
    cliente_id, tipo_movimiento, documento_venta_id, numero_documento,
    fecha_movimiento, fecha_vencimiento, moneda_id, tasa_cambio,
    monto_original, saldo_original, monto_local, saldo_local, estado, registrado_por
) VALUES (
    :cliente_id, CAST(:tipo_movimiento AS tipo_movimiento_cxc), :documento_venta_id,
    :numero_documento, :fecha_movimiento, :fecha_vencimiento, :moneda_id,
    :tasa_cambio, :monto_original, :saldo_original, :monto_local, :saldo_local,
    CAST(:estado AS estado_documento), :registrado_por
)
RETURNING id, tipo_movimiento, monto_original, saldo_original;
"""

INSERT_OVERRIDE_CREDITO_LOG = """
INSERT INTO override_credito_log (
    cliente_id, documento_venta_id, usuario_id, limite_vigente,
    saldo_antes_emision, monto_nueva_factura, monto_excedente, motivo
) VALUES (
    :cliente_id, :documento_venta_id, :usuario_id, :limite_vigente,
    :saldo_antes_emision, :monto_nueva_factura, :monto_excedente, :motivo
)
RETURNING id, fecha;
"""


# ============================================================
# UPDATES (anulacion)
# ============================================================

UPDATE_ANULAR_DOCUMENTO = """
UPDATE documentos_ventas SET
    estado = CAST('ANULADO' AS estado_documento),
    anulado_por = :anulado_por,
    anulado_en = CURRENT_TIMESTAMP,
    motivo = :motivo,
    actualizado_en = CURRENT_TIMESTAMP
WHERE id = :documento_id
RETURNING id, codigo, estado, anulado_por, anulado_en, motivo;
"""

UPDATE_MOVIMIENTO_CXC_ANULAR = """
UPDATE movimientos_cxc SET
    estado = CAST('ANULADO' AS estado_documento),
    actualizado_en = CURRENT_TIMESTAMP
WHERE documento_venta_id = :documento_venta_id
RETURNING id, estado;
"""

# Resta el saldo de un movimiento (sin condicion WHERE saldo >= ...), usado para
# rebajar el saldo_original de la NC cuando una parte se aplicó contra la factura
# y el resto queda como saldo a favor.
UPDATE_MOVIMIENTO_SALDO_RESTAR = """
UPDATE movimientos_cxc
SET saldo_original = ROUND(saldo_original - CAST(:monto AS NUMERIC), 2),
    saldo_local = ROUND(saldo_local - CAST(:monto_local AS NUMERIC), 2),
    estado = CASE WHEN ROUND(saldo_original - CAST(:monto AS NUMERIC), 2) <= 0.005
                  THEN CAST('PAGADO' AS estado_documento)
                  ELSE estado END,
    actualizado_en = CURRENT_TIMESTAMP
WHERE id = :movimiento_id
RETURNING id, saldo_original, saldo_local, estado;
"""

# INSERT de una aplicacion entre movimientos (NC -> factura)
INSERT_APLICACION_CXC = """
INSERT INTO aplicaciones_cxc (
    movimiento_pago_id, movimiento_deuda_id,
    monto_aplicado_original, monto_aplicado_local, aplicado_por
) VALUES (
    :movimiento_pago_id, :movimiento_deuda_id,
    :monto_aplicado_original, :monto_aplicado_local, :aplicado_por
)
RETURNING id, movimiento_pago_id, movimiento_deuda_id,
          monto_aplicado_original, monto_aplicado_local, fecha_aplicacion;
"""


# ============================================================
# SELECTS (lectura y listado)
# ============================================================

SELECT_DOCUMENTO_BY_ID = """
SELECT id, codigo, numero_control, tipo, cliente_id, vendedor_id, punto_emision_id,
       documento_referencia_id, motivo, fecha_emision, fecha_vencimiento,
       moneda_id, tasa_cambio, subtotal, total_impuestos, total_descuentos,
       total_neto, total_neto_local, estado, observaciones,
       creado_por, creado_en, actualizado_en, anulado_por, anulado_en
FROM documentos_ventas
WHERE id = :documento_id;
"""

SELECT_DETALLES_BY_DOCUMENTO = """
SELECT id, documento_id, producto_id, nro_renglon, descripcion, cantidad,
       precio_unitario, descuento_pct, impuesto_pct, total_renglon
FROM documentos_ventas_detalle
WHERE documento_id = :documento_id
ORDER BY nro_renglon ASC;
"""

SELECT_DOCUMENTOS_PAGINATED = """
SELECT d.id, d.codigo, d.numero_control, d.tipo, d.fecha_emision, d.fecha_vencimiento,
       d.cliente_id, c.nombre_razon_social AS cliente_nombre,
       d.total_neto, d.total_neto_local, d.estado
FROM documentos_ventas d
LEFT JOIN clientes c ON c.id = d.cliente_id
WHERE (CAST(:cliente_id AS BIGINT) IS NULL OR d.cliente_id = CAST(:cliente_id AS BIGINT))
  AND (CAST(:tipo AS TEXT) IS NULL OR d.tipo::TEXT = CAST(:tipo AS TEXT))
  AND (CAST(:estado AS TEXT) IS NULL OR d.estado::TEXT = CAST(:estado AS TEXT))
  AND (CAST(:fecha_desde AS DATE) IS NULL OR d.fecha_emision >= CAST(:fecha_desde AS DATE))
  AND (CAST(:fecha_hasta AS DATE) IS NULL OR d.fecha_emision <= CAST(:fecha_hasta AS DATE))
ORDER BY d.fecha_emision DESC, d.id DESC
LIMIT :limit OFFSET :offset;
"""

SELECT_DOCUMENTOS_COUNT = """
SELECT COUNT(*) AS total
FROM documentos_ventas
WHERE (CAST(:cliente_id AS BIGINT) IS NULL OR cliente_id = CAST(:cliente_id AS BIGINT))
  AND (CAST(:tipo AS TEXT) IS NULL OR tipo::TEXT = CAST(:tipo AS TEXT))
  AND (CAST(:estado AS TEXT) IS NULL OR estado::TEXT = CAST(:estado AS TEXT))
  AND (CAST(:fecha_desde AS DATE) IS NULL OR fecha_emision >= CAST(:fecha_desde AS DATE))
  AND (CAST(:fecha_hasta AS DATE) IS NULL OR fecha_emision <= CAST(:fecha_hasta AS DATE));
"""
