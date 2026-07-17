# Arquitectura del Proyecto: Vortex Facturación & CxC

> **Propósito:** Definir la estructura de carpetas, convenciones de nombres y patrones de diseño que seguirá el backend FastAPI del módulo de Facturación y CxC. Esta arquitectura prioriza **escalabilidad**, **mantenibilidad** y **claridad** sobre frameworks mágicos.

---

## 1. Principios de Diseño

1. **Escalabilidad por módulos:** cada dominio de negocio (Clientes, Productos, Facturas, CxC, etc.) es un **APIRouter independiente** que se enchufa en la app principal. Agregar un nuevo módulo no requiere tocar los existentes.
2. **SQL crudo (no ORM):** todas las queries se escriben explícitamente en archivos `statement/*.py` como constantes SQL, y se ejecutan vía `text(...)` de SQLAlchemy. Esto da control total, transparencia fiscal y cero "magia" del ORM.
3. **Separación de responsabilidades estricta:** cada archivo tiene una sola razón para cambiar.
4. **Respuestas estandarizadas:** TODO endpoint retorna la misma estructura JSON: `{ status_code, message, data }`.
5. **Async-first:** toda la pila es asíncrona (`AsyncSession`, `asyncpg`).

---

## 2. Estructura de Directorios

```
Vortex/
├── app.py                          # FastAPI app principal + registro de routers
├── main.py                         # Entry point: uvicorn main:app
├── requirements.txt
├── .env                            # Variables de entorno (no commiteado)
├── .env.example                    # Plantilla de .env
├── .gitignore
├── schema.sql                      # DDL de la base de datos (ya creado)
├── facturacion-cxc-spec.md         # Especificación funcional
├── arquitectura.md                 # Este documento
│
├── conex/                          # Capa de conexión a base de datos
│   ├── __init__.py
│   └── conn.py                     # Engine async, sesión, dependency
│
├── core/                           # Configuración transversal
│   ├── __init__.py
│   ├── config.py                   # Pydantic Settings (lee .env)
│   └── responses.py                # StandardResponse, helpers de respuesta
│
├── apirouters/                     # Módulos de negocio (uno por dominio)
│   ├── __init__.py
│   ├── auth/                       # Login, JWT, refresh token
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── api.py              # Endpoints del módulo auth
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── models.py           # LoginRequest, TokenResponse, etc.
│   │   ├── statement/
│   │   │   ├── __init__.py
│   │   │   └── statement.py        # SELECT_USUARIO, INSERT_USUARIO, etc.
│   │   └── use_case/
│   │       ├── __init__.py
│   │       └── use_case.py         # Lógica de login, refresh, etc.
│   │
│   ├── empresa/                    # Datos fiscales del emisor
│   │   ├── api/api.py
│   │   ├── models/models.py
│   │   ├── statement/statement.py
│   │   └── use_case/use_case.py
│   │
│   ├── monedas/                    # Maestros multimoneda
│   ├── tasas_cambio/
│   ├── parametros_sistema/
│   ├── usuarios/                   # CRUD de usuarios (admin)
│   ├── puntos_emision/             # Multi-sucursal / multi-caja
│   ├── secuencias_documentos/
│   ├── clientes/                   # CRUD de clientes
│   ├── vendedores/
│   ├── productos/                  # Productos y servicios
│   ├── documentos_ventas/          # Facturas, NC, ND, notas de entrega
│   ├── movimientos_cxc/            # Libro mayor de CxC
│   ├── aplicaciones_cxc/           # Cruces pago↔deuda
│   ├── pagos/                      # Endpoint compuesto de pago
│   ├── anticipos/
│   ├── retenciones/                # IVA / ISLR
│   ├── reportes/                   # Estado de cuenta, antigüedad, etc.
│   └── override_credito_log/
│
└── alembic/                        # Migraciones (Fase 0.b)
    ├── versions/
    ├── env.py
    └── script.py.mako
```

---

## 3. Convenciones de Nombramiento

### 3.1 Clases
- **API:** `<NombreModulo>API` — encapsula el `APIRouter` y los métodos HTTP.
  - Ej: `ClientesAPI`, `ProductosAPI`, `DocumentosVentasAPI`.
- **Use Case:** `<NombreModulo>UseCase` — encapsula la lógica de negocio.
  - Ej: `ClientesUseCase`, `ProductosUseCase`, `CxCPagosUseCase`.
- **Models (Pydantic):** sufijo semántico:
  - `*CreateRequest` — entrada para POST.
  - `*UpdateRequest` — entrada para PUT/PATCH.
  - `*Response` — salida individual.
  - `*ListResponse` — salida paginada/lista.
  - `*SearchRequest` — entrada para búsqueda por keyword.

