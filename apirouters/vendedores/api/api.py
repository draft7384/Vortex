"""
Capa HTTP del modulo Vendedores. Todos los endpoints requieren JWT.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from conex.conn import get_db
from apirouters.auth.use_case.use_case import get_current_user, CurrentUser
from apirouters.vendedores.models.models import (
    VendedorCreateRequest,
    VendedorUpdateRequest,
)
from apirouters.vendedores.use_case.use_case import VendedoresUseCase


class VendedoresAPI:
    router = APIRouter(prefix="/vendedores", tags=["Vendedores"])

    @staticmethod
    @router.post("/", status_code=201, summary="Crear un vendedor")
    async def create_vendedor(
        data: VendedorCreateRequest,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await VendedoresUseCase(db).create_vendedor(data)

    @staticmethod
    @router.get("/", summary="Listar vendedores con paginacion")
    async def get_vendedores(
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await VendedoresUseCase(db).get_vendedores(limit, offset)

    @staticmethod
    @router.get("/search", summary="Buscar vendedores por codigo o nombre")
    async def search_vendedores(
        keyword: str = Query(..., min_length=2),
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await VendedoresUseCase(db).search_vendedores(keyword)

    @staticmethod
    @router.get("/{vendedor_id}", summary="Obtener un vendedor por ID")
    async def get_vendedor_by_id(
        vendedor_id: int,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await VendedoresUseCase(db).get_vendedor_by_id(vendedor_id)

    @staticmethod
    @router.put("/{vendedor_id}", summary="Actualizar un vendedor")
    async def update_vendedor(
        vendedor_id: int,
        data: VendedorUpdateRequest,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await VendedoresUseCase(db).update_vendedor(vendedor_id, data)

    @staticmethod
    @router.delete("/{vendedor_id}", summary="Desactivar un vendedor (soft-delete)")
    async def delete_vendedor(
        vendedor_id: int,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await VendedoresUseCase(db).delete_vendedor(vendedor_id)
