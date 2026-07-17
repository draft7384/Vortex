"""
Capa HTTP del modulo Tasas de Cambio. Todos los endpoints requieren JWT.
"""
from datetime import date as date_type
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from conex.conn import get_db
from apirouters.auth.use_case.use_case import get_current_user, CurrentUser
from apirouters.tasas_cambio.models.models import (
    TasaCambioCreateRequest,
    TasaCambioUpdateRequest,
)
from apirouters.tasas_cambio.use_case.use_case import TasasCambioUseCase


class TasasCambioAPI:
    router = APIRouter(prefix="/tasas-cambio", tags=["Tasas de Cambio"])

    @staticmethod
    @router.post("/", status_code=201, summary="Registrar una tasa de cambio")
    async def create_tasa(
        data: TasaCambioCreateRequest,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await TasasCambioUseCase(db).create_tasa(data)

    @staticmethod
    @router.get("/", summary="Listar tasas con paginacion")
    async def get_tasas(
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await TasasCambioUseCase(db).get_tasas(limit, offset)

    @staticmethod
    @router.get("/actual", summary="Obtener la tasa mas reciente de una moneda")
    async def get_tasa_actual(
        moneda_id: int = Query(..., gt=0),
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await TasasCambioUseCase(db).get_tasa_actual(moneda_id)

    @staticmethod
    @router.get("/por-fecha", summary="Obtener la tasa de una moneda en una fecha especifica")
    async def get_tasa_by_fecha(
        moneda_id: int = Query(..., gt=0),
        fecha: date_type = Query(...),
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await TasasCambioUseCase(db).get_tasa_by_fecha(moneda_id, fecha)

    @staticmethod
    @router.get("/{tasa_id}", summary="Obtener una tasa por ID")
    async def get_tasa_by_id(
        tasa_id: int,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await TasasCambioUseCase(db).get_tasa_by_id(tasa_id)

    @staticmethod
    @router.put("/{tasa_id}", summary="Actualizar el valor de una tasa")
    async def update_tasa(
        tasa_id: int,
        data: TasaCambioUpdateRequest,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await TasasCambioUseCase(db).update_tasa(tasa_id, data)

    @staticmethod
    @router.delete("/{tasa_id}", summary="Eliminar una tasa")
    async def delete_tasa(
        tasa_id: int,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await TasasCambioUseCase(db).delete_tasa(tasa_id)
