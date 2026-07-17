"""
Logica de negocio del modulo Monedas.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.responses import standard_response
from apirouters.monedas.models.models import (
    MonedaCreateRequest,
    MonedaUpdateRequest,
)
from apirouters.monedas.statement import statement as st


class MonedasUseCase:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_moneda(self, data: MonedaCreateRequest) -> dict:
        try:
            # Validar codigo_iso unico
            existing = await self.db.execute(
                text(st.SELECT_MONEDA_BY_ISO), {"codigo_iso": data.codigo_iso.upper()}
            )
            if existing.mappings().first():
                return standard_response(
                    409, "REGISTRO_DUPLICADO: ya existe una moneda con ese codigo_iso", None
                )

            # Normalizar codigo_iso a mayusculas
            payload = data.model_dump()
            payload["codigo_iso"] = data.codigo_iso.upper()

            result = await self.db.execute(text(st.INSERT_MONEDA), payload)
            row = result.mappings().first()
            await self.db.commit()
            return standard_response(201, "Moneda creada exitosamente", dict(row))
        except Exception as e:
            await self.db.rollback()
            error_msg = str(e)
            # El constraint uq_moneda_local dispara este error si ya hay una local
            if "uq_moneda_local" in error_msg:
                return standard_response(
                    409, "SOLO_UNA_MONEDA_LOCAL: ya existe una moneda marcada como local (constraint DB)", None
                )
            return standard_response(500, f"Error al crear moneda: {error_msg}", None)

    async def get_monedas(self, limit: int = 50, offset: int = 0) -> dict:
        try:
            result = await self.db.execute(
                text(st.SELECT_MONEDAS_PAGINATED), {"limit": limit, "offset": offset}
            )
            rows = [dict(r) for r in result.mappings().all()]
            total_result = await self.db.execute(text(st.SELECT_MONEDAS_COUNT))
            total = total_result.scalar() or 0
            return standard_response(
                200,
                f"Listado de monedas (total={total})",
                {"items": rows, "total": total, "limit": limit, "offset": offset},
            )
        except Exception as e:
            return standard_response(500, f"Error al listar monedas: {str(e)}", None)

    async def get_moneda_by_id(self, moneda_id: int) -> dict:
        try:
            result = await self.db.execute(
                text(st.SELECT_MONEDA_BY_ID), {"moneda_id": moneda_id}
            )
            row = result.mappings().first()
            if not row:
                return standard_response(404, "Moneda no encontrada", None)
            return standard_response(200, "Moneda encontrada", dict(row))
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def get_moneda_local(self) -> dict:
        """Helper usado por otros modulos para saber cual es la moneda local."""
        try:
            result = await self.db.execute(text(st.SELECT_MONEDA_LOCAL))
            row = result.mappings().first()
            if not row:
                return standard_response(404, "No hay moneda local configurada", None)
            return standard_response(200, "Moneda local", dict(row))
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def search_monedas(self, keyword: str) -> dict:
        try:
            if not keyword or len(keyword.strip()) < 2:
                return standard_response(400, "KEYWORD_REQUERIDO: minimo 2 caracteres", None)
            result = await self.db.execute(
                text(st.SEARCH_MONEDAS_BY_KEYWORD), {"keyword": f"%{keyword.strip()}%"}
            )
            rows = [dict(r) for r in result.mappings().all()]
            return standard_response(200, f"{len(rows)} resultados para '{keyword}'", rows)
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def update_moneda(self, moneda_id: int, data: MonedaUpdateRequest) -> dict:
        try:
            existing = await self.db.execute(
                text(st.SELECT_MONEDA_BY_ID), {"moneda_id": moneda_id}
            )
            if not existing.mappings().first():
                return standard_response(404, "Moneda no encontrada", None)

            payload = data.model_dump(exclude_unset=True)
            payload["moneda_id"] = moneda_id
            if "codigo_iso" in payload and payload["codigo_iso"]:
                payload["codigo_iso"] = payload["codigo_iso"].upper()

            result = await self.db.execute(text(st.UPDATE_MONEDA), payload)
            row = result.mappings().first()
            await self.db.commit()
            return standard_response(200, "Moneda actualizada", dict(row))
        except Exception as e:
            await self.db.rollback()
            error_msg = str(e)
            if "uq_moneda_local" in error_msg:
                return standard_response(
                    409, "SOLO_UNA_MONEDA_LOCAL: ya existe otra moneda marcada como local", None
                )
            return standard_response(500, f"Error: {error_msg}", None)

    async def delete_moneda(self, moneda_id: int) -> dict:
        try:
            result = await self.db.execute(
                text(st.DELETE_MONEDA), {"moneda_id": moneda_id}
            )
            row = result.mappings().first()
            if not row:
                return standard_response(404, "Moneda no encontrada", None)
            await self.db.commit()
            return standard_response(200, "Moneda desactivada", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)
