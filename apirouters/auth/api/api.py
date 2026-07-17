"""
Capa HTTP del modulo Auth.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from conex.conn import get_db
from apirouters.auth.models.models import LoginRequest
from apirouters.auth.use_case.use_case import AuthUseCase, get_current_user, CurrentUser


class AuthAPI:
    router = APIRouter(prefix="/auth", tags=["Auth"])

    # =========================================================
    # POST /auth/login (PUBLICO: NO requiere token)
    # =========================================================
    @staticmethod
    @router.post("/login", summary="Iniciar sesion y obtener JWT")
    async def login(
        data: LoginRequest,
        db: AsyncSession = Depends(get_db),
    ):
        return await AuthUseCase(db).login(data)

    # =========================================================
    # GET /auth/me (PROTEGIDO: requiere token)
    # =========================================================
    @staticmethod
    @router.get("/me", summary="Obtener el usuario autenticado actualmente")
    async def me(usuario_actual: CurrentUser = Depends(get_current_user)):
        return {
            "status_code": 200,
            "message": "Usuario autenticado",
            "data": {
                "id": usuario_actual.id,
                "username": usuario_actual.username,
                "rol": usuario_actual.rol,
            },
        }