### 3.2 Constantes SQL
- `MAYÚSCULAS_CON_GUION_BAJO`, una por sentencia, sin importar el caso de uso.
- Nombres descriptivos: `INSERT_CLIENTE`, `SELECT_CLIENTE_BY_ID`, `UPDATE_CLIENTE`, `DELETE_CLIENTE`, `SEARCH_CLIENTES_BY_KEYWORD`.

### 3.3 Métodos
- En `api.py`: verbos HTTP (`create`, `get`, `get_by_id`, `update`, `delete`, `search`).
- En `use_case.py`: mismos verbos, sin prefijo HTTP (`create_cliente`, `get_clientes`, etc.).

---

## 4. Formato Estándar de Respuesta

**TODAS** las respuestas del API (exitosas o de error) siguen este contrato:

```json
{
  "status_code": 200,
  "message": "Cliente creado exitosamente",
  "data": { ... }
}
```

Para errores:
```json
{
  "status_code": 409,
  "message": "LIMITE_CREDITO_EXCEDIDO: el cliente supera el límite configurado",
  "data": null
}
```

Implementado en `core/responses.py` con una función helper:

```python
def standard_response(status_code: int, message: str, data: Any = None) -> dict:
    return {"status_code": status_code, "message": message, "data": data}
```

---

## 5. Anatomía de un Módulo (4 archivos)

Tomemos como ejemplo el módulo `clientes`:

### 5.1 `clientes/api/api.py` — Capa HTTP

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from conex.conn import get_db
from core.responses import standard_response
from apirouters.clientes.models.models import (
    ClienteCreateRequest, ClienteUpdateRequest
)
from apirouters.clientes.use_case.use_case import ClientesUseCase


class ClientesAPI:
    router = APIRouter(prefix="/clientes", tags=["Clientes"])

    @staticmethod
    @router.post("/", status_code=201)
    async def create_cliente(
        data: ClienteCreateRequest,
        db: AsyncSession = Depends(get_db)
    ):
        result = await ClientesUseCase(db).create_cliente(data)
        return result

    @staticmethod
    @router.get("/")
    async def get_clientes(
        limit: int = 50,
        offset: int = 0,
        db: AsyncSession = Depends(get_db)
    ):
        result = await ClientesUseCase(db).get_clientes(limit, offset)
        return result

    @staticmethod
    @router.get("/search")
    async def search_clientes(
        keyword: str,
        db: AsyncSession = Depends(get_db)
    ):
        result = await ClientesUseCase(db).search_clientes(keyword)
        return result

    @staticmethod
    @router.get("/{cliente_id}")
    async def get_cliente_by_id(
        cliente_id: int,
        db: AsyncSession = Depends(get_db)
    ):
        result = await ClientesUseCase(db).get_cliente_by_id(cliente_id)
        return result

    @staticmethod
    @router.put("/{cliente_id}")
    async def update_cliente(
        cliente_id: int,
        data: ClienteUpdateRequest,
        db: AsyncSession = Depends(get_db)
    ):
        result = await ClientesUseCase(db).update_cliente(cliente_id, data)
        return result

    @staticmethod
    @router.delete("/{cliente_id}")
    async def delete_cliente(
        cliente_id: int,
        db: AsyncSession = Depends(get_db)
    ):
        result = await ClientesUseCase(db).delete_cliente(cliente_id)
        return result
```

### 5.2 `clientes/models/models.py` — Schemas Pydantic

```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class ClienteCreateRequest(BaseModel):
    codigo: str = Field(..., max_length=20)
    rif: str = Field(..., max_length=20)
    nombre_razon_social: str = Field(..., max_length=255)
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    condicion_pago: str = "CONTADO"
    limite_credito: float = 0.00
    regimen_iva: str = "ORDINARIO"
    es_contribuyente_especial: bool = False
    numero_contribuyente_especial: Optional[str] = None
    moneda_id: Optional[int] = None


class ClienteUpdateRequest(BaseModel):
    codigo: Optional[str] = None
    rif: Optional[str] = None
    nombre_razon_social: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    condicion_pago: Optional[str] = None
    limite_credito: Optional[float] = None
    regimen_iva: Optional[str] = None
    es_contribuyente_especial: Optional[bool] = None
    numero_contribuyente_especial: Optional[str] = None
    moneda_id: Optional[int] = None
    activo: Optional[bool] = None


class ClienteResponse(BaseModel):
    id: int
    codigo: str
    rif: str
    nombre_razon_social: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    condicion_pago: str
    limite_credito: float
    regimen_iva: str
    es_contribuyente_especial: bool
    numero_contribuyente_especial: Optional[str] = None
    moneda_id: Optional[int] = None
    activo: bool
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None
```

### 5.3 `clientes/statement/statement.py` — SQL crudo

```python
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
RETURNING id, codigo, rif, nombre_razon_social, condicion_pago, limite_credito,
          es_contribuyente_especial, activo, creado_en;
