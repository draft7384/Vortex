# Especificación Técnica: Módulo de Facturación y Cuentas por Cobrar (CxC)

> **Propósito de este documento:** Esta es la especificación funcional y técnica completa para construir, mediante IA/vibe coding, el módulo de **Facturación** y **Cuentas por Cobrar** de un sistema administrativo para pequeños comerciantes en Venezuela. Está inspirado en la lógica de Profit Plus/Profit 21, pero modernizado. **El alcance de este documento es exclusivamente lo aquí descrito** — no agregar inventario avanzado, compras, nómina, ni contabilidad general salvo lo estrictamente necesario para que Facturación y CxC funcionen.

> **Versión:** 2.0 — Incluye soporte multi-sucursal / multi-caja / multi-punto de emisión, multiusuario con auditoría, número de control fiscal SENIAT separado del correlativo interno, contribuyente especial, regla de anulación segura, límite de crédito bloqueante con override auditable, y antigüedad de saldos configurable. Ver sección 12 para la lista de cambios respecto a v1.0.

---

## 1. Contexto y Objetivo del Sistema

Se busca construir un sistema **menos complejo que Profit u Odoo**, más económico y accesible para emprendedores venezolanos, pero **igual de robusto** en el módulo de Facturación y CxC.

**Regla de negocio central:**
> La Facturación registra la operación de venta (histórico inalterable). El CxC registra la deuda que esa venta genera y el historial de pagos que la cancelan (mutable).

### Stack tecnológico objetivo
- **Backend:** Python + FastAPI
- **Base de datos:** PostgreSQL
- **ORM sugerido:** SQLAlchemy o SQLModel (a definir en la implementación)
- **Validación:** Pydantic (schemas de entrada/salida de la API)
- **Arquitectura de integración futura:** API REST propia ahora; capa de consumo SOAP/XML más adelante (estilo Odoo) — **no implementar en esta fase**, solo dejar el diseño desacoplado para no bloquearlo.
- **Multimoneda:** nativo (VES, USD, EUR, ampliable a cualquier moneda ISO 4217)
- **Integración futura con Shopify:** el maestro de productos ya contempla campos de sincronización, pero la sincronización en sí **no se implementa en esta fase**.

---

## 2. Alcance Funcional (Scope)

### 2.1 Incluido en este módulo
- Emisión de documentos de venta: **facturas, notas de entrega, presupuestos, pedidos**.
- Documentos de ajuste: **notas de crédito y notas de débito** (con referencia explícita al documento original y motivo).
- Registro de **pagos y abonos** de clientes.
- Control de **anticipos**.
- Manejo de **retenciones de impuestos** (IVA, ISLR) aplicadas por el cliente.
- Cálculo de **vencimientos y antigüedad de saldos** (con rangos configurables).
- **Estados de cuenta** por cliente.
- Integración automática con inventario (descuento de existencia simple), y puntos de enganche para contabilidad y caja/bancos (sin implementar esos módulos completos).
- **Multimoneda** (VES, USD, EUR y ampliable) con tasas de cambio históricas por día.
- Maestro de **clientes**, **vendedores** y **productos** (versión simplificada, suficiente para facturar).
- **Multi-sucursal / multi-caja / multi-punto de emisión** con secuencias de numeración independientes por punto.
- **Multiusuario con auditoría**: todos los documentos y movimientos registran quién los creó/anuló/pagó.
- **Datos fiscales del emisor** (empresa que factura) en tabla de configuración: RIF, razón social, dirección fiscal, serial de imprenta digital, rango SENIAT autorizado por tipo de documento.
- **Límite de crédito bloqueante** al emitir facturas a crédito, con override auditable (requiere motivo).
- **Regla de anulación segura**: no se anula una factura con saldo pagado sin reversar primero las aplicaciones.

### 2.2 Fuera de alcance (no implementar ahora)
- Módulo de Compras / Cuentas por Pagar / Proveedores.
- Contabilidad general completa (libro mayor, plan de cuentas, asientos automáticos) — solo dejar el "gancho" (`documento_venta_id`, `movimiento_cxc`) para integrarlo después.
- Nómina.
- Inventario avanzado (múltiples almacenes, kits, lotes, series).
- Sincronización real con Shopify (solo se preparan los campos en la tabla `productos`).
- Consumo SOAP/XML (solo se diseña pensando en no bloquear esa futura capa).

---

## 3. Glosario / Equivalencia con Profit (contexto de origen)

Esta tabla es solo **referencia conceptual** para quien conozca Profit; el sistema nuevo **no usa estos nombres de tabla**, usa los nombres en español definidos en la sección 5.

| Tabla Profit | Equivalente en este sistema | Función |
|---|---|---|
| `SACLI` | `clientes` | Maestro de clientes |
| `SAVEN` | `vendedores` | Maestro de vendedores |
| `SAPROD` / `SAEXIS` | `productos` | Maestro de productos / existencias |
| `SAFACT` | `documentos_ventas` | Encabezado de documentos de venta |
| `SAFACR` | `documentos_ventas_detalle` | Renglones/detalle de cada documento |
| `SACXC` | `movimientos_cxc` | Libro mayor de cuentas por cobrar (deudas y pagos) |
| `SACXC_APLIC` | `aplicaciones_cxc` | Cruces entre pagos/retenciones y facturas |
| `SASAL` | (derivado por consulta, no tabla física) | Saldos acumulados / antigüedad de saldos |
| `SAMOV` | (fuera de alcance, futuro módulo inventario) | Movimientos de inventario |

