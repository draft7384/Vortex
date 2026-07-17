"""
Capa HTTP del modulo Clientes.
Encapsula el APIRouter y los endpoints. Solo delega al UseCase.
Todos los endpoints requieren autenticacion (JWT).
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from conex.conn import get_db
from apirouters.auth.use_case.use_case import get_current_user, CurrentUser
from apirouters.clientes.models.models import (
    ClienteCreateRequest,
    ClienteUpdateRequest,
)
from apirouters.clientes.use_case.use_case import ClientesUseCase


class ClientesAPI:
    """Router del modulo Clientes. Convencion: nombre de clase + sufijo 'API'."""

    router = APIRouter(prefix="/clientes", tags=["Clientes"])

    @staticmethod
    @router.post("/", status_code=201, summary="Crear un nuevo cliente")
    async def create_cliente(
        data: ClienteCreateRequest,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await ClientesUseCase(db).create_cliente(data)

    @staticmethod
    @router.get("/", summary="Listar clientes con paginacion")
    async def get_clientes(
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        search: Optional[str] = Query(None, description="Buscar por nombre, RIF o codigo"),
        activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
        sort_by: Optional[str] = Query("nombre_razon_social", description="Columna para ordenar"),
        sort_order: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Orden ascendente o descendente"),
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await ClientesUseCase(db).get_clientes(limit, offset, search, activo, sort_by, sort_order)

    @staticmethod
    @router.get("/search", summary="Buscar clientes por keyword (RIF, nombre o codigo)")
    async def search_clientes(
        keyword: str = Query(..., min_length=2, description="Texto a buscar"),
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await ClientesUseCase(db).search_clientes(keyword)

    @staticmethod
    @router.get("/{cliente_id}", summary="Obtener un cliente por ID")
    async def get_cliente_by_id(
        cliente_id: int,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await ClientesUseCase(db).get_cliente_by_id(cliente_id)

    @staticmethod
    @router.put("/{cliente_id}", summary="Actualizar un cliente existente")
    async def update_cliente(
        cliente_id: int,
        data: ClienteUpdateRequest,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await ClientesUseCase(db).update_cliente(cliente_id, data)

    @staticmethod
    @router.delete("/{cliente_id}", summary="Desactivar un cliente (soft-delete)")
    async def delete_cliente(
        cliente_id: int,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await ClientesUseCase(db).delete_cliente(cliente_id)
