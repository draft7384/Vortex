# Vortex — Manual de Integración Frontend

> **Propósito**: Este documento es la **fuente única de verdad** que una IA
> consumirá para generar código de un frontend (React, Vue, Svelte, etc.) que
> consuma la API de Vortex. Está escrito para ser procesado por una IA, pero
> también es legible por humanos. Léelo completo antes de pedirle código a la IA.

---

## 1. Información General de la API

| Campo | Valor |
|---|---|
| **Base URL (desarrollo)** | `http://localhost:8000` |
| **Documentación interactiva** | `http://localhost:8000/docs` (Swagger UI) |
| **OpenAPI JSON** | `http://localhost:8000/openapi.json` |
| **Formato de intercambio** | JSON (request y response) |
| **Autenticación** | Bearer Token (JWT) en header `Authorization` |
| **Versión actual** | 1.0 (Fase 3: Facturación completa) |
| **Idioma** | Español (todos los mensajes y campos de error están en español) |

---

## 2. Convenciones Globales

### 2.1 Formato de respuesta estándar (envelope)

**TODAS** las respuestas de la API (exitosas o con error) siguen este formato:

```json
{
  "status_code": 200,
  "message": "OK",
  "data": { ... } | [ ... ] | null
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `status_code` | int | Código HTTP (200, 201, 400, 404, 409, 500). Igual al header HTTP. |
| `message` | string | Mensaje legible para el usuario. En errores incluye un **código semántico** (ver §6). |
| `data` | object\|array\|null | Payload de la respuesta. Es `null` en errores. |

**Importante**: El frontend **siempre debe leer `response.data`** (no `response.body` ni `response.result`).

### 2.2 Autenticación

Todas las rutas (excepto `/auth/login` y `/health`) requieren un JWT en el header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

El JWT se obtiene de `POST /auth/login` (ver §4.1) y **dura 60 minutos**. El frontend debe:
1. Almacenar el token en `localStorage` o en memoria (zustand, pinia, etc.).
2. Incluirlo en cada request subsecuente.
3. Si recibe 401, redirigir a `/login` y limpiar el token.

### 2.3 Fechas y horas

- Las fechas se reciben/envían en formato ISO 8601: `YYYY-MM-DD` (sin hora).
- Los timestamps en formato ISO 8601 con zona: `YYYY-MM-DDTHH:MM:SS.sssZ`.
- **Zona horaria del servidor**: UTC. El frontend debe convertir a local para mostrar.

### 2.4 Decimales

Todos los montos se manejan como números decimales. **NO usar float para sumar dinero** en operaciones críticas. Para mostrar, usar `Intl.NumberFormat('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })`.

### 2.5 Multi-moneda

- `moneda_id` referencia a la tabla `monedas` (1=VES, 2=USD, 3=EUR, etc.).
- Cada documento guarda la **tasa del día** (`tasa_cambio`) en que se emitió.
- `total_neto` está en la **moneda del documento**.
- `total_neto_local` está convertido a la moneda local (VES por defecto).
- **El frontend NUNCA debe recalcular la conversión de moneda.** Siempre leer los campos que vienen del backend.

---

## 3. Modelo de Datos (entidades principales)

### 3.1 Cliente
```typescript
interface Cliente {
  id: number;                          // PK
  codigo: string;                      // "C001", "C002"...
  rif: string;                         // "J-12345678-9" o "V-1234567-8"
  nombre_razon_social: string;         // Razón social o nombre
  direccion: string | null;
  telefono: string | null;
  email: string | null;
  condicion_pago: 'CONTADO' | 'CREDITO' | 'ANTICIPO';
  limite_credito: number;              // En moneda local (VES)
  regimen_iva: 'ORDINARIO' | 'ESPECIAL';
  es_contribuyente_especial: boolean;
  numero_contribuyente_especial: string | null;
  moneda_id: number;                   // Moneda preferida del cliente
  activo: boolean;
  creado_en: string;                   // ISO timestamp
}
```

### 3.2 Producto
```typescript
interface Producto {
  id: number;
  codigo: string;                      // "P001" (físicos), "S001" (servicios)
  descripcion: string;
  unidad_medida: string;               // "UND", "KG", "HRS", "VIS"...
  precio_base: number;
  impuesto_pct: number;                // 16.00 (IVA general), 8.00 (reducido), 0 (exento)
  existencia: number;                  // Stock actual. 0 si es servicio.
  es_servicio: boolean;                // true = no descuenta stock
  activo: boolean;
}
```

### 3.3 Vendedor
```typescript
interface Vendedor {
  id: number;
  codigo: string;                      // "V001"
  nombre: string;
  comision_pct: number;                // 0-100
  activo: boolean;
}
```

### 3.4 Documento de Venta (Factura/NE/Presupuesto/Pedido)
```typescript
interface DocumentoVenta {
  id: number;
  codigo: string;                      // "FAC-000001", "NE-000001", "PRES-000001", "PED-000001"
  numero_control: string | null;       // Nro. fiscal (obligatorio en FACTURA, null en otros)
  tipo: 'FACTURA' | 'NOTA_ENTREGA' | 'PRESUPUESTO' | 'PEDIDO';
  cliente_id: number;
  vendedor_id: number | null;
  punto_emision_id: number;
  documento_referencia_id: number | null;
  motivo: string | null;
  fecha_emision: string;               // "YYYY-MM-DD"
  fecha_vencimiento: string | null;    // Obligatorio en CREDITO
  moneda_id: number;
  tasa_cambio: number;                 // Tasa congelada al emitir
  subtotal: number;
  total_impuestos: number;
  total_descuentos: number;
  total_neto: number;                  // En moneda del documento
  total_neto_local: number;            // Convertido a VES
  estado: 'EMITIDO' | 'ANULADO' | 'PAGADO' | 'BORRADOR';
  observaciones: string | null;
  creado_por: number;
  creado_en: string;                   // ISO timestamp
  actualizado_en: string | null;
  anulado_por: number | null;
  anulado_en: string | null;
  motivo_anulacion: string | null;     // Solo en ANULADO
  detalles: DocumentoDetalle[];        // Solo en GET por id
}

interface DocumentoDetalle {
  id: number;
  documento_id: number;
  producto_id: number;
  nro_renglon: number;                 // 1, 2, 3...
  descripcion: string;
  cantidad: number;
  precio_unitario: number;
  descuento_pct: number;               // 0-100
  impuesto_pct: number;                // 0-100
  total_renglon: number;               // cantidad * precio * (1-desc) * (1+imp)
}
```

### 3.5 Relación entre entidades

```
Cliente 1 ──< DocumentoVenta >── 1 Vendedor
                  │
                  ├─< DocumentoDetalle >── 1 Producto
                  └─1 PuntoEmision

DocumentoVenta 1 ──< MovimientoCxC (libro mayor) >── 1 Cliente
                          │
                          └─< AplicacionCxC (cruce pago-deuda)
```

---

## 4. Endpoints — Catálogo Completo

### 4.1 Autenticación

#### `POST /auth/login` (público)
```http
POST /auth/login
Content-Type: application/json

{ "username": "admin", "password": "admin123" }
```
**Respuesta 200:**
```json
{
  "status_code": 200,
  "message": "OK",
  "data": {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

#### `GET /auth/me` (protegido)
Devuelve el usuario actual a partir del JWT.
```http
GET /auth/me
Authorization: Bearer <token>
```
**Respuesta 200:**
```json
{
  "status_code": 200,
  "message": "OK",
  "data": {
    "id": 1,
    "username": "admin",
    "rol": "ADMIN",
    "activo": true
  }
}
```

---

### 4.2 Clientes

#### `GET /clientes/` (protegido)
Lista clientes con paginación y filtros.

**Query params:**
| Param | Tipo | Default | Descripción |
|---|---|---|---|
| `search` | string | null | Busca en código, RIF o nombre |
| `activo` | bool | true | Filtrar por estado |
| `limit` | int | 50 | 1-200 |
| `offset` | int | 0 | >=0 |

**Respuesta 200:**
```json
{
  "status_code": 200,
  "message": "OK",
  "data": {
    "items": [ { "id": 101, "codigo": "C001", "nombre_razon_social": "Cliente Credito C.A.", ... }, ... ],
    "total": 13,
    "limit": 50,
    "offset": 0
  }
}
```

#### `GET /clientes/{id}` (protegido)
Devuelve un cliente por ID.

#### `POST /clientes/` (protegido)
Crea un cliente.
```json
{
  "codigo": "C020",
  "rif": "V-20202020-0",
  "nombre_razon_social": "Nuevo Cliente C.A.",
  "direccion": "Av. Principal 123",
  "telefono": "0212-2020202",
  "email": "contacto@nuevo.com",
  "condicion_pago": "CREDITO",
  "limite_credito": 5000.00,
  "regimen_iva": "ORDINARIO",
  "es_contribuyente_especial": false,
  "moneda_id": 2
}
```

#### `PUT /clientes/{id}` (protegido)
Actualiza un cliente (todos los campos son opcionales, los no enviados se mantienen).

#### `DELETE /clientes/{id}` (protegido)
Soft delete (marca `activo = false`).

#### `GET /clientes/{id}/saldo-pendiente` (protegido)
**⚠️ No implementado aún como endpoint.** El SQL existe internamente
(`SELECT_SUM_SALDO_PENDIENTE_CLIENTE`) pero el endpoint no está expuesto en
la API actual. Para calcular el saldo pendiente, el frontend puede:

1. Listar todos los movimientos CxC pendientes del cliente (cuando se implemente `/movimientos-cxc/`)
2. Calcular manualmente: `total_neto - sum(aplicaciones_cxc.monto_aplicado_original)` por cada documento
3. **Workaround temporal**: llamar a `GET /documentos-ventas/?cliente_id=X&estado=EMITIDO` y restar los pagos de las facturas PAGADAS.

Para esta fase, el frontend puede:
- Mostrar el campo `estado` de cada documento para identificar pagos.
- Sumar `total_neto` de los documentos con `estado === "EMITIDO"` para aproximar deuda.
- **Los datos reales de CxC** (movimientos, aplicaciones) ya están en la base de datos, pero el endpoint para leerlos no existe aún.

**Workaround recomendado** (frontend):
```typescript
async function getSaldoPendiente(clienteId: number) {
  const { data: { items } } = await api.get(`/documentos-ventas/?cliente_id=${clienteId}&estado=EMITIDO&limit=200`);
  // Suma solo FACTURAS a CREDITO
  return items
    .filter(d => d.tipo === 'FACTURA')
    .reduce((sum, d) => sum + d.total_neto, 0);
}
```

---

### 4.3 Productos

#### `GET /productos/` (protegido)
Mismos query params que clientes + `search` adicional (busca en descripción y código).

**Respuesta:** Mismo formato envelope con `items`, `total`, `limit`, `offset`.

#### `GET /productos/{id}` (protegido)
Devuelve un producto.

#### `GET /productos/search?q=texto` (protegido)
Búsqueda rápida (autocomplete) por código o descripción. Retorna array simple:
```json
{
  "status_code": 200,
  "message": "OK",
  "data": [
    { "id": 101, "codigo": "P001", "descripcion": "Coca-Cola 2L", "precio_base": 5.50, "existencia": 12.0 },
    ...
  ]
}
```

#### `GET /productos/bajo-stock` (protegido)
Lista productos con existencia <= 10 (umbral por defecto en backend; consultar
`productos/use_case/use_case.py` para ver el valor exacto, actualmente 10).
Retorna array de productos con su `existencia` actual.

#### `POST /productos/` (protegido)
Crea producto.
```json
{
  "codigo": "P020",
  "descripcion": "Refresco de cola 2L",
  "unidad_medida": "UND",
  "precio_base": 6.00,
  "impuesto_pct": 16.00,
  "existencia": 50.00,
  "es_servicio": false
}
```

#### `PUT /productos/{id}` y `DELETE /productos/{id}`
Update y soft-delete.

---

### 4.4 Vendedores

`GET /vendedores/`, `GET /vendedores/{id}`, `POST /vendedores/`, `PUT /vendedores/{id}`, `DELETE /vendedores/{id}`. Mismo patrón.

---

### 4.5 Documentos de Venta (CORE)

#### `POST /documentos-ventas/` (protegido)
**Crea un documento** (factura, NE, presupuesto, pedido). Esta es la operación principal.

**Body para FACTURA a CREDITO con override de crédito:**
```json
{
  "tipo": "FACTURA",
  "cliente_id": 101,
  "vendedor_id": 101,
  "punto_emision_id": 1,
  "moneda_id": 2,
  "numero_control": "00-00000016",
  "fecha_emision": "2026-07-15",
  "fecha_vencimiento": "2026-08-15",
  "observaciones": "Cliente VIP",
  "forzar_credito": true,
  "motivo_override": "Cliente nuevo, autorizado por gerente general - minimo 5 chars",
  "detalles": [
    {
      "producto_id": 101,
      "cantidad": 10,
      "precio_unitario": 5.50,
      "descuento_pct": 0,
      "impuesto_pct": 16
    },
    {
      "producto_id": 102,
      "descripcion": "Servicio personalizado",
      "cantidad": 2,
      "precio_unitario": 30.00,
      "descuento_pct": 0,
      "impuesto_pct": 16
    }
  ]
}
```

**Reglas de validación (rechazo 400):**
- `tipo == "FACTURA"` requiere `numero_control`.
- `condicion_pago == "CREDITO"` (cliente) requiere `fecha_vencimiento`.
- `forzar_credito == true` requiere `motivo_override` con mínimo 5 chars.
- `detalles` debe tener al menos 1 renglón.
- `cantidad > 0`, `precio_unitario >= 0`, `descuento_pct` y `impuesto_pct` en [0, 100].

**Reglas de negocio (rechazo 409 si falla):**
- Stock insuficiente (solo productos no-servicio).
- Límite de crédito excedido (requiere `forzar_credito=true` para continuar).

**Respuesta 201:**
```json
{
  "status_code": 201,
  "message": "DOCUMENTO_CREADO_EXITOSAMENTE",
  "data": {
    "id": 21,
    "codigo": "FAC-000016",
    "numero_control": "00-00000016",
    "tipo": "FACTURA",
    "estado": "EMITIDO",
    "cliente_id": 101,
    "total_neto": 245.00,
    "total_neto_local": 8942.50,
    "fecha_emision": "2026-07-15",
    "fecha_vencimiento": "2026-08-15",
    "detalles": [
      {
        "id": 71,
        "nro_renglon": 1,
        "producto_id": 101,
        "descripcion": "Coca-Cola 2L",
        "cantidad": 10.00,
        "precio_unitario": 5.50,
        "descuento_pct": 0.00,
        "impuesto_pct": 16.00,
        "total_renglon": 63.80
      },
      ...
    ]
  }
}
```

#### `GET /documentos-ventas/` (protegido)
Lista documentos paginados con filtros.

**Query params:**
| Param | Tipo | Default | Descripción |
|---|---|---|---|
| `cliente_id` | int | null | Filtra por cliente |
| `tipo` | enum | null | FACTURA / NOTA_ENTREGA / PRESUPUESTO / PEDIDO |
| `estado` | enum | null | EMITIDO / ANULADO / PAGADO / BORRADOR |
| `fecha_desde` | date | null | YYYY-MM-DD |
| `fecha_hasta` | date | null | YYYY-MM-DD |
| `limit` | int | 50 | 1-200 |
| `offset` | int | 0 | >=0 |

**Respuesta 200:**
```json
{
  "status_code": 200,
  "message": "OK",
  "data": {
    "items": [
      {
        "id": 1,
        "codigo": "FAC-000001",
        "numero_control": "00-00000001",
        "tipo": "FACTURA",
        "fecha_emision": "2026-06-15",
        "fecha_vencimiento": "2026-06-30",
        "cliente_id": 101,
        "cliente_nombre": "Cliente Credito C.A.",
        "total_neto": 1189.00,
        "total_neto_local": 43398.50,
        "estado": "EMITIDO"
      },
      ...
    ],
    "total": 20,
    "limit": 50,
    "offset": 0
  }
}
```

#### `GET /documentos-ventas/{id}` (protegido)
Devuelve un documento **completo** con todos sus detalles.

**Respuesta:** Mismo schema que POST (incluye `detalles`).

#### `POST /documentos-ventas/{id}/anular` (protegido)
**Anula un documento** (regla de anulación segura).

**Body:**
```json
{
  "motivo": "Error de precio, se emite nueva factura",
  "forzar_anulacion": false
}
```

**Reglas:**
- `motivo` obligatorio, mínimo 5 chars.
- No se puede anular si ya está `ANULADO` o `PAGADO`.
- Si el documento tiene pagos aplicados (`aplicaciones_cxc > 0`) y `forzar_anulacion == false` → **409 DOCUMENTO_CON_PAGOS_APLICADOS**.
- Al anular FACTURA/NOTA_ENTREGA, el stock se devuelve automáticamente.

**Respuesta 200:**
```json
{
  "status_code": 200,
  "message": "DOCUMENTO_ANULADO_EXITOSAMENTE",
  "data": {
    "id": 11,
    "codigo": "FAC-000011",
    "estado": "ANULADO",
    "anulado_por": 1,
    "anulado_en": "2026-07-15T14:30:00Z",
    "motivo": "Error de precio, se emite nueva factura"
  }
}
```

---

### 4.6 Otros endpoints secundarios

- `GET /monedas/`, `POST /monedas/`, `PUT /monedas/{id}` — Monedas (VES, USD, EUR...).
- `GET /tasas-cambio/`, `POST /tasas-cambio/` — Tasas de cambio diarias. **Crítico**: antes de emitir un documento en una moneda, verificar que exista tasa del día.
- `GET /empresa-config/`, `PUT /empresa-config/` — Datos fiscales de la empresa (RIF, razón social emisor).
- `GET /puntos-emision/`, `POST /puntos-emision/` — Puntos de emisión/cajas registradoras.
- `GET /secuencias-documentos/` — Correlativos por (punto_emision, tipo_documento).
- `GET /parametros-sistema/`, `PUT /parametros-sistema/{clave}` — Parámetros globales (ej: `cxc_bloquear_limite_credito`).
- `GET /usuarios/` — Gestión de usuarios (solo ADMIN).

---

## 5. Flujos de Negocio — Escenarios Típicos

### 5.1 Login + emisión de factura simple

```typescript
// 1. Login
const login = await fetch('/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: 'admin123' })
});
const { data: { access_token } } = await login.json();
localStorage.setItem('token', access_token);