**Diferencia clave de diseño vs. Profit:** en vez de duplicar la factura dentro de CxC, `movimientos_cxc` funciona como un **libro mayor**: cada evento (factura, abono, retención, nota de crédito/débito, anticipo) es un registro nuevo, y `aplicaciones_cxc` es la tabla que **cruza** pagos contra deudas, permitiendo auditar exactamente qué pago canceló qué factura.

---

## 4. Reglas de Negocio Clave

1. **Inmutabilidad de la venta:** una vez `EMITIDO` un documento de venta, sus renglones y totales no se modifican; los ajustes se hacen con notas de crédito/débito.
2. **Nacimiento automático de la deuda:** al emitir una factura a crédito, se crea automáticamente un registro en `movimientos_cxc` (tipo `FACTURA`) con `saldo_original = monto_original`.
3. **Aplicación de pagos:** un pago (`ABONO`), retención (`RETENCION_IVA` / `RETENCION_ISLR`) o nota de crédito no borra el saldo directamente: se inserta como movimiento propio en `movimientos_cxc` y luego se registra su cruce en `aplicaciones_cxc` contra la(s) factura(s) que cancela. Solo entonces se actualiza el `saldo_original` / `saldo_local` de la factura afectada.
4. **Transaccionalidad obligatoria:** crear factura + su renglones + su movimiento de CxC debe ocurrir en una sola transacción DB (`BEGIN/COMMIT`, rollback si falla cualquier paso). Lo mismo aplica para registrar pago + aplicación + actualización de saldo.
5. **Multimoneda con tasa congelada:** cada documento de venta y cada movimiento de CxC guarda la **tasa de cambio del día exacto** en que ocurrió. Los históricos nunca se recalculan con la tasa de hoy.
6. **Retenciones como "pagos":** una retención de IVA/ISLR se trata como un `movimiento_cxc` más (no como un descuento directo), y se aplica a la factura igual que un abono. Esto permite que el estado de cuenta cuadre en cero automáticamente, cumpliendo la práctica fiscal venezolana.
7. **Antigüedad de saldos / estado de cuenta:** deben poder calcularse de forma eficiente a partir de `movimientos_cxc` filtrando por `saldo_original > 0` (existe índice parcial dedicado para esto).
8. **Restricciones de integridad:**
   - `saldo_original` nunca puede ser negativo ni mayor que `monto_original` (mismo para `_local`).
   - `monto_aplicado_original` en `aplicaciones_cxc` siempre debe ser positivo.
   - `cantidad` y `total_renglon` en el detalle de venta siempre deben ser positivos/no negativos.
9. **Un cliente tiene una moneda por defecto**, pero puede facturarse en cualquier moneda activa; y puede pagar en una moneda distinta a la de la factura original (el cruce en `aplicaciones_cxc` se hace convirtiendo con la tasa del día del pago).
10. **Auditoría de usuario obligatoria:** toda tabla transaccional (`documentos_ventas`, `movimientos_cxc`, `aplicaciones_cxc`) registra `creado_por` con FK a la tabla de usuarios. Las anulaciones registran `anulado_por` y `motivo_anulacion`.
11. **Número de control fiscal SENIAT:** las facturas, notas de crédito y notas de débito llevan un `numero_control` único, separado del correlativo interno `codigo`. Este número es asignado por la imprenta digital / máquina fiscal y es obligatorio en impresión fiscal.
12. **Multi-punto de emisión:** cada documento de venta se asocia a un `punto_emision_id`. El correlativo `codigo` se genera por combinación `(tipo_documento, punto_emision)` y nunca se repite entre puntos.
13. **Anulación segura:** una factura (`documentos_ventas`) en estado `EMITIDO` con `saldo_original = 0` (totalmente pagada) **no se puede anular directamente**. Primero deben reversarse todas las `aplicaciones_cxc` asociadas. Una factura con saldo pendiente puede anularse (la operación registra una `NOTA_CREDITO` interna y reversa el movimiento CxC, o marca el documento y su movimiento como anulados conservando histórico).
14. **Límite de crédito bloqueante con override auditable:** al emitir una factura a crédito, se valida que la suma de saldos pendientes del cliente + el nuevo total no supere `clientes.limite_credito`. Si lo supera, el endpoint retorna 409 con código `LIMITE_CREDITO_EXCEDIDO`. El cliente (vendedor/admin) puede **sobrescribir** el bloqueo enviando `forzar_credito: true` y `motivo_override: "..."`, lo cual se registra en una tabla `override_credito_log` para auditoría.
15. **Contribuyente especial:** los clientes marcados `es_contribuyente_especial = TRUE` permiten registrar retenciones de IVA (`RETENCION_IVA`). El campo `numero_contribuyente_especial` se imprime en la factura cuando aplica.
16. **Antigüedad de saldos configurable:** los rangos (ej. 0-30, 31-60, 61-90, +90) se leen de la tabla `parametros_sistema` (clave `cxc_rangos_antiguedad`, valor JSON), no están hardcodeados en el SQL.
17. **Constraint único de moneda local:** solo una fila en `monedas` puede tener `es_moneda_local = TRUE`, garantizado por índice único parcial a nivel DB.

---

## 5. Modelo de Datos (PostgreSQL) — Script Definitivo

> Este es el script **final y optimizado**, idempotente (usa `IF NOT EXISTS` y bloques `DO $$` para los `ENUM`, ya que PostgreSQL no soporta `CREATE TYPE IF NOT EXISTS` de forma nativa). Puede ejecutarse repetidas veces sin error de "relation/type already exists". **Este es el script que la IA debe usar como fuente de verdad** — no usar versiones anteriores/intermedias que puedan aparecer en el histórico de decisiones (sección 8).