"""

SELECT_CLIENTE_BY_ID = """
SELECT id, codigo, rif, nombre_razon_social, direccion, telefono, email,
       condicion_pago, limite_credito, regimen_iva,
       es_contribuyente_especial, numero_contribuyente_especial, moneda_id,
       activo, creado_en, actualizado_en
FROM clientes
WHERE id = :cliente_id AND activo = TRUE;
"""

SELECT_CLIENTES_PAGINATED = """
SELECT id, codigo, rif, nombre_razon_social, condicion_pago, limite_credito,
       es_contribuyente_especial, activo
FROM clientes
WHERE activo = TRUE
ORDER BY nombre_razon_social ASC
LIMIT :limit OFFSET :offset;
"""

SEARCH_CLIENTES_BY_KEYWORD = """
SELECT id, codigo, rif, nombre_razon_social, condicion_pago, limite_credito
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

UPDATE_CLIENTE = """
UPDATE clientes SET
    codigo = COALESCE(:codigo, codigo),
    rif = COALESCE(:rif, rif),
    nombre_razon_social = COALESCE(:nombre_razon_social, nombre_razon_social),
    direccion = COALESCE(:direccion, direccion),
    telefono = COALESCE(:telefono, telefono),
    email = COALESCE(:email, email),
    condicion_pago = COALESCE(:condicion_pago, condicion_pago),
    limite_credito = COALESCE(:limite_credito, limite_credito),
    regimen_iva = COALESCE(:regimen_iva, regimen_iva),
    es_contribuyente_especial = COALESCE(:es_contribuyente_especial, es_contribuyente_especial),
    numero_contribuyente_especial = COALESCE(:numero_contribuyente_especial, numero_contribuyente_especial),
    moneda_id = COALESCE(:moneda_id, moneda_id),
    activo = COALESCE(:activo, activo),
    actualizado_en = CURRENT_TIMESTAMP
WHERE id = :cliente_id
RETURNING id, codigo, rif, nombre_razon_social, activo, actualizado_en;
"""

DELETE_CLIENTE = """
UPDATE clientes
SET activo = FALSE, actualizado_en = CURRENT_TIMESTAMP
WHERE id = :cliente_id
RETURNING id, codigo;
"""

SELECT_SUM_SALDO_PENDIENTE_CLIENTE = """
SELECT COALESCE(SUM(saldo_original), 0) AS total_pendiente
FROM movimientos_cxc
WHERE cliente_id = :cliente_id AND saldo_original > 0;
"""
```

### 5.4 `clientes/use_case/use_case.py` — Lógica de negocio

```python
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from core.responses import standard_response
from apirouters.clientes.models.models import (
    ClienteCreateRequest, ClienteUpdateRequest
)
from apirouters.clientes.statement import statement as st


