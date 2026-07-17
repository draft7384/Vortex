"""
Logica de negocio del modulo Usuarios.
Incluye hashing de password con bcrypt.
"""
import bcrypt

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.responses import standard_response
from apirouters.usuarios.models.models import (
    UsuarioCreateRequest,
    UsuarioUpdateRequest,
)
from apirouters.usuarios.statement import statement as st


def _hash_password(plain: str) -> str:
    """Genera un hash bcrypt con cost=12."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


class UsuariosUseCase:
    """Encapsula la logica de negocio del modulo Usuarios."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================
    # CREATE
    # =========================================================
    async def create_usuario(self, data: UsuarioCreateRequest) -> dict:
        try:
            # Validar username unico
            existing = await self.db.execute(
                text(st.SELECT_USUARIO_BY_USERNAME), {"username": data.username}
            )
            if existing.mappings().first():
                return standard_response(
                    409, "REGISTRO_DUPLICADO: ya existe un usuario con ese username", None
                )

            # Validar email unico (si fue provisto)
            if data.email:
                existing_email = await self.db.execute(
                    text(st.SELECT_USUARIO_BY_EMAIL), {"email": data.email}
                )
                if existing_email.mappings().first():
                    return standard_response(
                        409, "REGISTRO_DUPLICADO: ya existe un usuario con ese email", None
                    )

            payload = data.model_dump()
            payload["password_hash"] = _hash_password(data.password)
            payload.pop("password")  # no va al SQL

            result = await self.db.execute(text(st.INSERT_USUARIO), payload)
            row = result.mappings().first()
            await self.db.commit()
            return standard_response(201, "Usuario creado exitosamente", dict(row))

        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error al crear usuario: {str(e)}", None)

    # =========================================================
    # READ - Listado
    # =========================================================
    async def get_usuarios(self, limit: int = 50, offset: int = 0) -> dict:
        try:
            result = await self.db.execute(
                text(st.SELECT_USUARIOS_PAGINATED), {"limit": limit, "offset": offset}
            )
            rows = [dict(r) for r in result.mappings().all()]

            total_result = await self.db.execute(text(st.SELECT_USUARIOS_COUNT))
            total = total_result.scalar() or 0

            return standard_response(
                200,
                f"Listado de usuarios (total={total})",
                {"items": rows, "total": total, "limit": limit, "offset": offset},
            )
        except Exception as e:
            return standard_response(500, f"Error al listar usuarios: {str(e)}", None)

    # =========================================================
    # READ - Por ID
    # =========================================================
    async def get_usuario_by_id(self, usuario_id: int) -> dict:
        try:
            result = await self.db.execute(
                text(st.SELECT_USUARIO_BY_ID), {"usuario_id": usuario_id}
            )
            row = result.mappings().first()
            if not row:
                return standard_response(404, "Usuario no encontrado", None)
            return standard_response(200, "Usuario encontrado", dict(row))
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    # =========================================================
    # READ - Busqueda por keyword
    # =========================================================
    async def search_usuarios(self, keyword: str) -> dict:
        try:
            if not keyword or len(keyword.strip()) < 2:
                return standard_response(
                    400, "KEYWORD_REQUERIDO: minimo 2 caracteres para buscar", None
                )
            result = await self.db.execute(
                text(st.SEARCH_USUARIOS_BY_KEYWORD), {"keyword": f"%{keyword.strip()}%"}
            )
            rows = [dict(r) for r in result.mappings().all()]
            return standard_response(200, f"{len(rows)} resultados para '{keyword}'", rows)
        except Exception as e:
            return standard_response(500, f"Error en busqueda: {str(e)}", None)

    # =========================================================
    # UPDATE
    # =========================================================
    async def update_usuario(self, usuario_id: int, data: UsuarioUpdateRequest) -> dict:
        try:
            existing = await self.db.execute(
                text(st.SELECT_USUARIO_BY_ID), {"usuario_id": usuario_id}
            )
            if not existing.mappings().first():
                return standard_response(404, "Usuario no encontrado", None)

            payload = data.model_dump(exclude_unset=True)
            payload["usuario_id"] = usuario_id

            # Si viene password nuevo, hashearlo
            if "password" in payload and payload["password"]:
                payload["password_hash"] = _hash_password(payload.pop("password"))
            else:
                payload.pop("password", None)

            result = await self.db.execute(text(st.UPDATE_USUARIO), payload)
            row = result.mappings().first()
            await self.db.commit()
            return standard_response(200, "Usuario actualizado", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error al actualizar usuario: {str(e)}", None)

    # =========================================================
    # DELETE (soft)
    # =========================================================
    async def delete_usuario(self, usuario_id: int) -> dict:
        try:
            result = await self.db.execute(
                text(st.DELETE_USUARIO), {"usuario_id": usuario_id}
            )
            row = result.mappings().first()
            if not row:
                return standard_response(404, "Usuario no encontrado", None)
            await self.db.commit()
            return standard_response(200, "Usuario desactivado", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error al eliminar usuario: {str(e)}", None)