```sql
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
('cxc_rangos_antiguedad', '[0, 30, 60, 90]'::jsonb, 'Rangos en días para reporte de antigüedad de saldos (último valor = +infinito)'),
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
SELECT 1, t.tipo, t.prefijo, 1, 0
FROM (VALUES
    ('FACTURA', 'FAC'),
    ('NOTA_ENTREGA', 'NE'),
    ('PRESUPUESTO', 'PRES'),
    ('PEDIDO', 'PED'),
    ('NOTA_CREDITO', 'NC'),
    ('NOTA_DEBITO', 'ND')
) AS t(tipo, prefijo)
ON CONFLICT (punto_emision_id, tipo_documento) DO NOTHING;
```

### 5.1 Notas de diseño sobre el esquema
- **`monedas.es_moneda_local`**: solo un registro debe tener `TRUE`, **garantizado por índice único parcial** `CREATE UNIQUE INDEX ON monedas ((TRUE)) WHERE es_moneda_local = TRUE`. Imposible a nivel DB tener dos monedas locales.
- **Internacionalización:** para soportar otro país, solo se agrega una fila en `monedas` — no se toca código Python.
- **Historial intocable:** `tasa_cambio` se congela en `documentos_ventas` y `movimientos_cxc`; los reportes históricos nunca se recalculan.
- **Pago en moneda distinta a la factura:** el registro de pago en `movimientos_cxc` puede tener un `moneda_id` distinto al de la factura; la conversión para aplicar el pago se hace en `aplicaciones_cxc` usando la tasa del día del pago.
- **Numeración fiscal vs interna:**
  - `documentos_ventas.codigo` = correlativo interno generado por `secuencias_documentos` (ej. `FAC-000125`).
  - `documentos_ventas.numero_control` = número fiscal asignado por la imprenta digital / SENIAT. Obligatorio solo para `FACTURA`, `NOTA_CREDITO` y `NOTA_DEBITO` (validado por `chk_numero_control`). El sistema alerta al acercarse al `rango_factura_hasta` configurado en `empresa_config`.
- **Multi-punto de emisión:** cada documento de venta se asocia a un `punto_emision_id`. La combinación `(punto_emision_id, tipo_documento)` define la secuencia en `secuencias_documentos`. El endpoint de crear documento debe hacer `SELECT ... FOR UPDATE` sobre la fila de secuencia para evitar concurrencia.
- **Auditoría:** `creado_por` es `NOT NULL` en todas las tablas transaccionales; `anulado_por` y `anulado_en` solo se llenan al pasar a `ANULADO`. `motivo_anulacion` se reutiliza el campo `motivo` del encabezado.
- **Override de crédito:** cuando `cxc_bloquear_limite_credito = true` en `parametros_sistema` y se excede el límite, el endpoint retorna 409 con código `LIMITE_CREDITO_EXCEDIDO`. Si el request trae `forzar_credito: true` y `motivo_override` no vacío, se registra en `override_credito_log` y se permite la operación.
- **Antigüedad configurable:** el endpoint `GET /cxc/antiguedad-saldos` lee `parametros_sistema.clave = 'cxc_rangos_antiguedad'` y construye los buckets dinámicamente (ej. `[0, 30, 60, 90]` → buckets `0-30`, `31-60`, `61-90`, `+90`).

---

## 6. Relaciones entre Entidades (resumen)

```
usuarios 1───N documentos_ventas (creado_por, anulado_por)
usuarios 1───N movimientos_cxc (registrado_por)
usuarios 1───N aplicaciones_cxc (aplicado_por)
usuarios 1───1 vendedores (opcional, vendedor también puede ser usuario)

empresa_config (singleton — 1 fila)

puntos_emision 1───N documentos_ventas
puntos_emision 1───N secuencias_documentos

documentos_ventas 1───1(0..1) documentos_ventas (documento_referencia_id, NC/ND → factura)

monedas 1───N tasas_cambio
monedas 1───N clientes (moneda por defecto)
monedas 1───N documentos_ventas
monedas 1───N movimientos_cxc

clientes 1───N documentos_ventas
clientes 1───N movimientos_cxc
clientes 1───N override_credito_log

vendedores 1───N documentos_ventas

productos 1───N documentos_ventas_detalle

documentos_ventas 1───N documentos_ventas_detalle
documentos_ventas 1───1(0..1) movimientos_cxc   (vía documento_venta_id, cuando el movimiento es tipo FACTURA/ND/NC)
documentos_ventas 1───N override_credito_log

movimientos_cxc 1───N aplicaciones_cxc (como movimiento_pago_id)
movimientos_cxc 1───N aplicaciones_cxc (como movimiento_deuda_id)
```

**Regla de relación factura ↔ CxC:** al emitir una factura a crédito, se crea un registro espejo en `movimientos_cxc` (`tipo_movimiento = 'FACTURA'`, `documento_venta_id` = id de la factura, `monto_original` = total de la factura, `saldo_original` = mismo monto inicialmente). Los pagos posteriores son **nuevos registros independientes** en `movimientos_cxc`, cruzados contra esa deuda mediante `aplicaciones_cxc`.

---

## 7. Flujos de Negocio / Lógica de Servicios (para los endpoints FastAPI)