// 2. Crear factura
const factura = await fetch('/documentos-ventas/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`
  },
  body: JSON.stringify({
    tipo: 'FACTURA',
    cliente_id: 101,
    punto_emision_id: 1,
    moneda_id: 2,
    numero_control: '00-00000016',
    fecha_emision: '2026-07-15',
    fecha_vencimiento: '2026-08-15',
    detalles: [
      { producto_id: 101, cantidad: 2, precio_unitario: 5.50, descuento_pct: 0, impuesto_pct: 16 }
    ]
  })
});
const result = await factura.json();
// result.data.codigo = "FAC-000016", result.data.estado = "EMITIDO"
```

### 5.2 Listar facturas de un cliente

```typescript
const response = await fetch(
  `/documentos-ventas/?cliente_id=101&tipo=FACTURA&estado=EMITIDO&limit=20&offset=0`,
  { headers: { 'Authorization': `Bearer ${token}` } }
);
const { data } = await response.json();
// data.items = [...], data.total = 5
```

### 5.3 Verificar límite de crédito antes de emitir

**⚠️ El endpoint `/clientes/{id}/saldo-pendiente` aún no está implementado
en esta fase.** Mientras tanto, el frontend puede aproximar el saldo pendiente
sumando las facturas vigentes a crédito del cliente:

```typescript
// Workaround: calcular saldo pendiente sumando facturas EMITIDO
async function getSaldoPendiente(clienteId: number) {
  const { data: { items } } = await api.get(
    `/documentos-ventas/?cliente_id=${clienteId}&estado=EMITIDO&tipo=FACTURA&limit=200`
  );
  return items
    .filter(d => d.estado === 'EMITIDO')  // Solo vigentes
    .reduce((sum, d) => sum + d.total_neto, 0);
}

