-- =====================================================================
-- schema.sql
-- Script de creación del esquema para el módulo de Facturación y CxC
-- Basado en: facturacion-cxc-spec.md (v2.0)
--
-- CARACTERÍSTICAS:
-- - Idempotente: se puede ejecutar múltiples veces sin errores
-- - Crea extensiones, ENUMs, tablas, índices, constraints y seeds mínimos
-- - Orden de dependencias respetado (no requiere ALTER TABLE posteriores)
--
-- USO:
--   psql -U <usuario> -d <base_de_datos> -f schema.sql
--
-- =====================================================================

-- =====================================================================
-- 0. EXTENSIONES NECESARIAS
-- =====================================================================
CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- para gen_random_uuid() y digest()

-- =====================================================================
-- 1. CREACIÓN DE TIPOS ENUM (de forma segura con DO $$)
-- =====================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_documento_venta') THEN
        CREATE TYPE tipo_documento_venta AS ENUM ('FACTURA', 'NOTA_ENTREGA', 'PRESUPUESTO', 'PEDIDO', 'NOTA_CREDITO', 'NOTA_DEBITO');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_movimiento_cxc') THEN
        CREATE TYPE tipo_movimiento_cxc AS ENUM ('FACTURA', 'NOTA_DEBITO', 'ABONO', 'NOTA_CREDITO', 'RETENCION_IVA', 'RETENCION_ISLR', 'ANTICIPO');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estado_documento') THEN
        CREATE TYPE estado_documento AS ENUM ('BORRADOR', 'EMITIDO', 'ANULADO', 'PAGADO');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'condicion_pago') THEN
        CREATE TYPE condicion_pago AS ENUM ('CONTADO', 'CREDITO', 'ANTICIPO');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_punto_emision') THEN
        CREATE TYPE tipo_punto_emision AS ENUM ('SUCURSAL', 'CAJA', 'DEPOSITO');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'rol_usuario') THEN
        CREATE TYPE rol_usuario AS ENUM ('ADMIN', 'VENDEDOR', 'CAJERO', 'CONTADOR');
    END IF;
END $$;

-- =====================================================================
-- 2. CONFIGURACIÓN DE LA EMPRESA EMISORA (datos fiscales)
-- =====================================================================
-- Tabla singleton (se espera 1 fila). Contiene RIF, razón social, dirección fiscal
-- y rangos SENIAT autorizados por tipo de documento.
CREATE TABLE IF NOT EXISTS empresa_config (
    id SMALLINT PRIMARY KEY DEFAULT 1,
    rif VARCHAR(20) UNIQUE NOT NULL,                  -- Ej: 'J-12345678-9'
    nombre_razon_social VARCHAR(255) NOT NULL,
    nombre_comercial VARCHAR(255),
    direccion_fiscal TEXT NOT NULL,
    telefono VARCHAR(50),
    email VARCHAR(100),
    sitio_web VARCHAR(255),
    logo_url TEXT,

    -- Datos de la máquina fiscal / imprenta digital (asignados por SENIAT)
    serial_imprenta VARCHAR(50),

    -- Rangos autorizados por SENIAT (uno por cada tipo que se emite)
    rango_factura_desde BIGINT,
    rango_factura_hasta BIGINT,
    rango_nc_desde BIGINT,
    rango_nc_hasta BIGINT,
    rango_nd_desde BIGINT,
    rango_nd_hasta BIGINT,

    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_singleton CHECK (id = 1)
);