### 7.1 Crear documento de venta — `POST /documentos-ventas`
1. **Autenticación:** el request debe incluir el `usuario_id` (extraído del token JWT en producción, pero el spec lo recibe explícito en el body/header para mantener el contrato del servicio).
2. Validar existencia y estado activo de cliente, vendedor (opcional), productos, y `punto_emision_id`.
3. Si el documento es `FACTURA`, `NOTA_CREDITO` o `NOTA_DEBITO`: validar que `numero_control` venga en el body (no nulo). Si el tipo es `NOTA_CREDITO` o `NOTA_DEBITO`: validar que `documento_referencia_id` exista y sea de tipo `FACTURA`.
4. Si el cliente es `es_contribuyente_especial = FALSE`, **rechazar** retenciones de IVA en cualquier movimiento relacionado (validación cruzada al registrar pagos).
5. **Validación de stock** si el producto no es servicio (descuento simple de `existencia`, sin manejo de almacenes múltiples).
6. **Tasa de cambio:** obtener la tasa del día (`tasas_cambio` por `moneda_id` + `fecha_actual`). Si no existe → 400 `DEBE_CARGAR_TASA_DEL_DIA`.
7. **Límite de crédito (solo si `tipo = FACTURA` y `condicion_pago = CREDITO`):**
   - Calcular `suma_saldo_pendiente = SUM(movimientos_cxc.saldo_original WHERE cliente_id = ? AND saldo_original > 0)`.
   - Calcular `nuevo_total_factura = total_neto`.
   - Si `suma_saldo_pendiente + nuevo_total_factura > clientes.limite_credito`:
     - Si `parametros_sistema.cxc_bloquear_limite_credito = true` Y el request **no** trae `forzar_credito: true` con `motivo_override` no vacío → retornar **409 `LIMITE_CREDITO_EXCEDIDO`** con detalle del cálculo.
     - Si trae `forzar_credito: true` y `motivo_override` válido → continuar y registrar en `override_credito_log` (dentro de la misma transacción).
     - Si `cxc_bloquear_limite_credito = false` → solo registrar warning en log, no bloquear.
8. **Correlativo interno (transaccional):**
   ```sql
   SELECT * FROM secuencias_documentos
   WHERE punto_emision_id = ? AND tipo_documento = ?
   FOR UPDATE;  -- evita carreras
   UPDATE secuencias_documentos
   SET numero_actual = numero_actual + 1, proximo_numero = numero_actual + 2
   WHERE id = ?;
   -- codigo = CONCAT(prefijo, '-', LPAD(numero_actual::text, 6, '0'))
   ```
9. Calcular `subtotal`, `total_impuestos`, `total_descuentos`, `total_neto` y `total_neto_local`.
10. **En una sola transacción:**
    - Insertar encabezado en `documentos_ventas` (`estado = 'EMITIDO'` si no es borrador, con `creado_por`).
    - Insertar renglones en `documentos_ventas_detalle`.
    - Si `tipo = 'FACTURA'` y `condicion_pago = 'CREDITO'`: insertar el movimiento espejo en `movimientos_cxc` (tipo `FACTURA`, `registrado_por` = mismo usuario).
    - Si `tipo = 'NOTA_CREDITO'`: insertar movimiento CxC tipo `NOTA_CREDITO` y crear `aplicacion_cxc` automática contra el movimiento de la factura referenciada.
    - Si `tipo = 'NOTA_DEBITO'`: insertar movimiento CxC tipo `NOTA_DEBITO` (deuda nueva contra el cliente).
    - Descontar existencia de productos físicos.
    - Si se forzó override de crédito → insertar en `override_credito_log`.
11. Si algo falla → `ROLLBACK` completo.

### 7.2 Registrar pago / abono — `POST /cxc/pagos`
1. Autenticación: requiere `usuario_id`.
2. Si el cliente es `es_contribuyente_especial = FALSE`, rechazar cualquier `RETENCION_IVA` en el request → 400 `CLIENTE_NO_ES_CONTRIBUYENTE_ESPECIAL`.
3. Obtener tasa de cambio del día del pago.
4. **En una sola transacción:**
   - Insertar movimiento(s) en `movimientos_cxc` (tipo `ABONO` y/o `RETENCION_IVA` / `RETENCION_ISLR`, según corresponda), con `registrado_por`.
   - Insertar el/los cruce(s) en `aplicaciones_cxc`, con `aplicado_por`.
   - Actualizar `saldo_original` y `saldo_local` de cada factura afectada (`saldo -= monto_aplicado`).
   - Si el saldo llega a 0, marcar `estado = 'PAGADO'` en el movimiento de la factura.
5. Validar que la suma de montos aplicados nunca deje un saldo negativo (constraint DB lo impide, pero validar antes para buen mensaje).

### 7.3 Notas de crédito / débito — `POST /notas-credito` y `POST /notas-debito`
- Requieren `documento_referencia_id` (la factura original) y `motivo` (texto obligatorio).
- Requieren `numero_control` (validado por `chk_numero_control`).
- Requieren `punto_emision_id` y consumen la secuencia del tipo correspondiente.
- **NC:** genera movimiento `NOTA_CREDITO` en CxC y aplica automáticamente contra el movimiento de la factura referenciada (similar a un pago). Si la factura está totalmente pagada, se rebajan los pagos proporcionalmente (reverso de aplicaciones) — **caso excepcional, requiere decisión de negocio adicional**.
- **ND:** genera movimiento `NOTA_DEBITO` en CxC (deuda nueva). Si se referencia a una factura existente, se considera un cargo adicional al cliente.

### 7.4 Anticipos — `POST /cxc/anticipos`
- Se registran como `movimientos_cxc` tipo `ANTICIPO` con `saldo_original` positivo (a favor del cliente, saldo pendiente de aplicar contra futuras facturas).
- Cuando se emite una factura posterior, el anticipo se "aplica" vía `aplicaciones_cxc` igual que un abono.
- Si el anticipo es en moneda distinta a la factura futura, la conversión se hace en `aplicaciones_cxc` con la tasa del día de la aplicación.

