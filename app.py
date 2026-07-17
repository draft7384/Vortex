"""
Vortex - App principal FastAPI.
Registra middlewares, routers de cada modulo y endpoints transversales.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from apirouters.auth.api.api import AuthAPI
from apirouters.clientes.api.api import ClientesAPI
from apirouters.usuarios.api.api import UsuariosAPI
from apirouters.monedas.api.api import MonedasAPI
from apirouters.tasas_cambio.api.api import TasasCambioAPI
from apirouters.parametros_sistema.api.api import ParametrosSistemaAPI
from apirouters.empresa.api.api import EmpresaAPI
from apirouters.puntos_emision.api.api import PuntosEmisionAPI
from apirouters.secuencias_documentos.api.api import SecuenciasDocumentosAPI
from apirouters.vendedores.api.api import VendedoresAPI
from apirouters.productos.api.api import ProductosAPI
from apirouters.documentos_ventas.api.api import DocumentosVentasAPI
from apirouters.pagos.api.api import PagosAPI
from apirouters.aplicaciones_cxc.api.api import AplicacionesCxcAPI
from apirouters.cxc_reportes.api.api import CxcReportesAPI


# ============================================================
# Inicializacion de la app
# ============================================================
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    description="Modulo de Facturacion y Cuentas por Cobrar para pequenos comerciantes venezolanos.",
)


# ============================================================
# Middlewares
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.CORS_ORIGINS == "*" else settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Endpoints transversales (publicos)
# ============================================================
@app.get("/health", tags=["Health"])
async def health():
    return {
        "status_code": 200,
        "message": "OK",
        "data": {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "debug": settings.DEBUG,
        },
    }


# ============================================================
# Registro de routers
# Convencion: app.include_router(ModuloAPI.router)
#
# Orden de dependencias:
#   1. /auth     (publico, devuelve JWT)
#   2. /usuarios (CRUD, requiere JWT; cualquier usuario autenticado)
#   3. /clientes (CRUD, requiere JWT; cualquier usuario autenticado)
# Los routers se registran tal cual; la proteccion se aplica dentro de cada
# modulo usando Depends(get_current_user) en los endpoints individuales.
# ============================================================
app.include_router(AuthAPI.router)               # /auth/login (publico) + /auth/me (protegido)
app.include_router(UsuariosAPI.router)          # /usuarios/* (protegido)
app.include_router(ClientesAPI.router)          # /clientes/* (protegido)
app.include_router(EmpresaAPI.router)           # /empresa-config/* (protegido, singleton)
app.include_router(MonedasAPI.router)           # /monedas/* (protegido)
app.include_router(TasasCambioAPI.router)       # /tasas-cambio/* (protegido)
app.include_router(ParametrosSistemaAPI.router) # /parametros-sistema/* (protegido)
app.include_router(PuntosEmisionAPI.router)     # /puntos-emision/* (protegido)
app.include_router(SecuenciasDocumentosAPI.router) # /secuencias-documentos/* (protegido)
app.include_router(VendedoresAPI.router)          # /vendedores/* (protegido)
app.include_router(ProductosAPI.router)           # /productos/* (protegido)
app.include_router(DocumentosVentasAPI.router)    # /documentos-ventas/* (protegido)
app.include_router(PagosAPI.router)                  # /pagos/* (protegido, Fase 4)
app.include_router(AplicacionesCxcAPI.router)        # /aplicaciones-cxc/* (protegido, Fase 4)
app.include_router(CxcReportesAPI.router)            # /cxc-reportes/* (protegido, Fase 4)
