"""
Logica de negocio del modulo Parametros del Sistema.
"""
import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.responses import standard_response
from apirouters.parametros_sistema.models.models import (
    ParametroCreateRequest,
    ParametroUpdateRequest,
)
from apirouters.parametros_sistema.statement import statement as st


def _serialize_valor(valor: Any) -> str:
    """Serializa el valor a string JSON para pasarlo a :valor::jsonb."""
    return json.dumps(valor, ensure_ascii=False, default=str)


class ParametrosSistemaUseCase:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_parametro(self, data: ParametroCreateRequest) -> dict:
        try:
            existing = await self.db.execute(
                text(st.SELECT_PARAMETRO_BY_CLAVE), {"clave": data.clave}
            )
            if existing.mappings().first():
                return standard_response(
                    409, "REGISTRO_DUPLICADO: ya existe un parametro con esa clave. Use PUT para actualizar", None
                )

            payload = {
                "clave": data.clave,
                "valor": _serialize_valor(data.valor),
                "descripcion": data.descripcion,
            }
            result = await self.db.execute(text(st.INSERT_PARAMETRO), payload)
            row = result.mappings().first()
            await self.db.commit()
            return standard_response(201, "Parametro creado exitosamente", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)

    async def get_parametros(self, limit: int = 50, offset: int = 0) -> dict:
        try:
            result = await self.db.execute(
                text(st.SELECT_PARAMETROS_PAGINATED), {"limit": limit, "offset": offset}
            )
            rows = [dict(r) for r in result.mappings().all()]
            total_result = await self.db.execute(text(st.SELECT_PARAMETROS_COUNT))
            total = total_result.scalar() or 0
            return standard_response(
                200,
                f"Listado de parametros (total={total})",
                {"items": rows, "total": total, "limit": limit, "offset": offset},
            )
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def get_parametro_by_clave(self, clave: str) -> dict:
        try:
            result = await self.db.execute(
                text(st.SELECT_PARAMETRO_BY_CLAVE), {"clave": clave}
            )
            row = result.mappings().first()
            if not row:
                return standard_response(404, f"Parametro '{clave}' no encontrado", None)
            return standard_response(200, "Parametro encontrado", dict(row))
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def search_parametros(self, keyword: str) -> dict:
        try:
            if not keyword or len(keyword.strip()) < 2:
                return standard_response(400, "KEYWORD_REQUERIDO: minimo 2 caracteres", None)
            result = await self.db.execute(
                text(st.SEARCH_PARAMETROS_BY_KEYWORD), {"keyword": f"%{keyword.strip()}%"}
            )
            rows = [dict(r) for r in result.mappings().all()]
            return standard_response(200, f"{len(rows)} resultados para '{keyword}'", rows)
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def update_parametro(self, clave: str, data: ParametroUpdateRequest) -> dict:
        try:
            existing = await self.db.execute(
                text(st.SELECT_PARAMETRO_BY_CLAVE), {"clave": clave}
            )
            if not existing.mappings().first():
                return standard_response(404, f"Parametro '{clave}' no encontrado", None)

            payload = {
                "clave": clave,
                "valor": _serialize_valor(data.valor),
                "descripcion": data.descripcion,
            }
            result = await self.db.execute(text(st.UPDATE_PARAMETRO), payload)
            row = result.mappings().first()
            await self.db.commit()
            return standard_response(200, "Parametro actualizado", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)

    async def delete_parametro(self, clave: str) -> dict:
        try:
            result = await self.db.execute(
                text(st.DELETE_PARAMETRO), {"clave": clave}
            )
            row = result.mappings().first()
            if not row:
                return standard_response(404, f"Parametro '{clave}' no encontrado", None)
            await self.db.commit()
            return standard_response(200, "Parametro eliminado", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)
