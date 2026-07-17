"""
Capa HTTP del modulo Parametros del Sistema. Todos los endpoints requieren JWT.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from conex.conn import get_db
from apirouters.auth.use_case.use_case import get_current_user, CurrentUser
from apirouters.parametros_sistema.models.models import (
    ParametroCreateRequest,
    ParametroUpdateRequest,
)
from apirouters.parametros_sistema.use_case.use_case import ParametrosSistemaUseCase


class ParametrosSistemaAPI:
    router = APIRouter(prefix="/parametros-sistema", tags=["Parametros del Sistema"])

    @staticmethod
    @router.post("/", status_code=201, summary="Crear un parametro del sistema")
    async def create_parametro(
        data: ParametroCreateRequest,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await ParametrosSistemaUseCase(db).create_parametro(data)

    @staticmethod
    @router.get("/", summary="Listar parametros del sistema")
    async def get_parametros(
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await ParametrosSistemaUseCase(db).get_parametros(limit, offset)

    @staticmethod
    @router.get("/search", summary="Buscar parametros por clave o descripcion")
    async def search_parametros(
        keyword: str = Query(..., min_length=2),
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await ParametrosSistemaUseCase(db).search_parametros(keyword)

    @staticmethod
    @router.get("/{clave}", summary="Obtener un parametro por su clave")
    async def get_parametro_by_clave(
        clave: str,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await ParametrosSistemaUseCase(db).get_parametro_by_clave(clave)

    @staticmethod
    @router.put("/{clave}", summary="Actualizar el valor de un parametro")
    async def update_parametro(
        clave: str,
        data: ParametroUpdateRequest,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await ParametrosSistemaUseCase(db).update_parametro(clave, data)

    @staticmethod
    @router.delete("/{clave}", summary="Eliminar un parametro")
    async def delete_parametro(
        clave: str,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await ParametrosSistemaUseCase(db).delete_parametro(clave)
