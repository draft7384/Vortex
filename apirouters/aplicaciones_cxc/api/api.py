"""
Router del modulo Aplicaciones CxC.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apirouters.aplicaciones_cxc.models.models import (
    AplicacionCxcCreateRequest,
    AplicacionCxcReverseRequest,
)
from apirouters.aplicaciones_cxc.use_case.use_case import AplicacionesCxcUseCase
from apirouters.auth.use_case.use_case import CurrentUser, get_current_user
from conex.conn import get_db


class AplicacionesCxcAPI:
    router = APIRouter(prefix="/aplicaciones-cxc", tags=["Aplicaciones CxC"])

    @staticmethod
    @router.post("/", status_code=201)
    async def create_aplicacion(
        data: AplicacionCxcCreateRequest,
        current_user: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        return await AplicacionesCxcUseCase(db).create_aplicacion(data, current_user)

    @staticmethod
    @router.post("/{aplicacion_id}/reversar", status_code=200)
    async def reversar_aplicacion(
        aplicacion_id: int,
        data: AplicacionCxcReverseRequest,
        current_user: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        return await AplicacionesCxcUseCase(db).reversar_aplicacion(aplicacion_id, data, current_user)

    @staticmethod
    @router.get("/{aplicacion_id}", status_code=200)
    async def get_aplicacion(
        aplicacion_id: int,
        _: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        return await AplicacionesCxcUseCase(db).get_aplicacion_by_id(aplicacion_id)
