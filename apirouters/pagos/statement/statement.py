"""
SQL crudo del modulo Pagos / CxC.
Cada constante es un query nombrado semanticamente, ejecutado con `text(...)` desde use_case.
"""

# ============================================================
# VALIDACIONES Y LOOKUPS
# ============================================================

SELECT_MONEDA_BY_ID = """
SELECT id, codigo_iso, nombre, simbolo, decimales, es_moneda_local, activo
FROM monedas
WHERE id = :moneda_id;
"""

SELECT_TASA_BY_MONEDA_FECHA = """
SELECT tasa
FROM tasas_cambio
WHERE moneda_id = :moneda_id AND fecha = CAST(:fecha AS DATE);
"""

SELECT_DEUDAS_PENDIENTES_FIFO = """
SELECT id, tipo_movimiento, documento_venta_id, numero_documento,
       fecha_vencimiento, monto_original, saldo_original, tasa_cambio
FROM movimientos_cxc
WHERE cliente_id = :cliente_id
  AND saldo_original > 0
  AND estado = CAST('EMITIDO' AS estado_documento)
  AND tipo_movimiento IN (CAST('FACTURA' AS tipo_movimiento_cxc),
                          CAST('NOTA_DEBITO' AS tipo_movimiento_cxc))
ORDER BY fecha_vencimiento ASC NULLS LAST, id ASC;
"""

SELECT_MOVIMIENTO_BY_ID = """
SELECT id, cliente_id, tipo_movimiento, estado, saldo_original, saldo_local,
       monto_original, tasa_cambio, numero_documento, fecha_vencimiento
FROM movimientos_cxc
WHERE id = :movimiento_id;
"""

SELECT_APLICACIONES_BY_MOVIMIENTO = """
SELECT id, movimiento_pago_id, movimiento_deuda_id, monto_aplicado_original,
       monto_aplicado_local, fecha_aplicacion, aplicado_por,
       reversada, reversada_por, reversada_en, motivo_reverso
FROM aplicaciones_cxc
WHERE movimiento_pago_id = :movimiento_id OR movimiento_deuda_id = :movimiento_id
ORDER BY fecha_aplicacion ASC, id ASC;
"""


# ============================================================
# INSERTS
# ============================================================

INSERT_MOVIMIENTO_CXC_PAGO = """
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
RETURNING id, cliente_id, tipo_movimiento, documento_venta_id, numero_documento,
          fecha_movimiento, fecha_vencimiento, moneda_id, tasa_cambio,
          monto_original, saldo_original, monto_local, saldo_local, estado;
"""

INSERT_APLICACION_CXC = """
INSERT INTO aplicaciones_cxc (
    movimiento_pago_id, movimiento_deuda_id,
    monto_aplicado_original, monto_aplicado_local, aplicado_por
) VALUES (
    :movimiento_pago_id, :movimiento_deuda_id,
    :monto_aplicado_original, :monto_aplicado_local, :aplicado_por
)
RETURNING id, movimiento_pago_id, movimiento_deuda_id,
          monto_aplicado_original, monto_aplicado_local,
          fecha_aplicacion, aplicado_por;
"""


# ============================================================
# UPDATES
# ============================================================

UPDATE_MOVIMIENTO_SALDO_RESTAR = """
UPDATE movimientos_cxc
SET saldo_original = ROUND(saldo_original - CAST(:monto_aplicado AS NUMERIC), 2),
    saldo_local = ROUND(saldo_local - CAST(:monto_aplicado_local AS NUMERIC), 2),
    estado = CASE WHEN ROUND(saldo_original - CAST(:monto_aplicado AS NUMERIC), 2) <= 0.005
                  THEN CAST('PAGADO' AS estado_documento)
                  ELSE estado END,
    actualizado_en = CURRENT_TIMESTAMP
WHERE id = :movimiento_id
  AND saldo_original >= CAST(:monto_aplicado AS NUMERIC)
RETURNING id, saldo_original, saldo_local, estado;
"""
