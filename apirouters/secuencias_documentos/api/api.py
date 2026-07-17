"""
Capa HTTP del modulo Secuencias de Documentos. Todos los endpoints requieren JWT.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from conex.conn import get_db
from apirouters.auth.use_case.use_case import get_current_user, CurrentUser
from apirouters.secuencias_documentos.models.models import (
    SecuenciaCreateRequest,
    SecuenciaUpdateRequest,
    InicializarSecuenciasRequest,
)
from apirouters.secuencias_documentos.use_case.use_case import SecuenciasDocumentosUseCase


class SecuenciasDocumentosAPI:
    router = APIRouter(prefix="/secuencias-documentos", tags=["Secuencias de Documentos"])

    @staticmethod
    @router.post("/", status_code=201, summary="Crear una secuencia personalizada")
    async def create_secuencia(
        data: SecuenciaCreateRequest,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await SecuenciasDocumentosUseCase(db).create_secuencia(data)

    @staticmethod
    @router.post("/inicializar", status_code=201, summary="Inicializar las 6 secuencias estandar de un punto de emision")
    async def inicializar_secuencias(
        data: InicializarSecuenciasRequest,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await SecuenciasDocumentosUseCase(db).inicializar_secuencias(data)

    @staticmethod
    @router.get("/", summary="Listar secuencias con paginacion")
    async def get_secuencias(
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await SecuenciasDocumentosUseCase(db).get_secuencias(limit, offset)

    @staticmethod
    @router.get("/por-punto/{punto_emision_id}", summary="Listar secuencias de un punto de emision")
    async def get_secuencias_by_punto(
        punto_emision_id: int,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await SecuenciasDocumentosUseCase(db).get_secuencias_by_punto(punto_emision_id)

    @staticmethod
    @router.get("/{secuencia_id}", summary="Obtener una secuencia por ID")
    async def get_secuencia_by_id(
        secuencia_id: int,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await SecuenciasDocumentosUseCase(db).get_secuencia_by_id(secuencia_id)

    @staticmethod
    @router.put("/{secuencia_id}", summary="Actualizar una secuencia")
    async def update_secuencia(
        secuencia_id: int,
        data: SecuenciaUpdateRequest,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await SecuenciasDocumentosUseCase(db).update_secuencia(secuencia_id, data)

    @staticmethod
    @router.delete("/{secuencia_id}", summary="Desactivar una secuencia (soft-delete)")
    async def delete_secuencia(
        secuencia_id: int,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await SecuenciasDocumentosUseCase(db).delete_secuencia(secuencia_id)
