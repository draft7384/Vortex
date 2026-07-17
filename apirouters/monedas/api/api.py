"""
Capa HTTP del modulo Monedas. Todos los endpoints requieren JWT.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from conex.conn import get_db
from apirouters.auth.use_case.use_case import get_current_user, CurrentUser
from apirouters.monedas.models.models import (
    MonedaCreateRequest,
    MonedaUpdateRequest,
)
from apirouters.monedas.use_case.use_case import MonedasUseCase


class MonedasAPI:
    router = APIRouter(prefix="/monedas", tags=["Monedas"])

    @staticmethod
    @router.post("/", status_code=201, summary="Crear una nueva moneda")
    async def create_moneda(
        data: MonedaCreateRequest,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await MonedasUseCase(db).create_moneda(data)

    @staticmethod
    @router.get("/", summary="Listar monedas con paginacion")
    async def get_monedas(
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await MonedasUseCase(db).get_monedas(limit, offset)

    @staticmethod
    @router.get("/local", summary="Obtener la moneda local del sistema")
    async def get_moneda_local(
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await MonedasUseCase(db).get_moneda_local()

    @staticmethod
    @router.get("/search", summary="Buscar monedas por codigo ISO o nombre")
    async def search_monedas(
        keyword: str = Query(..., min_length=2),
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await MonedasUseCase(db).search_monedas(keyword)

    @staticmethod
    @router.get("/{moneda_id}", summary="Obtener una moneda por ID")
    async def get_moneda_by_id(
        moneda_id: int,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await MonedasUseCase(db).get_moneda_by_id(moneda_id)

    @staticmethod
    @router.put("/{moneda_id}", summary="Actualizar una moneda")
    async def update_moneda(
        moneda_id: int,
        data: MonedaUpdateRequest,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await MonedasUseCase(db).update_moneda(moneda_id, data)

    @staticmethod
    @router.delete("/{moneda_id}", summary="Desactivar una moneda (soft-delete)")
    async def delete_moneda(
        moneda_id: int,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await MonedasUseCase(db).delete_moneda(moneda_id)
