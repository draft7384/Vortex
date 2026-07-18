"""
Capa HTTP del modulo Productos. Todos los endpoints requieren JWT.
"""
from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from conex.conn import get_db
from apirouters.auth.use_case.use_case import get_current_user, CurrentUser
from apirouters.productos.models.models import (
    ProductoCreateRequest,
    ProductoUpdateRequest,
)
from apirouters.productos.use_case.use_case import ProductosUseCase
from core.responses import standard_response


class ProductosAPI:
    router = APIRouter(prefix="/productos", tags=["Productos"])

    @staticmethod
    @router.post("/", status_code=201, summary="Crear un producto o servicio")
    async def create_producto(
        data: ProductoCreateRequest,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await ProductosUseCase(db).create_producto(data)

    @staticmethod
    @router.get("/", summary="Listar productos con paginacion")
    async def get_productos(
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await ProductosUseCase(db).get_productos(limit, offset)

    @staticmethod
    @router.get("/search", summary="Buscar productos por codigo o descripcion")
    async def search_productos(
        keyword: str = Query(..., min_length=2),
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await ProductosUseCase(db).search_productos(keyword)

    @staticmethod
    @router.get("/bajo-stock", summary="Listar productos con existencia bajo umbral")
    async def get_bajo_stock(
        umbral: float = Query(5.0, ge=0),
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await ProductosUseCase(db).get_productos_bajo_stock(umbral)

    @staticmethod
    @router.get("/{producto_id}", summary="Obtener un producto por ID")
    async def get_producto_by_id(
        producto_id: int,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await ProductosUseCase(db).get_producto_by_id(producto_id)

    @staticmethod
    @router.put("/{producto_id}", summary="Actualizar un producto")
    async def update_producto(
        producto_id: int,
        data: ProductoUpdateRequest,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await ProductosUseCase(db).update_producto(producto_id, data)

    @staticmethod
    @router.delete("/{producto_id}", summary="Desactivar un producto (soft-delete)")
    async def delete_producto(
        producto_id: int,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await ProductosUseCase(db).delete_producto(producto_id)

    @staticmethod
    @router.post("/import", summary="Importar productos masivamente desde Excel")
    async def import_productos(
        file: UploadFile = File(..., description="Archivo Excel (.xlsx)"),
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        if not file.filename.endswith(".xlsx"):
            return standard_response(400, "FORMATO_INVALIDO: solo se permiten archivos .xlsx", None)
        return await ProductosUseCase(db).import_productos_from_excel(file)