### 7.5 Retenciones (IVA / ISLR)
- Se registran como `movimientos_cxc` (tipo `RETENCION_IVA` / `RETENCION_ISLR`) y se aplican a la factura correspondiente vía `aplicaciones_cxc`, exactamente igual que un abono.
- El estado de cuenta cierra en cero aunque el cliente nunca transfiera el 100% en efectivo.
- **Restricción:** `RETENCION_IVA` solo se permite si `clientes.es_contribuyente_especial = TRUE`.

### 7.6 Anular documento de venta — `POST /documentos-ventas/{id}/anular`
1. Validar que el documento esté en estado `EMITIDO` o `BORRADOR`. Si ya está `ANULADO` o `PAGADO` → 400.
2. **Regla de anulación segura:**
   - Si el documento tiene movimientos en `aplicaciones_cxc` (es decir, ya fue pagado total o parcialmente):
     - **Bloquear la anulación directa** → retornar 409 `DOCUMENTO_CON_PAGOS_APLICADOS`. Indicar al cliente que primero debe reversar los pagos (`POST /cxc/aplicaciones/{id}/reversar`) o emitir una `NOTA_CREDITO` por el saldo pendiente.
     - Excepción: si todas las aplicaciones aún pueden reversarse (no están reconciliadas con un módulo externo), permitir override con `forzar_anulacion: true` + `motivo` (auditable en `documentos_ventas.motivo` + `anulado_por`).
   - Si no tiene aplicaciones → proceder.
3. **En una sola transacción:**
   - Marcar `documentos_ventas.estado = 'ANULADO'`, `anulado_por = ?`, `anulado_en = NOW()`, llenar `motivo` con el motivo recibido.
   - Si tiene movimiento CxC espejo, marcarlo `ANULADO` también (mantener histórico).
   - Si la factura había descontado existencia, **devolver stock** a los productos.
4. Retornar documento actualizado.

### 7.7 Estado de cuenta por cliente — `GET /clientes/{id}/estado-cuenta`
- Consulta sobre `movimientos_cxc` filtrando por `cliente_id`, mostrando todos los movimientos (deudas y pagos) ordenados por fecha, con su `saldo_original` / `saldo_local` y su `numero_documento`.

### 7.8 Antigüedad de saldos — `GET /cxc/antiguedad-saldos`
1. Leer `parametros_sistema.clave = 'cxc_rangos_antiguedad'` (ej. `[0, 30, 60, 90]`).
2. Generar buckets dinámicamente: `0-30`, `31-60`, `61-90`, `+90`.
3. Consultar `movimientos_cxc WHERE saldo_original > 0` (usa el índice parcial `idx_cxc_saldo_pendiente`) y agrupar por rango de días vencidos respecto a `fecha_vencimiento`.
4. Aceptar query param opcional `?rangos=0,30,60,90,120` para sobrescribir temporalmente.

### 7.9 Listado de documentos con paginación
- Todos los endpoints de listado (`GET /documentos-ventas`, `GET /movimientos-cxc`, etc.) deben soportar `?limit=`, `?offset=`, `?order_by=`, `?order_dir=`, y filtros específicos (cliente, fecha desde/hasta, estado).

---

## 8. Ejemplo de Datos Semilla (para pruebas / entender el flujo)

> Orden de dependencia obligatorio para los `INSERT`: **empresa_config → usuarios → puntos_emision → secuencias_documentos → monedas → tasas_cambio → vendedores/clientes/productos → documentos_ventas → documentos_ventas_detalle → movimientos_cxc (factura) → movimientos_cxc (pagos/retenciones) → aplicaciones_cxc → UPDATE de saldos**.

**Escenario:** Factura en USD a un cliente Contribuyente Especial (sujeto a retención de IVA), emitida desde el punto de emisión `S001` por el usuario `admin (id=1)`, con pago parcial por transferencia y retención del 100% del IVA.

