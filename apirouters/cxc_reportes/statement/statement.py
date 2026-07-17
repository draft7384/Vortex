"""
SQL crudo del modulo Reportes CxC.
"""


# ============================================================
# LISTADO DE MOVIMIENTOS
# ============================================================

SELECT_MOVIMIENTOS_PAGINATED = """
SELECT id, cliente_id, tipo_movimiento, documento_venta_id, numero_documento,
       fecha_movimiento, fecha_vencimiento, moneda_id, tasa_cambio,
       monto_original, saldo_original, monto_local, saldo_local, estado
FROM movimientos_cxc
WHERE (CAST(:cliente_id AS BIGINT) IS NULL OR cliente_id = CAST(:cliente_id AS BIGINT))
  AND (CAST(:tipo AS TEXT) IS NULL OR tipo_movimiento::TEXT = CAST(:tipo AS TEXT))
  AND (CAST(:estado AS TEXT) IS NULL OR estado::TEXT = CAST(:estado AS TEXT))
  AND (CAST(:fecha_desde AS DATE) IS NULL OR fecha_movimiento >= CAST(:fecha_desde AS DATE))
  AND (CAST(:fecha_hasta AS DATE) IS NULL OR fecha_movimiento <= CAST(:fecha_hasta AS DATE))
  AND (CAST(:solo_pendientes AS BOOLEAN) IS NULL
       OR (CAST(:solo_pendientes AS BOOLEAN) = FALSE)
       OR (tipo_movimiento IN (CAST('FACTURA' AS tipo_movimiento_cxc),
                                CAST('NOTA_DEBITO' AS tipo_movimiento_cxc))
           AND saldo_original > 0))
ORDER BY fecha_movimiento DESC, id DESC
LIMIT :limit OFFSET :offset;
"""

SELECT_MOVIMIENTOS_COUNT = """
SELECT COUNT(*) AS total
FROM movimientos_cxc
WHERE (CAST(:cliente_id AS BIGINT) IS NULL OR cliente_id = CAST(:cliente_id AS BIGINT))
  AND (CAST(:tipo AS TEXT) IS NULL OR tipo_movimiento::TEXT = CAST(:tipo AS TEXT))
  AND (CAST(:estado AS TEXT) IS NULL OR estado::TEXT = CAST(:estado AS TEXT))
  AND (CAST(:fecha_desde AS DATE) IS NULL OR fecha_movimiento >= CAST(:fecha_desde AS DATE))
  AND (CAST(:fecha_hasta AS DATE) IS NULL OR fecha_movimiento <= CAST(:fecha_hasta AS DATE))
  AND (CAST(:solo_pendientes AS BOOLEAN) IS NULL
       OR (CAST(:solo_pendientes AS BOOLEAN) = FALSE)
       OR (tipo_movimiento IN (CAST('FACTURA' AS tipo_movimiento_cxc),
                                CAST('NOTA_DEBITO' AS tipo_movimiento_cxc))
           AND saldo_original > 0));
"""

SELECT_MOVIMIENTO_BY_ID = """
SELECT id, cliente_id, tipo_movimiento, documento_venta_id, numero_documento,
       fecha_movimiento, fecha_vencimiento, moneda_id, tasa_cambio,
       monto_original, saldo_original, monto_local, saldo_local, estado
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
# ESTADO DE CUENTA POR CLIENTE
# ============================================================

SELECT_ESTADO_CUENTA = """
SELECT m.id, m.cliente_id, m.tipo_movimiento, m.documento_venta_id, m.numero_documento,
       m.fecha_movimiento, m.fecha_vencimiento, m.moneda_id, m.tasa_cambio,
       m.monto_original, m.saldo_original, m.monto_local, m.saldo_local, m.estado
FROM movimientos_cxc m
WHERE m.cliente_id = :cliente_id
  AND m.estado = CAST('EMITIDO' AS estado_documento)
ORDER BY m.fecha_movimiento ASC, m.id ASC;
"""


# ============================================================
# ANTIGUEDAD DE SALDOS
# ============================================================

SELECT_ANTIGUEDAD_SALDOS = """
SELECT id, fecha_vencimiento, saldo_original, saldo_local, tasa_cambio,
       (CURRENT_DATE - fecha_vencimiento) AS dias_vencidos
FROM movimientos_cxc
WHERE (CAST(:cliente_id AS BIGINT) IS NULL OR cliente_id = CAST(:cliente_id AS BIGINT))
  AND estado = CAST('EMITIDO' AS estado_documento)
  AND saldo_original > 0
  AND fecha_vencimiento IS NOT NULL
ORDER BY dias_vencidos DESC;
"""

SELECT_RANGOS_ANTIGUEDAD = """
SELECT valor
FROM parametros_sistema
WHERE clave = 'cxc_rangos_antiguedad';
"""