-- Parámetros generales del sistema (clave-valor, valor en JSONB)
CREATE TABLE IF NOT EXISTS parametros_sistema (
    clave VARCHAR(100) PRIMARY KEY,
    valor JSONB NOT NULL,
    descripcion TEXT,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed del parámetro de antigüedad de saldos (rangos configurables)
INSERT INTO parametros_sistema (clave, valor, descripcion) VALUES
('cxc_rangos_antiguedad', '[30, 60, 90]'::jsonb, 'Rangos en días para reporte de antigüedad de saldos. Formato: cotas superiores consecutivas. Genera buckets: 0-30, 31-60, 61-90, +90.'),
('cxc_bloquear_limite_credito', 'true'::jsonb, 'Si TRUE, bloquea emisión de factura a crédito cuando supera el límite. Override auditable.')
ON CONFLICT (clave) DO NOTHING;

-- =====================================================================
-- 3. USUARIOS (para auditoría multiusuario)
-- =====================================================================
CREATE TABLE IF NOT EXISTS usuarios (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    nombre_completo VARCHAR(150) NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol rol_usuario NOT NULL DEFAULT 'VENDEDOR',
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso TIMESTAMP
);

-- =====================================================================
-- 4. PUNTOS DE EMISIÓN (multi-sucursal / multi-caja)
-- =====================================================================
-- Cada punto de emisión tiene su propia secuencia de numeración por tipo de documento.
-- Ejemplos: 'Sucursal Centro - Caja 1', 'Sucursal Norte - Caja 2'.
CREATE TABLE IF NOT EXISTS puntos_emision (
    id BIGSERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,                -- 'S001', 'S001-C1', 'S002-C1'
    nombre VARCHAR(100) NOT NULL,
    tipo tipo_punto_emision NOT NULL DEFAULT 'SUCURSAL',
    direccion TEXT,
    telefono VARCHAR(50),
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Secuencias independientes por (punto_emision, tipo_documento).
-- El correlativo (codigo) del documento se construye concatenando prefijo + próximo número.
CREATE TABLE IF NOT EXISTS secuencias_documentos (
    id BIGSERIAL PRIMARY KEY,
    punto_emision_id BIGINT REFERENCES puntos_emision(id) NOT NULL,
    tipo_documento tipo_documento_venta NOT NULL,
    prefijo VARCHAR(10) NOT NULL,                       -- 'FAC', 'NC', 'ND', 'NE', 'PED', 'PRES'
    proximo_numero BIGINT NOT NULL DEFAULT 1,
    numero_actual BIGINT NOT NULL DEFAULT 0,
    activo BOOLEAN DEFAULT TRUE,
    CONSTRAINT uq_secuencia_por_punto UNIQUE (punto_emision_id, tipo_documento)
);

-- =====================================================================
-- 5. MAESTROS MULTIMONEDA
-- =====================================================================
CREATE TABLE IF NOT EXISTS monedas (
    id BIGSERIAL PRIMARY KEY,
    codigo_iso CHAR(3) UNIQUE NOT NULL,          -- ISO 4217: 'VES', 'USD', 'EUR', 'COP'...
    nombre VARCHAR(50) NOT NULL,                 -- 'Bolívar', 'Dólar', 'Euro'...
    simbolo VARCHAR(10) NOT NULL,                -- 'Bs.', '$', '€'...
    decimales INT DEFAULT 2,
    es_moneda_local BOOLEAN DEFAULT FALSE,       -- Solo UNA moneda debe ser TRUE (garantizado por índice único parcial)
    activo BOOLEAN DEFAULT TRUE
);

-- Constraint único: solo una moneda puede ser local
CREATE UNIQUE INDEX IF NOT EXISTS uq_moneda_local
    ON monedas ((TRUE)) WHERE es_moneda_local = TRUE;

INSERT INTO monedas (codigo_iso, nombre, simbolo, es_moneda_local) VALUES
('VES', 'Bolívar', 'Bs.', TRUE),
('USD', 'Dólar estadounidense', '$', FALSE),
('EUR', 'Euro', '€', FALSE)
ON CONFLICT (codigo_iso) DO NOTHING;

CREATE TABLE IF NOT EXISTS tasas_cambio (
    id BIGSERIAL PRIMARY KEY,
    moneda_id BIGINT REFERENCES monedas(id) NOT NULL,
    fecha DATE NOT NULL DEFAULT CURRENT_DATE,
    tasa NUMERIC(15,4) NOT NULL,                 -- cuánta moneda local vale 1 unidad de esta moneda
    CONSTRAINT uq_tasa_diaria UNIQUE (moneda_id, fecha)
);
CREATE INDEX IF NOT EXISTS idx_tasas_fecha ON tasas_cambio(fecha);

-- =====================================================================
-- 6. MAESTROS PRINCIPALES (Clientes, Vendedores, Productos)
-- =====================================================================
CREATE TABLE IF NOT EXISTS clientes (
    id BIGSERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    rif VARCHAR(20) UNIQUE NOT NULL,                 -- Formato: 'J-123456789', 'V-12345678', etc.
    nombre_razon_social VARCHAR(255) NOT NULL,
    direccion TEXT,
    telefono VARCHAR(50),
    email VARCHAR(100),
    condicion_pago condicion_pago DEFAULT 'CONTADO',
    limite_credito NUMERIC(15,2) DEFAULT 0.00,
    regimen_iva VARCHAR(20) DEFAULT 'ORDINARIO',      -- ORDINARIO, ESPECIAL, AGENTE
    es_contribuyente_especial BOOLEAN DEFAULT FALSE,  -- Si TRUE, permite registrar RETENCION_IVA
    numero_contribuyente_especial VARCHAR(30),        -- Nro. de provisión SENIAT, requerido si es_contribuyente_especial
    moneda_id BIGINT REFERENCES monedas(id),          -- moneda por defecto del cliente
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vendedores (
    id BIGSERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    usuario_id BIGINT REFERENCES usuarios(id),        -- Relación opcional con usuario del sistema
    nombre VARCHAR(100) NOT NULL,
    comision_pct NUMERIC(5,2) DEFAULT 0.00,
    activo BOOLEAN DEFAULT TRUE
);

-- PRODUCTOS con integración nativa preparada para Shopify (sync futura, no implementada aún)
CREATE TABLE IF NOT EXISTS productos (
    id BIGSERIAL PRIMARY KEY,
    codigo VARCHAR(30) UNIQUE NOT NULL,
    descripcion VARCHAR(255) NOT NULL,
    unidad_medida VARCHAR(10) DEFAULT 'UND',
    precio_base NUMERIC(15,2) NOT NULL,
    impuesto_pct NUMERIC(5,2) DEFAULT 16.00,          -- IVA por defecto
    existencia NUMERIC(15,2) DEFAULT 0.00,
    es_servicio BOOLEAN DEFAULT FALSE,
    activo BOOLEAN DEFAULT TRUE,

    -- >>> CAMPOS DE SINCRONIZACIÓN CON SHOPIFY (preparación, no sync activa) <<<
    shopify_id BIGINT UNIQUE,
    shopify_handle VARCHAR(255) UNIQUE,
    shopify_status VARCHAR(50) DEFAULT 'active',
    shopify_product_type VARCHAR(255),
    shopify_tags TEXT,
    shopify_image_url TEXT,
    shopify_last_synced_at TIMESTAMP,

    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_productos_shopify_id ON productos(shopify_id) WHERE shopify_id IS NOT NULL;

-- =====================================================================
-- 7. MÓDULO DE FACTURACIÓN (Documentos de Venta)
-- =====================================================================
CREATE TABLE IF NOT EXISTS documentos_ventas (
    id BIGSERIAL PRIMARY KEY,
    codigo VARCHAR(30) UNIQUE NOT NULL,               -- Ej: FAC-000125 (correlativo por punto de emisión)
    numero_control VARCHAR(30) UNIQUE,                 -- Nro. de control fiscal SENIAT (solo FACTURA, NC, ND)
    tipo tipo_documento_venta NOT NULL,
    cliente_id BIGINT REFERENCES clientes(id),
    vendedor_id BIGINT REFERENCES vendedores(id),
    punto_emision_id BIGINT REFERENCES puntos_emision(id) NOT NULL,  -- Multi-sucursal/caja
    documento_referencia_id BIGINT REFERENCES documentos_ventas(id),  -- NC/ND referencian al doc. original
    motivo TEXT,                                       -- Motivo de NC/ND, o motivo de anulación
    fecha_emision DATE NOT NULL DEFAULT CURRENT_DATE,
    fecha_vencimiento DATE,

    -- MULTIMONEDA
    moneda_id BIGINT REFERENCES monedas(id) NOT NULL,
    tasa_cambio NUMERIC(15,4) NOT NULL DEFAULT 1.0000,

    -- Montos en la moneda original del documento
    subtotal NUMERIC(15,2) NOT NULL,
    total_impuestos NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    total_descuentos NUMERIC(15,2) DEFAULT 0.00,
    total_neto NUMERIC(15,2) NOT NULL,

    -- Equivalente en moneda local
    total_neto_local NUMERIC(15,2) NOT NULL,

    estado estado_documento DEFAULT 'BORRADOR',
    observaciones TEXT,

    -- Auditoría
    creado_por BIGINT REFERENCES usuarios(id) NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    anulado_por BIGINT REFERENCES usuarios(id),
    anulado_en TIMESTAMP,

    CONSTRAINT chk_totales CHECK (total_neto >= 0),
    -- numero_control es obligatorio solo para FACTURA, NC y ND
    CONSTRAINT chk_numero_control CHECK (
        (tipo IN ('FACTURA', 'NOTA_CREDITO', 'NOTA_DEBITO') AND numero_control IS NOT NULL)
        OR tipo NOT IN ('FACTURA', 'NOTA_CREDITO', 'NOTA_DEBITO')
    )
);

CREATE INDEX IF NOT EXISTS idx_doc_ventas_cliente ON documentos_ventas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_doc_ventas_fecha ON documentos_ventas(fecha_emision);
CREATE INDEX IF NOT EXISTS idx_doc_ventas_estado ON documentos_ventas(estado);
CREATE INDEX IF NOT EXISTS idx_doc_ventas_punto ON documentos_ventas(punto_emision_id);
CREATE INDEX IF NOT EXISTS idx_doc_ventas_referencia ON documentos_ventas(documento_referencia_id);

CREATE TABLE IF NOT EXISTS documentos_ventas_detalle (
    id BIGSERIAL PRIMARY KEY,
    documento_id BIGINT REFERENCES documentos_ventas(id) ON DELETE CASCADE,
    producto_id BIGINT REFERENCES productos(id),
    nro_renglon INT NOT NULL,
    descripcion VARCHAR(255) NOT NULL,
    cantidad NUMERIC(15,2) NOT NULL,
    precio_unitario NUMERIC(15,2) NOT NULL,
    descuento_pct NUMERIC(5,2) DEFAULT 0.00,
    impuesto_pct NUMERIC(5,2) DEFAULT 0.00,
    total_renglon NUMERIC(15,2) NOT NULL,

    CONSTRAINT chk_cantidad CHECK (cantidad > 0),
    CONSTRAINT chk_total_renglon CHECK (total_renglon >= 0)
);

CREATE INDEX IF NOT EXISTS idx_doc_detalle_documento ON documentos_ventas_detalle(documento_id);

-- =====================================================================
-- 8. MÓDULO DE CUENTAS POR COBRAR (CxC)
-- =====================================================================
CREATE TABLE IF NOT EXISTS movimientos_cxc (
    id BIGSERIAL PRIMARY KEY,
    cliente_id BIGINT REFERENCES clientes(id) NOT NULL,
    tipo_movimiento tipo_movimiento_cxc NOT NULL,

    documento_venta_id BIGINT REFERENCES documentos_ventas(id),
    numero_documento VARCHAR(30),

    fecha_movimiento DATE NOT NULL DEFAULT CURRENT_DATE,
    fecha_vencimiento DATE,

    -- MULTIMONEDA
    moneda_id BIGINT REFERENCES monedas(id) NOT NULL,
    tasa_cambio NUMERIC(15,4) NOT NULL,

    -- Montos en moneda original
    monto_original NUMERIC(15,2) NOT NULL,
    saldo_original NUMERIC(15,2) NOT NULL,

    -- Montos en moneda local
    monto_local NUMERIC(15,2) NOT NULL,
    saldo_local NUMERIC(15,2) NOT NULL,

    estado estado_documento DEFAULT 'EMITIDO',
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Auditoría
    registrado_por BIGINT REFERENCES usuarios(id) NOT NULL,

    CONSTRAINT chk_saldo_cxc CHECK (saldo_original >= 0 AND saldo_original <= monto_original),
    CONSTRAINT chk_saldo_local CHECK (saldo_local >= 0 AND saldo_local <= monto_local)
);

CREATE INDEX IF NOT EXISTS idx_cxc_cliente ON movimientos_cxc(cliente_id);
CREATE INDEX IF NOT EXISTS idx_cxc_vencimiento ON movimientos_cxc(fecha_vencimiento);
-- Índice parcial: solo indexa deudas vivas → estado de cuenta / antigüedad instantáneos
CREATE INDEX IF NOT EXISTS idx_cxc_saldo_pendiente ON movimientos_cxc(saldo_original) WHERE saldo_original > 0;

CREATE TABLE IF NOT EXISTS aplicaciones_cxc (
    id BIGSERIAL PRIMARY KEY,
    movimiento_pago_id BIGINT REFERENCES movimientos_cxc(id) NOT NULL,
    movimiento_deuda_id BIGINT REFERENCES movimientos_cxc(id) NOT NULL,
    monto_aplicado_original NUMERIC(15,2) NOT NULL,
    monto_aplicado_local NUMERIC(15,2) NOT NULL,
    fecha_aplicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aplicado_por BIGINT REFERENCES usuarios(id) NOT NULL,

    CONSTRAINT chk_monto_aplicado CHECK (monto_aplicado_original > 0),
    -- Impide aplicar un movimiento contra sí mismo
    CONSTRAINT chk_aplicacion_distinta CHECK (movimiento_pago_id <> movimiento_deuda_id)
);

CREATE INDEX IF NOT EXISTS idx_aplicaciones_pago ON aplicaciones_cxc(movimiento_pago_id);
CREATE INDEX IF NOT EXISTS idx_aplicaciones_deuda ON aplicaciones_cxc(movimiento_deuda_id);

-- =====================================================================
-- 9. AUDITORÍA: OVERRIDE DE LÍMITE DE CRÉDITO
-- =====================================================================
-- Cuando se emite una factura a crédito que excede el límite del cliente
-- y el usuario fuerza la operación con un motivo, se registra aquí.
CREATE TABLE IF NOT EXISTS override_credito_log (
    id BIGSERIAL PRIMARY KEY,
    cliente_id BIGINT REFERENCES clientes(id) NOT NULL,
    documento_venta_id BIGINT REFERENCES documentos_ventas(id) NOT NULL,
    usuario_id BIGINT REFERENCES usuarios(id) NOT NULL,
    limite_vigente NUMERIC(15,2) NOT NULL,            -- límite del cliente al momento del override
    saldo_antes_emision NUMERIC(15,2) NOT NULL,       -- suma de saldos pendientes del cliente antes
    monto_nueva_factura NUMERIC(15,2) NOT NULL,       -- total de la factura que disparó el bloqueo
    monto_excedente NUMERIC(15,2) NOT NULL,           -- (saldo_antes + factura) - limite
    motivo TEXT NOT NULL,                              -- obligatorio, auditable
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_override_cliente ON override_credito_log(cliente_id);
CREATE INDEX IF NOT EXISTS idx_override_documento ON override_credito_log(documento_venta_id);

-- =====================================================================
-- 10. SEEDS MÍNIMOS RECOMENDADOS
-- =====================================================================
-- Empresa por defecto (completar con datos reales)
INSERT INTO empresa_config (
    id, rif, nombre_razon_social, nombre_comercial, direccion_fiscal
) VALUES (
    1, 'J-00000000-0', 'EMPRESA POR DEFECTO C.A.', 'Mi Empresa',
    'Av. Principal, Edif. X, Caracas, Venezuela'
) ON CONFLICT (id) DO NOTHING;

-- Usuario administrador inicial (password: 'admin123' — CAMBIAR INMEDIATAMENTE en producción)
-- Hash bcrypt de 'admin123' generado externamente; aquí va un placeholder que debe reemplazarse
INSERT INTO usuarios (id, username, nombre_completo, email, password_hash, rol) VALUES
(1, 'admin', 'Administrador del Sistema', 'admin@miempresa.com',
 '$2b$12$REEMPLAZAR_CON_HASH_BCRYPT_REAL_DE_ADMIN123', 'ADMIN')
ON CONFLICT (id) DO NOTHING;

-- Punto de emisión por defecto (Casa Matriz)
INSERT INTO puntos_emision (id, codigo, nombre, tipo) VALUES
(1, 'S001', 'Casa Matriz - Caja 1', 'SUCURSAL')
ON CONFLICT (id) DO NOTHING;

-- Secuencia inicial para FACTURA en punto de emisión 1
INSERT INTO secuencias_documentos (punto_emision_id, tipo_documento, prefijo, proximo_numero, numero_actual)
SELECT 1, t.tipo::tipo_documento_venta, t.prefijo, 1, 0
FROM (VALUES
    ('FACTURA', 'FAC'),
    ('NOTA_ENTREGA', 'NE'),
    ('PRESUPUESTO', 'PRES'),
    ('PEDIDO', 'PED'),
    ('NOTA_CREDITO', 'NC'),
    ('NOTA_DEBITO', 'ND')
) AS t(tipo, prefijo)
ON CONFLICT (punto_emision_id, tipo_documento) DO NOTHING;

-- =====================================================================
-- 11. SINCRONIZAR SECUENCIAS BIGSERIAL CON SEEDS EXISTENTES
-- =====================================================================
-- Los seeds anteriores insertan filas con id explicito, lo que NO avanza
-- la secuencia. Sin este paso, el siguiente INSERT choca con el PK.
-- (is_called=true garantiza que nextval() devuelva MAX(id)+1)
SELECT setval('usuarios_id_seq',                  (SELECT COALESCE(MAX(id), 0) FROM usuarios),                  true);
SELECT setval('puntos_emision_id_seq',           (SELECT COALESCE(MAX(id), 0) FROM puntos_emision),           true);
SELECT setval('secuencias_documentos_id_seq',    (SELECT COALESCE(MAX(id), 0) FROM secuencias_documentos),    true);

-- =====================================================================
-- FIN DEL SCRIPT
-- =====================================================================
-- Total de tablas creadas: 15
--   1. empresa_config
--   2. parametros_sistema
--   3. usuarios
--   4. puntos_emision
--   5. secuencias_documentos
--   6. monedas
--   7. tasas_cambio
--   8. clientes
--   9. vendedores
--   10. productos
--   11. documentos_ventas
--   12. documentos_ventas_detalle
--   13. movimientos_cxc
--   14. aplicaciones_cxc
--   15. override_credito_log
--
-- Para verificar la instalación:
--   SELECT table_name FROM information_schema.tables
--   WHERE table_schema = 'public' ORDER BY table_name;
-- =====================================================================
