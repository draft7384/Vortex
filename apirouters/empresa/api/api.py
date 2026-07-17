"""
Capa HTTP del modulo Empresa (singleton). Todos los endpoints requieren JWT.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from conex.conn import get_db
from apirouters.auth.use_case.use_case import get_current_user, CurrentUser
from apirouters.empresa.models.models import EmpresaConfigRequest
from apirouters.empresa.use_case.use_case import EmpresaUseCase


class EmpresaAPI:
    router = APIRouter(prefix="/empresa-config", tags=["Empresa"])

    @staticmethod
    @router.get("/", summary="Obtener la configuracion de la empresa")
    async def get_empresa(
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await EmpresaUseCase(db).get_empresa()

    @staticmethod
    @router.post("/", summary="Crear o reemplazar la configuracion de la empresa (upsert)")
    async def upsert_empresa(
        data: EmpresaConfigRequest,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await EmpresaUseCase(db).upsert_empresa(data)

    @staticmethod
    @router.put("/", summary="Alias de POST (upsert) - actualiza la configuracion")
    async def upsert_empresa_put(
        data: EmpresaConfigRequest,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await EmpresaUseCase(db).upsert_empresa(data)