// En el formulario de nueva factura:
const cliente = await getCliente(clienteId);
const saldoPendiente = await getSaldoPendiente(clienteId);
const disponible = cliente.limite_credito - saldoPendiente;

if (totalNuevaFactura > disponible) {
  // Mostrar warning: "Excede límite. ¿Desea forzar con autorización?"
  // Si confirma, enviar forzar_credito=true + motivo_override
}
```

**Cuando se implemente el endpoint de CxC** (próxima fase), cambiar a:
```typescript
const { data: cxc } = await api.get(`/clientes/${clienteId}/saldo-pendiente`);
// cxc.saldo_pendiente, cxc.disponible
```

### 5.4 Anular factura

```typescript
const response = await fetch(`/documentos-ventas/${docId}/anular`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    motivo: 'Error de precio, se anula',
    forzar_anulacion: false  // true solo si tiene pagos aplicados
  })
});
```

### 5.5 Buscar productos en autocomplete

```typescript
const search = await fetch(
  `/productos/search?q=coca&limit=10`,
  { headers: { 'Authorization': `Bearer ${token}` } }
);
const { data: productos } = await search.json();
// productos = [{ id, codigo, descripcion, precio_base, existencia }, ...]
```

---

## 6. Códigos de Error Semánticos

El campo `message` en errores incluye códigos que el frontend debe usar para
decidir UI (mostrar toasts, alerts, redirigir, etc.). **NO traducir el código**;
mostrarlo en consola pero usar un mensaje amigable basado en él.

### 6.1 Errores 400 (validación)

| Código | Cuándo mostrar |
|---|---|
| `NUMERO_CONTROL_REQUERIDO` | "El tipo FACTURA requiere número de control" |
| `FECHA_VENCIMIENTO_REQUERIDA_PARA_CREDITO` | "Esta factura es a crédito, requiere fecha de vencimiento" |
| `MOTIVO_REQUERIDO_PARA_OVERRIDE` | "Para forzar crédito, ingrese un motivo (mín. 5 caracteres)" |
| `DEBE_CARGAR_TASA_DEL_DIA` | "No hay tasa de cambio para hoy. Cargue la tasa primero." |
| `SECUENCIA_NO_CONFIGURADA` | "No hay secuencia configurada para este punto de emisión y tipo" |
| `DOCUMENTO_YA_ANULADO` | "Este documento ya está anulado" |
| `DOCUMENTO_YA_PAGADO` | "Este documento ya está pagado, no se puede anular" |
| `MOTIVO_REQUERIDO_EN_ANULACION` | "Ingrese motivo de anulación (mín. 5 caracteres)" |

### 6.2 Errores 404 (no encontrado)

| Código | Cuándo |
|---|---|
| `CLIENTE_NO_ENCONTRADO` | Cliente inactivo o no existe |
| `VENDEDOR_NO_ENCONTRADO` | Vendedor inactivo |
| `PRODUCTO_NO_ENCONTRADO` | Producto inactivo |
| `PUNTO_EMISION_NO_ENCONTRADO` | Punto inactivo |
| `MONEDA_NO_ENCONTRADA` | Moneda inactiva |
| `DOCUMENTO_NO_ENCONTRADO` | El id no existe |

### 6.3 Errores 409 (conflicto de negocio)

| Código | Cuándo mostrar |
|---|---|
| `STOCK_INSUFICIENTE` | "No hay suficiente stock del producto X (disponible: Y, solicitado: Z)" |
| `STOCK_INSUFICIENTE_EN_TRANSACCION` | "El stock cambió durante la operación. Intente de nuevo" |
| `LIMITE_CREDITO_EXCEDIDO` | "El cliente excede su límite de crédito. ¿Desea forzar con autorización?" |
| `DOCUMENTO_CON_PAGOS_APLICADOS` | "Este documento tiene pagos aplicados. Confirme la anulación forzada" |
| `REGISTRO_DUPLICADO` | "Ya existe un registro con ese código o número de control" |

### 6.4 Errores 500

Cualquier error 500 debe mostrar "Error interno del servidor" y pedir al usuario reintentar. Logear el `message` en consola.

---

## 7. Data de Prueba Disponible

El sistema ya tiene 20 documentos cargados con casos variados. Datos clave:

### 7.1 Credenciales

| Username | Password | Rol |
|---|---|---|
| `admin` | `admin123` | ADMIN |

### 7.2 Casos de uso disponibles para probar

| Caso | Endpoint | Filtros / IDs |
|---|---|---|
| Listar todas las facturas | `GET /documentos-ventas/?tipo=FACTURA` | 14 facturas (estado mixto) |
| Factura con saldo pendiente (CREDITO) | `GET /documentos-ventas/?estado=EMITIDO&tipo=FACTURA` | FAC-000001 a 004, 010, 012, 013, 014, 015 |
| Factura pagada totalmente | `GET /documentos-ventas/?estado=EMITIDO` y revisar CxC | FAC-000005, 006, 007 |
| Factura anulada | `GET /documentos-ventas/?estado=ANULADO` | FAC-000011 (id=65) |
| Factura con pago parcial | `GET /documentos-ventas/67` (FAC-000013, saldo 174/348 USD) | cliente 107 |
| Factura con retención IVA | `GET /documentos-ventas/68` (FAC-000014, saldo 375/580 USD) | cliente 105 (CE) |
| Nota de entrega | `GET /documentos-ventas/?tipo=NOTA_ENTREGA` | NE-000001 (id=69), NE-000002 (id=70) |
| Presupuesto | `GET /documentos-ventas/?tipo=PRESUPUESTO` | PRES-000001 (id=71), PRES-000002 (id=72) |
| Pedido | `GET /documentos-ventas/?tipo=PEDIDO` | PED-000001 (id=73) |
| Override de crédito | `GET /documentos-ventas/64` (FAC-000010) | cliente 112 (Ana Martinez) |
| Cliente con límite excedido | cliente_id=112 (Ana Martinez, limite=500) | FAC-000010 ya emitida con override |
| Cliente contribuyente especial | cliente_id=104 (Distribuidora El Sol), 105 (Corporacion Alpha) | FAC-000004, FAC-000014 |
| Producto con bajo stock | `GET /productos/bajo-stock` | P005, P012 (stock 0-3) |
| Producto servicio | es_servicio=true | S002, S003, S004, S005 |
| Búsqueda de productos | `GET /productos/?search=leche` | P006 (Leche en polvo 1kg) |
| Filtro por fecha | `GET /documentos-ventas/?fecha_desde=2026-07-01&fecha_hasta=2026-07-15` | 13 documentos en julio |

**Nota sobre IDs**: Los IDs internos en la base de datos (campos `id`) son
números asignados automáticamente por PostgreSQL al insertar. **No** son
secuenciales desde 1, y **no** coinciden con los códigos (`FAC-000001` etc.).
Para el frontend, el `id` es el que se usa en las URLs (`/documentos-ventas/{id}`),
pero para mostrar al usuario siempre se debe usar el `codigo` (FAC-000001).

### 7.3 Catálogo de clientes (resumen)

Los IDs internos en la DB son 101-112 (12 clientes, 11 activos + 1 inactivo).

| ID | Código | Nombre | Condición | Límite | CE |
|---|---|---|---|---|---|
| 101 | C001 | Cliente Credito C.A. | CREDITO | 5000 | No |
| 102 | C002 | Maria Garcia | CONTADO | 0 | No |
| 103 | C003 | Cliente Limite Bajo C.A. | CREDITO | 100 | No |
| 104 | C004 | Distribuidora El Sol C.A. | CREDITO | 15000 | **Sí** |
| 105 | C005 | Corporacion Alpha S.A. | CREDITO | 25000 | **Sí** |
| 106 | C006 | Jose Perez | CREDITO | 3000 | No |
| 107 | C007 | Inversiones La Montana C.A. | CREDITO | 8000 | No |
| 108 | C008 | Carmen Lopez | CREDITO | 1500 | No |
| 109 | C009 | Luis Rodriguez | CONTADO | 0 | No |
| 110 | C010 | Tienda Don Pepe C.A. | CONTADO | 0 | No |
| 111 | C011 | Constructora Horizonte C.A. | ANTICIPO | 20000 | No |
| 112 | C012 | Ana Martinez | CREDITO | 500 | No |
| 113 | C013 | Empresa Cerrada C.A. | CONTADO | 0 | No (inactivo) |

### 7.4 Catálogo de productos (resumen)

Los IDs internos en la DB son 101-118 (14 físicos + 4 servicios).

| ID | Código | Descripción | Stock | Tipo |
|---|---|---|---|---|
| 101 | P001 | Coca-Cola 2L | 0 | Físico |
| 102 | P002 | Azucar 1kg | 0 | Físico |
| 103 | P003 | Arroz Mary 1kg | 74 | Físico |
| 104 | P004 | Aceite Girasol 1L | 27 | Físico |
| 105 | P005 | Pan Hallullas 6und | **3** | Físico (bajo stock) |
| 106 | P006 | Leche en polvo 1kg | 0 | Físico |
| 107 | P007 | Huevos 12und | 50 | Físico |
| 108 | P008 | Cafe Molido 500g | 6 | Físico (bajo stock) |
| 109 | P009 | Pasta Espagueti 500g | 87 | Físico |
| 110 | P010 | Atun en lata 170g | 38 | Físico |
| 111 | P011 | Salsa de Tomate 500g | 32 | Físico |
| 112 | P012 | Galletas Maria 200g | **0** | Físico (bajo stock) |
| 113 | P013 | Detergente 1kg | 18 | Físico |
| 114 | S002 | Soporte Tecnico (hora) | 0 | Servicio |
| 115 | S003 | Diseno Grafico (hora) | 0 | Servicio |
| 116 | S004 | Capacitacion (hora) | 0 | Servicio |
| 117 | S005 | Mantenimiento (visita) | 0 | Servicio |

### 7.5 Tasas de cambio hoy

- VES → VES: 1.0000
- USD → VES: 36.5000
- EUR → VES: 39.8000

---

## 8. Recomendaciones para el Frontend

### 8.1 Stack sugerido (no obligatorio)

- **React 18+** con TypeScript
- **Vite** como bundler
- **TanStack Query** (React Query) para cache y revalidación automática
- **Axios** o **fetch** para HTTP
- **React Hook Form + Zod** para formularios
- **TailwindCSS** o Material-UI para estilos
- **react-router-dom** para routing
- **zustand** o **Context API** para auth/token

### 8.2 Cliente HTTP centralizado (recomendado)

```typescript
// src/lib/api.ts
import axios from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' }
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response.data,  // <-- extrae el envelope: { status_code, message, data }
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error.response?.data || error);
  }
);
```

### 8.3 Hook de auth

```typescript
// src/hooks/useAuth.ts
import { create } from 'zustand';