```sql
-- Nivel 0: Empresa, usuario, punto de emisión, secuencias
INSERT INTO empresa_config (id, rif, nombre_razon_social, direccion_fiscal, rango_factura_desde, rango_factura_hasta)
VALUES (1, 'J-12345678-9', 'Inversiones Demo C.A.', 'Av. Principal, Caracas', 1, 50000)
ON CONFLICT (id) DO NOTHING;

INSERT INTO puntos_emision (id, codigo, nombre, tipo) VALUES
(1, 'S001', 'Casa Matriz - Caja 1', 'SUCURSAL')
ON CONFLICT (id) DO NOTHING;

INSERT INTO secuencias_documentos (punto_emision_id, tipo_documento, prefijo, proximo_numero, numero_actual)
VALUES (1, 'FACTURA', 'FAC', 1, 0)
ON CONFLICT (punto_emision_id, tipo_documento) DO NOTHING;

-- Nivel 1: Monedas y tasas
INSERT INTO monedas (id, codigo_iso, nombre, simbolo, decimales, es_moneda_local, activo) VALUES
(1, 'VES', 'Bolívar', 'Bs.', 2, TRUE, TRUE),
(2, 'USD', 'Dólar estadounidense', '$', 2, FALSE, TRUE),
(3, 'EUR', 'Euro', '€', 2, FALSE, TRUE)
ON CONFLICT (id) DO NOTHING;

INSERT INTO tasas_cambio (moneda_id, fecha, tasa) VALUES
(2, CURRENT_DATE, 36.5000),
(3, CURRENT_DATE, 39.8000)
ON CONFLICT (moneda_id, fecha) DO NOTHING;

-- Nivel 2: Maestros
INSERT INTO vendedores (id, codigo, nombre, comision_pct, activo) VALUES
(1, 'V001', 'Carlos Mendoza', 5.00, TRUE)
ON CONFLICT (id) DO NOTHING;

INSERT INTO clientes (id, codigo, rif, nombre_razon_social, condicion_pago, limite_credito,
                     regimen_iva, es_contribuyente_especial, numero_contribuyente_especial, moneda_id)
VALUES (1, 'C001', 'J-123456789', 'Inversiones El Tigre C.A.', 'CREDITO', 5000.00,
        'ESPECIAL', TRUE, 'CE-12345', 2)
ON CONFLICT (id) DO NOTHING;

INSERT INTO productos (id, codigo, descripcion, precio_base, impuesto_pct, existencia, es_servicio) VALUES
(1, 'PROD-001', 'Laptop HP 15" Core i5', 500.00, 16.00, 10.00, FALSE)
ON CONFLICT (id) DO NOTHING;

-- Nivel 3: Encabezado de factura (2 laptops x $500 = $1000, IVA 16% = $160, total $1160, tasa 36.50 → 42,340 Bs)
INSERT INTO documentos_ventas (
    id, codigo, numero_control, tipo, cliente_id, vendedor_id, punto_emision_id,
    fecha_emision, fecha_vencimiento,
    moneda_id, tasa_cambio, subtotal, total_impuestos, total_neto, total_neto_local,
    estado, creado_por
) VALUES (
    1, 'FAC-000001', '00-00000001', 'FACTURA', 1, 1, 1,
    CURRENT_DATE, CURRENT_DATE + 15,
    2, 36.5000, 1000.00, 160.00, 1160.00, 42340.00,
    'EMITIDO', 1
)
ON CONFLICT (id) DO NOTHING;

-- Nivel 4: Detalle
INSERT INTO documentos_ventas_detalle (
    documento_id, producto_id, nro_renglon, descripcion, cantidad, precio_unitario, impuesto_pct, total_renglon
) VALUES
(1, 1, 1, 'Laptop HP 15" Core i5', 2.00, 500.00, 16.00, 1000.00);

-- Nivel 5: Nace la deuda en CxC
INSERT INTO movimientos_cxc (
    id, cliente_id, tipo_movimiento, documento_venta_id, numero_documento,
    fecha_movimiento, fecha_vencimiento, moneda_id, tasa_cambio,
    monto_original, saldo_original, monto_local, saldo_local, estado, registrado_por
) VALUES (
    1, 1, 'FACTURA', 1, 'FAC-000001',
    CURRENT_DATE, CURRENT_DATE + 15, 2, 36.5000,
    1160.00, 1160.00, 42340.00, 42340.00, 'EMITIDO', 1
);

-- Nivel 6: Retención de IVA (100% del impuesto) + Pago parcial por transferencia
INSERT INTO movimientos_cxc (
    id, cliente_id, tipo_movimiento, numero_documento, fecha_movimiento,
    moneda_id, tasa_cambio, monto_original, saldo_original, monto_local, saldo_local, estado, registrado_por
) VALUES (
    2, 1, 'RETENCION_IVA', 'RET-IVA-2023-001', CURRENT_DATE,
    2, 36.5000, 160.00, 160.00, 5840.00, 5840.00, 'EMITIDO', 1
);

INSERT INTO movimientos_cxc (
    id, cliente_id, tipo_movimiento, numero_documento, fecha_movimiento,
    moneda_id, tasa_cambio, monto_original, saldo_original, monto_local, saldo_local, estado, registrado_por
) VALUES (
    3, 1, 'ABONO', 'REF-BANC-998877', CURRENT_DATE,
    2, 36.5000, 1000.00, 1000.00, 36500.00, 36500.00, 'EMITIDO', 1
);

-- Aplicaciones: cruzar retención y abono contra la factura
INSERT INTO aplicaciones_cxc (movimiento_pago_id, movimiento_deuda_id, monto_aplicado_original, monto_aplicado_local, aplicado_por)
VALUES (2, 1, 160.00, 5840.00, 1);

INSERT INTO aplicaciones_cxc (movimiento_pago_id, movimiento_deuda_id, monto_aplicado_original, monto_aplicado_local, aplicado_por)
VALUES (3, 1, 1000.00, 36500.00, 1);

-- Actualización de saldos (en la API real esto va DENTRO de la misma transacción del pago)
UPDATE movimientos_cxc SET saldo_original = 0.00, saldo_local = 0.00, estado = 'PAGADO' WHERE id = 1;
UPDATE movimientos_cxc SET saldo_original = 0.00, saldo_local = 0.00, estado = 'PAGADO' WHERE id IN (2, 3);
```

---

## 9. Sugerencia de Endpoints FastAPI (a construir)

### 9.1 Maestros y configuración
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/auth/login` | Login (devuelve JWT con `usuario_id`) |
| GET/PUT | `/empresa-config` | Obtener/actualizar datos fiscales de la empresa |
| POST | `/monedas` | Crear moneda (ISO 4217) |
| POST | `/tasas-cambio` | Registrar tasa del día |
| GET/PUT | `/parametros-sistema/{clave}` | Consultar/actualizar parámetros |
| POST/GET | `/usuarios` | Crear/listar usuarios (solo ADMIN) |
| POST/GET | `/puntos-emision` | Crear/listar puntos de emisión (sucursales/cajas) |
| POST/GET | `/secuencias-documentos` | Configurar secuencias por punto de emisión |
| POST/GET/PUT | `/clientes` | CRUD de clientes |
| GET | `/clientes/{id}/estado-cuenta` | Estado de cuenta del cliente |
| POST/GET/PUT | `/productos` | CRUD de productos |
| POST/GET/PUT | `/vendedores` | CRUD de vendedores |

### 9.2 Documentos de venta
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/documentos-ventas` | Emitir factura/nota de entrega/presupuesto/pedido (soporta `forzar_credito`) |
| GET | `/documentos-ventas` | Listar con paginación y filtros |
| GET | `/documentos-ventas/{id}` | Obtener documento con detalle |
| POST | `/documentos-ventas/{id}/anular` | Anular documento (regla segura) |
| POST | `/notas-credito` | Emitir NC (requiere `documento_referencia_id`, `motivo`, `numero_control`) |
| POST | `/notas-debito` | Emitir ND (requiere `documento_referencia_id`, `motivo`, `numero_control`) |

