"""
Capa HTTP del modulo Puntos de Emision. Todos los endpoints requieren JWT.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from conex.conn import get_db
from apirouters.auth.use_case.use_case import get_current_user, CurrentUser
from apirouters.puntos_emision.models.models import (
    PuntoEmisionCreateRequest,
    PuntoEmisionUpdateRequest,
)
from apirouters.puntos_emision.use_case.use_case import PuntosEmisionUseCase


class PuntosEmisionAPI:
    router = APIRouter(prefix="/puntos-emision", tags=["Puntos de Emision"])

    @staticmethod
    @router.post("/", status_code=201, summary="Crear un punto de emision (sucursal/caja)")
    async def create_punto(
        data: PuntoEmisionCreateRequest,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await PuntosEmisionUseCase(db).create_punto(data)

    @staticmethod
    @router.get("/", summary="Listar puntos de emision con paginacion")
    async def get_puntos(
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await PuntosEmisionUseCase(db).get_puntos(limit, offset)

    @staticmethod
    @router.get("/search", summary="Buscar puntos de emision por codigo o nombre")
    async def search_puntos(
        keyword: str = Query(..., min_length=2),
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await PuntosEmisionUseCase(db).search_puntos(keyword)

    @staticmethod
    @router.get("/{punto_id}", summary="Obtener un punto de emision por ID")
    async def get_punto_by_id(
        punto_id: int,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await PuntosEmisionUseCase(db).get_punto_by_id(punto_id)

    @staticmethod
    @router.put("/{punto_id}", summary="Actualizar un punto de emision")
    async def update_punto(
        punto_id: int,
        data: PuntoEmisionUpdateRequest,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await PuntosEmisionUseCase(db).update_punto(punto_id, data)

    @staticmethod
    @router.delete("/{punto_id}", summary="Desactivar un punto de emision (soft-delete)")
    async def delete_punto(
        punto_id: int,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await PuntosEmisionUseCase(db).delete_punto(punto_id)