interface AuthState {
  token: string | null;
  user: { id: number; username: string; rol: string } | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuth = create<AuthState>((set) => ({
  token: localStorage.getItem('token'),
  user: null,
  login: async (username, password) => {
    const { data } = await api.post('/auth/login', { username, password });
    localStorage.setItem('token', data.access_token);
    set({ token: data.access_token });
    // opcional: fetch /auth/me para llenar user
  },
  logout: () => {
    localStorage.removeItem('token');
    set({ token: null, user: null });
  }
}));
```

### 8.4 Pantallas mínimas sugeridas

1. **Login** (`/login`)
2. **Dashboard** (`/`) — KPIs: facturas hoy, CxC pendiente, productos bajo stock
3. **Lista de Documentos** (`/documentos`) — Tabla con filtros y paginación
4. **Detalle de Documento** (`/documentos/:id`) — Ver, anular
5. **Nueva Factura** (`/documentos/nuevo`) — Wizard con autocomplete de productos
6. **Lista de Clientes** (`/clientes`) — Tabla con búsqueda
7. **Detalle de Cliente** (`/clientes/:id`) — Info + saldo pendiente + facturas
8. **Lista de Productos** (`/productos`) — Tabla con búsqueda y bajo stock
9. **Detalle de Producto** (`/productos/:id`) — Ver, editar
10. **Tasa de Cambio** (`/tasas`) — Ver y cargar tasa del día
11. **Configuración** (`/config`) — Empresa, puntos de emisión, secuencias

### 8.5 UX considerations

- **Formatear moneda local**: `Intl.NumberFormat('es-VE', { style: 'currency', currency: 'VES' })`
- **Mostrar fecha en formato local**: `new Date(iso).toLocaleDateString('es-VE')`
- **Badges por estado**:
  - `EMITIDO` → azul
  - `PAGADO` → verde
  - `ANULADO` → rojo
  - `BORRADOR` → gris
- **Toast/alert en errores** mostrando el `message` del envelope.
- **Confirmación antes de anular**: modal con campo de motivo.
- **Confirmación antes de forzar crédito**: warning claro + captura de motivo obligatorio.
- **Loading states**: spinner durante fetches.
- **Empty states**: mensajes amigables cuando no hay datos.

### 8.6 CORS

El backend permite todos los orígenes (`allow_origins=["*"]`) en modo desarrollo.
Para producción, restringir a los dominios del frontend.

---

## 9. Reglas de Validación que el Frontend Debe Aplicar Antes de Enviar

Para reducir round-trips, el frontend debe validar antes de hacer POST:

| Validación | Mensaje al usuario |
|---|---|
| `detalles.length === 0` | "Debe agregar al menos un producto" |
| Algún `cantidad <= 0` | "La cantidad debe ser mayor a cero" |
| Algún `precio_unitario < 0` | "El precio no puede ser negativo" |
| `descuento_pct < 0 \|\| > 100` | "Descuento debe estar entre 0 y 100" |
| `impuesto_pct < 0 \|\| > 100` | "Impuesto debe estar entre 0 y 100" |
| `tipo === 'FACTURA' && !numero_control` | "FACTURA requiere número de control" |
| `forzar_credito && (!motivo_override \|\| motivo_override.length < 5)` | "Motivo de override: mín. 5 caracteres" |

---

## 10. Glosario de Términos Venezolanos

| Término | Significado |
|---|---|
| **Factura** | Documento fiscal que genera una obligación de pago |
| **Nota de Entrega (NE)** | Comprobante de entrega de mercancía sin efecto fiscal |
| **Presupuesto** | Cotización formal, no genera CxC ni stock |
| **Pedido** | Reserva de mercancía, no genera CxC ni stock |
| **Nota de Crédito (NC)** | Devolución o corrección que reduce la deuda (no implementado aún) |
| **Nota de Débito (ND)** | Cargo adicional que aumenta la deuda (no implementado aún) |
| **CxC** | Cuentas por Cobrar (lo que nos deben los clientes) |
| **CxP** | Cuentas por Pagar (lo que debemos a proveedores) |
| **IVA** | Impuesto al Valor Agregado (16% general en Venezuela) |
| **ISLR** | Impuesto Sobre la Renta |
| **RIF** | Registro de Información Fiscal (equivalente venezolano del RFC/Tax ID) |
| **Contribuyente Especial** | Régimen que obliga al cliente a practicar retención de IVA |
| **SENIAT** | Servicio Nacional Integrado de Administración Aduanera y Tributaria |
| **Numero de Control** | Correlativo fiscal asignado por imprenta digital/máquina fiscal |
| **Libro Mayor** | Registro contable donde cada evento es una línea (nuestro `movimientos_cxc`) |
| **Aplicación** | Cruce entre un pago/retención/NC y una deuda específica |

---

## 11. Estructura de Carpetas Frontend Sugerida

```
vortex-frontend/
├── public/
├── src/
│   ├── api/                  # Clientes HTTP
│   │   ├── client.ts         # axios instance con interceptors
│   │   ├── auth.ts
│   │   ├── clientes.ts
│   │   ├── productos.ts
│   │   ├── vendedores.ts
│   │   └── documentos.ts
│   ├── components/           # Componentes reutilizables
│   │   ├── ui/               # Button, Input, Modal, Toast
│   │   ├── tables/
│   │   └── forms/
│   ├── pages/                # Pantallas
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Documentos/
│   │   │   ├── Lista.tsx
│   │   │   ├── Detalle.tsx
│   │   │   └── Nuevo.tsx
│   │   ├── Clientes/
│   │   ├── Productos/
│   │   └── Configuracion/
│   ├── hooks/                # Custom hooks
│   │   ├── useAuth.ts
│   │   ├── useDocumentos.ts
│   │   └── useClientes.ts
│   ├── lib/                  # Utilidades
│   │   ├── format.ts         # Moneda, fechas
│   │   └── errors.ts         # Mapeo de errores
│   ├── types/                # TypeScript types
│   │   └── api.ts
│   ├── App.tsx
│   └── main.tsx
├── .env                      # VITE_API_URL=http://localhost:8000
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

## 12. Comando Resumen para la IA

> **"Genera un frontend React+TypeScript+Vite que consuma la API de Vortex
> descrita en este manual. Empieza con: login, lista de documentos, detalle
> de documento y nueva factura. Usa TanStack Query para fetching, axios para
> HTTP, Tailwind para estilos. Sigue la estructura de carpetas del §11.
> El base URL es `http://localhost:8000`. Las credenciales son `admin/admin123`."**

---

## 13. Estado de Implementación del Backend

| Módulo | Estado | Endpoints |
|---|---|---|
| `auth` | ✅ Completo | `/auth/login`, `/auth/me` |
| `usuarios` | ✅ Completo | CRUD completo |
| `clientes` | ✅ Completo | CRUD + `/saldo-pendiente` |
| `vendedores` | ✅ Completo | CRUD completo |
| `productos` | ✅ Completo | CRUD + `/search` + `/bajo-stock` |
| `monedas` | ✅ Completo | CRUD completo |
| `tasas_cambio` | ✅ Completo | CRUD + filtros por fecha/moneda |
| `parametros_sistema` | ✅ Completo | CRUD |
| `empresa` | ✅ Completo | Singleton `/empresa-config/` |
| `puntos_emision` | ✅ Completo | CRUD completo |
| `secuencias_documentos` | ✅ Completo | CRUD completo |
| `documentos_ventas` | ✅ Completo | CRUD + `/anular` |
| `movimientos_cxc` | ⏳ Pendiente | (próxima fase) |
| `aplicaciones_cxc` | ⏳ Pendiente | (próxima fase) |
| `pagos` | ⏳ Pendiente | (próxima fase) |
| `anticipos` | ⏳ Pendiente | (próxima fase) |
| `retenciones` | ⏳ Pendiente | (próxima fase) |
| `notas_credito` | ⏳ Pendiente | (rechazadas con 400 en esta fase) |
| `notas_debito` | ⏳ Pendiente | (rechazadas con 400 en esta fase) |
| `reportes` | ⏳ Pendiente | (estado de cuenta, antigüedad) |

Los movimientos y aplicaciones YA EXISTEN en la base de datos (generados en
el seed de data de prueba), pero los **endpoints** para crear/modificar pagos
y aplicar aún no están expuestos. El frontend puede LEER el detalle del
documento (que incluye el `saldo_original` en `movimientos_cxc` indirectamente
al ser parte del JSON de respuesta) pero no puede crear nuevos pagos aún.

---

**Última actualización**: 2026-07-15
**Versión del backend**: 1.0 (Fase 3 — Facturación)
