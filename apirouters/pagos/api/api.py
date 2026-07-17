"""
Router del modulo Pagos / CxC.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apirouters.auth.use_case.use_case import CurrentUser, get_current_user
from apirouters.pagos.models.models import PagoCreateRequest
from apirouters.pagos.use_case.use_case import PagosUseCase
from conex.conn import get_db


class PagosAPI:
    router = APIRouter(prefix="/pagos", tags=["Pagos / CxC"])

    @staticmethod
    @router.post("/", status_code=201)
    async def create_pago(
        data: PagoCreateRequest,
        current_user: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        return await PagosUseCase(db).create_pago(data, current_user)