class ClientesUseCase:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_cliente(self, data: ClienteCreateRequest) -> dict:
        try:
            result = await self.db.execute(
                text(st.INSERT_CLIENTE),
                data.model_dump()
            )
            row = result.mappings().first()
            await self.db.commit()
            return standard_response(201, "Cliente creado exitosamente", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error al crear cliente: {str(e)}", None)

    async def get_clientes(self, limit: int = 50, offset: int = 0) -> dict:
        try:
            result = await self.db.execute(
                text(st.SELECT_CLIENTES_PAGINATED),
                {"limit": limit, "offset": offset}
            )
            rows = [dict(r) for r in result.mappings().all()]
            return standard_response(200, "Listado de clientes", rows)
        except Exception as e:
            return standard_response(500, f"Error al listar clientes: {str(e)}", None)

    async def get_cliente_by_id(self, cliente_id: int) -> dict:
        try:
            result = await self.db.execute(
                text(st.SELECT_CLIENTE_BY_ID),
                {"cliente_id": cliente_id}
            )
            row = result.mappings().first()
            if not row:
                return standard_response(404, "Cliente no encontrado", None)
            return standard_response(200, "Cliente encontrado", dict(row))
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def search_clientes(self, keyword: str) -> dict:
        try:
            result = await self.db.execute(
                text(st.SEARCH_CLIENTES_BY_KEYWORD),
                {"keyword": f"%{keyword}%"}
            )
            rows = [dict(r) for r in result.mappings().all()]
            return standard_response(200, f"{len(rows)} resultados", rows)
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def update_cliente(self, cliente_id: int, data: ClienteUpdateRequest) -> dict:
        try:
            payload = data.model_dump(exclude_unset=True)
            payload["cliente_id"] = cliente_id
            result = await self.db.execute(text(st.UPDATE_CLIENTE), payload)
            row = result.mappings().first()
            if not row:
                return standard_response(404, "Cliente no encontrado", None)
            await self.db.commit()
            return standard_response(200, "Cliente actualizado", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)

    async def delete_cliente(self, cliente_id: int) -> dict:
        try:
            result = await self.db.execute(
                text(st.DELETE_CLIENTE),
                {"cliente_id": cliente_id}
            )
            row = result.mappings().first()
            if not row:
                return standard_response(404, "Cliente no encontrado", None)
            await self.db.commit()
            return standard_response(200, "Cliente desactivado", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)
```

---

## 6. Capa de Conexión (`conex/conn.py`)

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from core.config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    poolclass=AsyncAdaptedQueuePool,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

---

## 7. Configuración (`core/config.py`)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # Base de datos
    DATABASE_URL: str = "postgresql+asyncpg://postgres:1234@localhost:5432/Vortex"
    DB_ECHO: bool = False

    # JWT
    JWT_SECRET: str = "CAMBIAR_EN_PRODUCCION"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    # App
    APP_NAME: str = "Vortex Facturación & CxC"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True


settings = Settings()
```

---

## 8. App Principal (`app.py`)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from apirouters.auth.api.api import AuthAPI
from apirouters.empresa.api.api import EmpresaAPI
from apirouters.monedas.api.api import MonedasAPI
# ... importar todos los routers de los módulos ...

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ajustar en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status_code": 200, "message": "OK", "data": {"app": settings.APP_NAME}}


# Registro de routers
app.include_router(AuthAPI.router)
app.include_router(EmpresaAPI.router)
app.include_router(MonedasAPI.router)
# ... resto de routers ...
```

---

## 9. Entry Point (`main.py`)

```python
import uvicorn
from app import app

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
```

---

## 10. Patrón de Manejo de Errores

Tres niveles:

1. **Validación de entrada** — Pydantic la hace automáticamente (retorna 422).
2. **Reglas de negocio** — el use case retorna `standard_response(409, "REGLA_NEGOCIO: mensaje", None)`. Ej: `LIMITE_CREDITO_EXCEDIDO`, `CLIENTE_YA_EXISTE`, `STOCK_INSUFICIENTE`.
3. **Errores no controlados** — el `except Exception` general retorna 500 con el detalle.

Códigos de error semánticos (constantes en `core/responses.py`):
- `200 OK` — operación exitosa.
- `201 Created` — recurso creado.
- `400 Bad Request` — datos inválidos que Pydantic no detectó.
- `404 Not Found` — recurso no existe.
- `409 Conflict` — regla de negocio violada.
- `500 Internal Server Error` — error inesperado.

---

## 11. Orden de Implementación Sugerido (Fases)

| Fase | Módulo | Notas |
|---|---|---|
| **0** | Setup + `conex/` + `core/` + `app.py` + `/health` | Verificar conectividad a la DB Vortex |
| **1** | `empresa`, `monedas`, `tasas_cambio`, `parametros_sistema`, `usuarios` | Maestros base |
| **2** | `puntos_emision`, `secuencias_documentos` | Configuración de numeración |
| **3** | `clientes`, `vendedores`, `productos` | Maestros de negocio |
| **4** | `documentos_ventas` (factura/nota entrega) | Core transaccional |
| **5** | `movimientos_cxc`, `aplicaciones_cxc` | Libro mayor y cruces |
| **6** | `pagos`, `anticipos`, `retenciones` | Operación CxC |
| **7** | `notas_credito`, `notas_debito` | Ajustes |
| **8** | `reportes` (estado de cuenta, antigüedad) | Reportes |
| **9** | `override_credito_log` + auditoría | Endurecimiento |
| **10** | Tests, validación de reglas de negocio, hardening | Cierre MVP |

---

## 12. Reglas de Oro

1. **Nunca** se mezcla SQL con lógica de negocio. SQL → `statement/`, lógica → `use_case/`.
2. **Nunca** un endpoint retorna datos sin la envoltura `{ status_code, message, data }`.
3. **Nunca** un `use_case` importa `APIRouter` o `Depends`. Solo recibe `AsyncSession` por DI.
4. **Nunca** se hacen `commit` implícitos. `commit()` solo cuando la operación es exitosa.
5. **Nunca** se mezcla lógica de un módulo dentro de otro. Si Clientes necesita consultar monedas, importa el query de `monedas.statement`, no reinventa.
6. **Siempre** se valida el RIF venezolano con regex antes de insertar clientes.
7. **Siempre** se manejan transacciones explícitamente: `try/except + rollback + commit` en cada use case.
8. **Siempre** los nombres de archivos coinciden con el nombre del directorio: `api/api.py`, `models/models.py`, `statement/statement.py`, `use_case/use_case.py`.