### 9.3 Cuentas por cobrar
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/cxc/pagos` | Registrar abono/pago (con o sin retenciones) |
| POST | `/cxc/anticipos` | Registrar anticipo de cliente |
| POST | `/cxc/aplicaciones` | Aplicar un movimiento contra otro (manual) |
| POST | `/cxc/aplicaciones/{id}/reversar` | Reversar una aplicación (para anular facturas pagadas) |
| GET | `/cxc/antiguedad-saldos` | Reporte de antigüedad (rangos configurables) |
| GET | `/cxc/movimientos` | Listar movimientos con filtros |

### 9.4 Reportes y utilidades
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/reportes/ventas-por-cliente` | Resumen de ventas agrupadas por cliente |
| GET | `/reportes/ventas-por-vendedor` | Resumen de ventas por vendedor |
| GET | `/reportes/documentos-anulados` | Auditoría de documentos anulados |
| GET | `/reportes/overrides-credito` | Auditoría de overrides de límite de crédito |

> Esta tabla es una **propuesta inicial**; la IA puede ajustarla según convenciones REST, pero debe respetar la lógica transaccional de la sección 7 y los flujos de validación de la sección 4.

---

## 10. Checklist de Implementación (para la IA)

### 10.1 Fundamentos
- [ ] Ejecutar el script de la sección 5 en PostgreSQL (idempotente, seguro re-ejecutar).
- [ ] Crear modelos SQLAlchemy/SQLModel que reflejen exactamente las tablas anteriores.
- [ ] Configurar Alembic para migraciones futuras.
- [ ] Crear schemas Pydantic de entrada/salida para cada endpoint de la sección 9.

### 10.2 Maestros y configuración
- [ ] CRUD de `monedas`, `tasas_cambio`.
- [ ] CRUD de `usuarios` con hash de contraseña (bcrypt) y emisión de JWT.
- [ ] CRUD de `puntos_emision` y `secuencias_documentos`.
- [ ] CRUD de `clientes` (con validación de RIF venezolano y campo `es_contribuyente_especial`).
- [ ] CRUD de `vendedores` y `productos`.
- [ ] GET/PUT de `empresa_config` (singleton) y `parametros_sistema`.

### 10.3 Facturación
- [ ] Implementar la lógica transaccional de creación de documento de venta (sección 7.1), incluyendo:
  - Validación de `numero_control` para FACTURA/NC/ND.
  - Validación de `documento_referencia_id` y `motivo` para NC/ND.
  - Validación de stock.
  - Asignación transaccional de correlativo desde `secuencias_documentos` (con `FOR UPDATE`).
  - Validación de límite de crédito con override auditable.
- [ ] Implementar `POST /documentos-ventas/{id}/anular` con regla de anulación segura (sección 7.6).
- [ ] Implementar emisión de NC/ND (sección 7.3).

### 10.4 Cuentas por cobrar
- [ ] Implementar la lógica transaccional de registro de pago/retención (sección 7.2), incluyendo validación de `es_contribuyente_especial` para `RETENCION_IVA`.
- [ ] Implementar anticipos (sección 7.4).
- [ ] Implementar `POST /cxc/aplicaciones/{id}/reversar` (para anular facturas con pagos).

### 10.5 Reportes
- [ ] Implementar estado de cuenta (sección 7.7).
- [ ] Implementar antigüedad de saldos con rangos configurables desde `parametros_sistema` (sección 7.8).
- [ ] Implementar reportes de auditoría (anulados, overrides de crédito).

### 10.6 Endurecimiento y validación
- [ ] Validar **todas** las reglas de negocio de la sección 4 con tests automatizados:
  - Saldo nunca negativo.
  - Tasa congelada.
  - Un solo `es_moneda_local = TRUE` (verificar constraint DB).
  - `numero_control` obligatorio para FACTURA/NC/ND.
  - Anulación segura (no se anula factura pagada sin reversar pagos).
  - Límite de crédito bloqueante con override auditable.
  - RETENCION_IVA solo si cliente es contribuyente especial.
  - Concurrencia en `secuencias_documentos` (`FOR UPDATE`).
- [ ] Tests de concurrencia (dos requests simultáneos al mismo correlativo).
- [ ] Tests de integridad transaccional (rollback si falla cualquier paso).

### 10.7 NO implementar (fuera de alcance)
- [ ] Compras / CxP / Proveedores.
- [ ] Nómina.
- [ ] Contabilidad general completa (solo mantener ganchos: `documento_venta_id`, `movimiento_cxc`).
- [ ] Sincronización real de Shopify.
- [ ] Capa SOAP/XML activa (solo dejar arquitectura desacoplada).

---

## 11. Notas Finales de Contexto (decisiones tomadas durante el diseño)

- El script de la sección 5 es la **versión final** tras corregir un error de "relation already exists" causado por definir tablas dos veces en un borrador anterior; se resolvió con `CREATE TABLE IF NOT EXISTS`, bloques `DO $$` para los `ENUM`, y reordenando las dependencias (monedas → maestros → transaccionales) para no necesitar `ALTER TABLE` posteriores.
- La multimoneda **no se modeló como `VARCHAR`** (decisión temprana descartada) sino como tabla relacional (`monedas` + `tasas_cambio`) para permitir agregar países/monedas sin tocar código y para soportar tasas históricas congeladas por documento.
- Los campos de Shopify se añadieron a `productos` únicamente como preparación para una integración futura, sin lógica de sincronización activa en esta fase.

