"""
Logica de negocio del modulo Puntos de Emision.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.responses import standard_response
from apirouters.puntos_emision.models.models import (
    PuntoEmisionCreateRequest,
    PuntoEmisionUpdateRequest,
)
from apirouters.puntos_emision.statement import statement as st


class PuntosEmisionUseCase:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_punto(self, data: PuntoEmisionCreateRequest) -> dict:
        try:
            existing = await self.db.execute(
                text(st.SELECT_PUNTO_EMISION_BY_CODIGO), {"codigo": data.codigo}
            )
            if existing.mappings().first():
                return standard_response(
                    409, "REGISTRO_DUPLICADO: ya existe un punto de emision con ese codigo", None
                )

            result = await self.db.execute(text(st.INSERT_PUNTO_EMISION), data.model_dump())
            row = result.mappings().first()
            await self.db.commit()
            return standard_response(201, "Punto de emision creado exitosamente", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)

    async def get_puntos(self, limit: int = 50, offset: int = 0) -> dict:
        try:
            result = await self.db.execute(
                text(st.SELECT_PUNTOS_EMISION_PAGINATED), {"limit": limit, "offset": offset}
            )
            rows = [dict(r) for r in result.mappings().all()]
            total_result = await self.db.execute(text(st.SELECT_PUNTOS_EMISION_COUNT))
            total = total_result.scalar() or 0
            return standard_response(
                200,
                f"Listado de puntos de emision (total={total})",
                {"items": rows, "total": total, "limit": limit, "offset": offset},
            )
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def get_punto_by_id(self, punto_id: int) -> dict:
        try:
            result = await self.db.execute(
                text(st.SELECT_PUNTO_EMISION_BY_ID), {"punto_id": punto_id}
            )
            row = result.mappings().first()
            if not row:
                return standard_response(404, "Punto de emision no encontrado", None)
            return standard_response(200, "Punto de emision encontrado", dict(row))
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def search_puntos(self, keyword: str) -> dict:
        try:
            if not keyword or len(keyword.strip()) < 2:
                return standard_response(400, "KEYWORD_REQUERIDO: minimo 2 caracteres", None)
            result = await self.db.execute(
                text(st.SEARCH_PUNTOS_EMISION_BY_KEYWORD), {"keyword": f"%{keyword.strip()}%"}
            )
            rows = [dict(r) for r in result.mappings().all()]
            return standard_response(200, f"{len(rows)} resultados para '{keyword}'", rows)
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def update_punto(self, punto_id: int, data: PuntoEmisionUpdateRequest) -> dict:
        try:
            existing = await self.db.execute(
                text(st.SELECT_PUNTO_EMISION_BY_ID), {"punto_id": punto_id}
            )
            if not existing.mappings().first():
                return standard_response(404, "Punto de emision no encontrado", None)

            payload = data.model_dump(exclude_unset=True)
            payload["punto_id"] = punto_id

            result = await self.db.execute(text(st.UPDATE_PUNTO_EMISION), payload)
            row = result.mappings().first()
            await self.db.commit()
            return standard_response(200, "Punto de emision actualizado", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)

    async def delete_punto(self, punto_id: int) -> dict:
        try:
            result = await self.db.execute(
                text(st.DELETE_PUNTO_EMISION), {"punto_id": punto_id}
            )
            row = result.mappings().first()
            if not row:
                return standard_response(404, "Punto de emision no encontrado", None)
            await self.db.commit()
            return standard_response(200, "Punto de emision desactivado", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)
