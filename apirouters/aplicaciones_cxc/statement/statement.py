"""
SQL crudo del modulo Aplicaciones CxC.
"""

# ============================================================
# READ
# ============================================================

SELECT_APLICACION_BY_ID = """
SELECT id, movimiento_pago_id, movimiento_deuda_id, monto_aplicado_original, monto_aplicado_local,
       fecha_aplicacion, aplicado_por, reversada, reversada_por, reversada_en, motivo_reverso
FROM aplicaciones_cxc
WHERE id = :aplicacion_id;
"""

SELECT_MOVIMIENTO_BY_ID = """
SELECT id, cliente_id, tipo_movimiento, estado, saldo_original, saldo_local,
       monto_original, tasa_cambio, numero_documento
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

UPDATE_APLICACION_REVERSAR = """
UPDATE aplicaciones_cxc
SET reversada = TRUE,
    reversada_por = :usuario_id,
    reversada_en = CURRENT_TIMESTAMP,
    motivo_reverso = :motivo
WHERE id = :aplicacion_id AND reversada = FALSE
RETURNING id, movimiento_pago_id, movimiento_deuda_id,
          monto_aplicado_original, monto_aplicado_local,
          fecha_aplicacion, aplicado_por, reversada, reversada_por, reversada_en, motivo_reverso;
"""

UPDATE_MOVIMIENTO_SALDO_SUMAR = """
UPDATE movimientos_cxc
SET saldo_original = ROUND(saldo_original + CAST(:monto_aplicado AS NUMERIC), 2),
    saldo_local = ROUND(saldo_local + CAST(:monto_aplicado_local AS NUMERIC), 2),
    estado = CASE WHEN ROUND(saldo_original + CAST(:monto_aplicado AS NUMERIC), 2) > 0.005
                  THEN CAST('EMITIDO' AS estado_documento)
                  ELSE estado END,
    actualizado_en = CURRENT_TIMESTAMP
WHERE id = :movimiento_id
RETURNING id, saldo_original, saldo_local, estado;
"""

UPDATE_MOVIMIENTO_SALDO_RESTAR_CONDICIONAL = """
UPDATE movimientos_cxc
SET saldo_original = ROUND(saldo_original - CAST(:monto AS NUMERIC), 2),
    saldo_local = ROUND(saldo_local - CAST(:monto_local AS NUMERIC), 2),
    estado = CASE WHEN ROUND(saldo_original - CAST(:monto AS NUMERIC), 2) <= 0.005
                  THEN CAST('PAGADO' AS estado_documento)
                  ELSE estado END,
    actualizado_en = CURRENT_TIMESTAMP
WHERE id = :movimiento_id
  AND saldo_original >= CAST(:monto AS NUMERIC)
RETURNING id, saldo_original, saldo_local, estado;
"""
