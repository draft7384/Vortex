"""
SQL crudo del módulo Clientes.
Cada constante es un query nombrado semánticamente, ejecutado con `text(...)` desde use_case.
"""

# ============================================================
# CREATE
# ============================================================
INSERT_CLIENTE = """
INSERT INTO clientes (
    codigo, rif, nombre_razon_social, direccion, telefono, email,
    condicion_pago, limite_credito, regimen_iva,
    es_contribuyente_especial, numero_contribuyente_especial,
    moneda_id
) VALUES (
    :codigo, :rif, :nombre_razon_social, :direccion, :telefono, :email,
    :condicion_pago, :limite_credito, :regimen_iva,
    :es_contribuyente_especial, :numero_contribuyente_especial,
    :moneda_id
)
RETURNING id, codigo, rif, nombre_razon_social, direccion, telefono, email,
          condicion_pago, limite_credito, regimen_iva,
          es_contribuyente_especial, numero_contribuyente_especial, moneda_id,
          activo, creado_en, actualizado_en;
"""


# ============================================================
# READ
# ============================================================
SELECT_CLIENTE_BY_ID = """
SELECT id, codigo, rif, nombre_razon_social, direccion, telefono, email,
       condicion_pago, limite_credito, regimen_iva,
       es_contribuyente_especial, numero_contribuyente_especial, moneda_id,
       activo, creado_en, actualizado_en
FROM clientes
WHERE id = :cliente_id;
"""

SELECT_CLIENTES_PAGINATED = """
SELECT id, codigo, rif, nombre_razon_social, condicion_pago, limite_credito,
       es_contribuyente_especial, activo
FROM clientes
WHERE activo = TRUE
ORDER BY nombre_razon_social ASC
LIMIT :limit OFFSET :offset;
"""

SELECT_CLIENTES_COUNT = """
SELECT COUNT(*) AS total
FROM clientes
WHERE activo = TRUE;
"""

SEARCH_CLIENTES_BY_KEYWORD = """
SELECT id, codigo, rif, nombre_razon_social, condicion_pago, limite_credito,
       es_contribuyente_especial, activo
FROM clientes
WHERE activo = TRUE
  AND (
    LOWER(nombre_razon_social) LIKE LOWER(:keyword)
    OR LOWER(rif) LIKE LOWER(:keyword)
    OR LOWER(codigo) LIKE LOWER(:keyword)
  )
ORDER BY nombre_razon_social ASC
LIMIT 50;
"""


# ============================================================
# UPDATE
# ============================================================
UPDATE_CLIENTE = """
UPDATE clientes SET
    codigo                       = COALESCE(:codigo, codigo),
    rif                          = COALESCE(:rif, rif),
    nombre_razon_social          = COALESCE(:nombre_razon_social, nombre_razon_social),
    direccion                    = COALESCE(:direccion, direccion),
    telefono                     = COALESCE(:telefono, telefono),
    email                        = COALESCE(:email, email),
    condicion_pago               = COALESCE(:condicion_pago, condicion_pago),
    limite_credito               = COALESCE(:limite_credito, limite_credito),
    regimen_iva                  = COALESCE(:regimen_iva, regimen_iva),
    es_contribuyente_especial    = COALESCE(:es_contribuyente_especial, es_contribuyente_especial),
    numero_contribuyente_especial = COALESCE(:numero_contribuyente_especial, numero_contribuyente_especial),
    moneda_id                    = COALESCE(:moneda_id, moneda_id),
    activo                       = COALESCE(:activo, activo),
    actualizado_en               = CURRENT_TIMESTAMP
WHERE id = :cliente_id
RETURNING id, codigo, rif, nombre_razon_social, condicion_pago, limite_credito,
          es_contribuyente_especial, activo, actualizado_en;
"""


# ============================================================
# DELETE (soft-delete: activo = FALSE)
# ============================================================
DELETE_CLIENTE = """
UPDATE clientes
SET activo = FALSE, actualizado_en = CURRENT_TIMESTAMP
WHERE id = :cliente_id
RETURNING id, codigo;
"""


# ============================================================
# VALIDACIONES DE NEGOCIO (queries auxiliares)
# ============================================================
SELECT_CLIENTE_BY_RIF = """
SELECT id, codigo, rif, nombre_razon_social, activo
FROM clientes
WHERE rif = :rif;
"""

SELECT_SUM_SALDO_PENDIENTE_CLIENTE = """
SELECT COALESCE(SUM(saldo_original), 0) AS total_pendiente
FROM movimientos_cxc
WHERE cliente_id = :cliente_id AND saldo_original > 0;
"""