---

## 12. Changelog y Evoluciones Planificadas

### 12.1 Cambios v1.0 → v2.0 (aplicados en este spec)

**Reglas de negocio añadidas:**
- Regla 10: auditoría multiusuario obligatoria (`creado_por`, `anulado_por`, `registrado_por`, `aplicado_por`).
- Regla 11: número de control fiscal SENIAT separado del correlativo interno.
- Regla 12: multi-punto de emisión con secuencias independientes.
- Regla 13: anulación segura (no se anula factura pagada sin reversar pagos).
- Regla 14: límite de crédito bloqueante con override auditable.
- Regla 15: contribuyente especial (campo `es_contribuyente_especial`).
- Regla 16: antigüedad de saldos configurable desde `parametros_sistema`.
- Regla 17: constraint único DB para "solo una moneda local".

**Tablas nuevas:**
- `empresa_config` (singleton, datos fiscales del emisor).
- `parametros_sistema` (clave-valor JSONB para configuración dinámica).
- `usuarios` (multiusuario con roles y hash de contraseña).
- `puntos_emision` (multi-sucursal / multi-caja).
- `secuencias_documentos` (correlativo por punto + tipo).
- `override_credito_log` (auditoría de overrides de límite de crédito).

**Tablas modificadas:**
- `clientes`: + `es_contribuyente_especial`, + `numero_contribuyente_especial`.
- `vendedores`: + `usuario_id` (relación opcional con usuario del sistema).
- `documentos_ventas`: + `numero_control`, + `punto_emision_id`, + `documento_referencia_id`, + `motivo`, + `creado_por`, + `anulado_por`, + `anulado_en`, + constraint `chk_numero_control`.
- `movimientos_cxc`: + `registrado_por`.
- `aplicaciones_cxc`: + `aplicado_por`, + constraint `chk_aplicacion_distinta` (impide auto-aplicación).

**Índices nuevos:**
- `uq_moneda_local` (parcial, garantiza una sola moneda local).
- `idx_doc_ventas_punto`, `idx_doc_ventas_referencia`.
- `idx_override_cliente`, `idx_override_documento`.

### 12.2 Evoluciones planificadas (fuera del MVP actual)

| # | Evolución | Justificación | Prioridad sugerida |
|---|---|---|---|
| E1 | Diferencial cambiario como movimiento aparte | Cuando se paga en moneda distinta y la tasa cambió, generar movimiento de ajuste para cuadrar contra contabilidad. | Media (cuando se implemente contabilidad) |
| E2 | Tabla `condiciones_pago` con cuotas (30-60-90, 2/10 neto 30) | Hoy `condicion_pago` es ENUM simple. Profit/Odoo soportan reglas de cuotas configurables. | Baja (suficiente con ENUM para MVP) |
| E3 | Descuentos por pronto pago | Funcionalidad de `SACXCR` en Profit. Probablemente no necesario para pequeños comerciantes. | Baja (confirmar con usuario) |
| E4 | Reconciliación bancaria | Vincular pagos CxC con movimientos de banco. Requiere módulo de tesorería. | Media-Alta |
| E5 | Integración contable (asientos automáticos) | Generar asientos en `libro_diario` desde facturas y pagos. Requiere plan de cuentas. | Alta (cuando entre contabilidad) |
| E6 | Multi-impuesto por renglón (IVA + ISLR municipal, etc.) | Hoy solo se contempla IVA. Venezuela tiene impuestos adicionales. | Media |
| E7 | Reportes DUA / SENIAT (libro de ventas, formato XML) | Exportación fiscal. | Alta (cuando se acerque fecha de declaración) |
| E8 | Impresión fiscal directa (impresora de tickets fiscal) | Impresora matricial con driver propio. | Baja (depende del hardware del cliente) |
| E9 | Capa SOAP/XML (estilo Odoo) para integraciones externas | Hoy solo REST. La arquitectura está desacoplada para no bloquearlo. | Baja |
| E10 | Liquidación de comisiones a vendedores | Hoy `vendedores.comision_pct` existe pero no se liquida. | Media |

---

## 13. Resumen de Cambios Aplicados en esta Actualización (v1.0 → v2.0)

Para el equipo de desarrollo, esta es la lista compacta de qué cambió:

1. **DDL (sección 5)**: 6 tablas nuevas (`empresa_config`, `parametros_sistema`, `usuarios`, `puntos_emision`, `secuencias_documentos`, `override_credito_log`), 5 tablas modificadas con nuevos campos, 2 ENUM nuevos (`tipo_punto_emision`, `rol_usuario`), 5 índices nuevos, 2 constraints CHECK nuevos, seeds iniciales para `empresa_config`, `usuarios` y `puntos_emision`.
2. **Reglas de negocio (sección 4)**: 8 reglas nuevas (10 a 17).
3. **Flujos (sección 7)**: 2 sub-flujos nuevos (anulación segura con reverso, validación de límite con override), reglas de NC/ND con referencia obligatoria, número de control obligatorio.
4. **Endpoints (sección 9)**: 4 nuevos grupos (auth/config, documentos, CxC, reportes), ~15 endpoints nuevos.
5. **Checklist (sección 10)**: reorganizada en 7 sub-secciones para guiar la implementación por fases.
6. **Changelog (sección 12)**: trazabilidad de cambios y roadmap de evoluciones.
