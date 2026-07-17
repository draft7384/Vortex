"""
Router del modulo Reportes CxC.
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apirouters.auth.use_case.use_case import CurrentUser, get_current_user
from apirouters.cxc_reportes.use_case.use_case import CxcReportesUseCase
from conex.conn import get_db


class CxcReportesAPI:
    router = APIRouter(prefix="/cxc-reportes", tags=["Reportes CxC"])

    @staticmethod
    @router.get("/movimientos", status_code=200)
    async def list_movimientos(
        cliente_id: Optional[int] = Query(None, gt=0),
        tipo: Optional[str] = Query(None),
        estado: Optional[str] = Query(None),
        fecha_desde: Optional[date] = Query(None),
        fecha_hasta: Optional[date] = Query(None),
        solo_pendientes: bool = Query(False),
        limit: int = Query(50, ge=1, le=500),
        offset: int = Query(0, ge=0),
        _: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        return await CxcReportesUseCase(db).get_movimientos(
            cliente_id=cliente_id,
            tipo=tipo,
            estado=estado,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            solo_pendientes=solo_pendientes,
            limit=limit,
            offset=offset,
        )

    @staticmethod
    @router.get("/movimientos/{movimiento_id}", status_code=200)
    async def get_movimiento(
        movimiento_id: int,
        _: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        return await CxcReportesUseCase(db).get_movimiento_by_id(movimiento_id)

    @staticmethod
    @router.get("/estado-cuenta/{cliente_id}", status_code=200)
    async def estado_cuenta(
        cliente_id: int,
        _: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        return await CxcReportesUseCase(db).get_estado_cuenta(cliente_id)

    @staticmethod
    @router.get("/antiguedad-saldos", status_code=200)
    async def antiguedad_saldos(
        cliente_id: Optional[int] = Query(None, gt=0),
        rangos: Optional[str] = Query(None, description="Override de rangos, ej. '0,30,60,90,120'"),
        _: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        return await CxcReportesUseCase(db).get_antiguedad_saldos(
            cliente_id=cliente_id,
            rangos_override=rangos,
        )
