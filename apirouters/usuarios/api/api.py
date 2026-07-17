"""
Capa HTTP del modulo Usuarios.
Todos los endpoints requieren autenticacion (JWT).
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from conex.conn import get_db
from apirouters.auth.use_case.use_case import get_current_user, CurrentUser
from apirouters.usuarios.models.models import (
    UsuarioCreateRequest,
    UsuarioUpdateRequest,
)
from apirouters.usuarios.use_case.use_case import UsuariosUseCase


class UsuariosAPI:
    router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

    @staticmethod
    @router.post("/", status_code=201, summary="Crear un nuevo usuario")
    async def create_usuario(
        data: UsuarioCreateRequest,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await UsuariosUseCase(db).create_usuario(data)

    @staticmethod
    @router.get("/", summary="Listar usuarios con paginacion")
    async def get_usuarios(
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await UsuariosUseCase(db).get_usuarios(limit, offset)

    @staticmethod
    @router.get("/search", summary="Buscar usuarios por username/nombre/email")
    async def search_usuarios(
        keyword: str = Query(..., min_length=2),
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await UsuariosUseCase(db).search_usuarios(keyword)

    @staticmethod
    @router.get("/{usuario_id}", summary="Obtener un usuario por ID")
    async def get_usuario_by_id(
        usuario_id: int,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await UsuariosUseCase(db).get_usuario_by_id(usuario_id)

    @staticmethod
    @router.put("/{usuario_id}", summary="Actualizar un usuario")
    async def update_usuario(
        usuario_id: int,
        data: UsuarioUpdateRequest,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await UsuariosUseCase(db).update_usuario(usuario_id, data)

    @staticmethod
    @router.delete("/{usuario_id}", summary="Desactivar un usuario (soft-delete)")
    async def delete_usuario(
        usuario_id: int,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await UsuariosUseCase(db).delete_usuario(usuario_id)
