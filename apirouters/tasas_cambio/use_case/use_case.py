"""
Logica de negocio del modulo Tasas de Cambio.
"""
from datetime import date as date_type

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.responses import standard_response
from apirouters.tasas_cambio.models.models import (
    TasaCambioCreateRequest,
    TasaCambioUpdateRequest,
)
from apirouters.tasas_cambio.statement import statement as st


class TasasCambioUseCase:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_tasa(self, data: TasaCambioCreateRequest) -> dict:
        try:
            # Verificar unicidad (moneda_id, fecha)
            existing = await self.db.execute(
                text(st.SELECT_TASA_BY_MONEDA_FECHA),
                {"moneda_id": data.moneda_id, "fecha": data.fecha},
            )
            if existing.mappings().first():
                return standard_response(
                    409, "REGISTRO_DUPLICADO: ya existe tasa para esa moneda en esa fecha. Use PUT para actualizar", None
                )

            result = await self.db.execute(text(st.INSERT_TASA), data.model_dump())
            row = result.mappings().first()
            await self.db.commit()
            return standard_response(201, "Tasa registrada exitosamente", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)

    async def get_tasas(self, limit: int = 50, offset: int = 0) -> dict:
        try:
            result = await self.db.execute(
                text(st.SELECT_TASAS_PAGINATED), {"limit": limit, "offset": offset}
            )
            rows = [dict(r) for r in result.mappings().all()]
            total_result = await self.db.execute(text(st.SELECT_TASAS_COUNT))
            total = total_result.scalar() or 0
            return standard_response(
                200,
                f"Listado de tasas (total={total})",
                {"items": rows, "total": total, "limit": limit, "offset": offset},
            )
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def get_tasa_by_id(self, tasa_id: int) -> dict:
        try:
            result = await self.db.execute(
                text(st.SELECT_TASA_BY_ID), {"tasa_id": tasa_id}
            )
            row = result.mappings().first()
            if not row:
                return standard_response(404, "Tasa no encontrada", None)
            return standard_response(200, "Tasa encontrada", dict(row))
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def get_tasa_actual(self, moneda_id: int) -> dict:
        """Retorna la tasa mas reciente de una moneda (helper para facturacion)."""
        try:
            result = await self.db.execute(
                text(st.SELECT_TASA_BY_MONEDA), {"moneda_id": moneda_id}
            )
            row = result.mappings().first()
            if not row:
                return standard_response(
                    404, f"DEBE_CARGAR_TASA_DEL_DIA: no hay tasa registrada para la moneda {moneda_id}", None
                )
            return standard_response(200, "Tasa actual", dict(row))
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def get_tasa_by_fecha(self, moneda_id: int, fecha: date_type) -> dict:
        """Retorna la tasa de una moneda en una fecha especifica."""
        try:
            result = await self.db.execute(
                text(st.SELECT_TASA_BY_MONEDA_FECHA),
                {"moneda_id": moneda_id, "fecha": fecha},
            )
            row = result.mappings().first()
            if not row:
                return standard_response(
                    404, f"No hay tasa para la moneda {moneda_id} en fecha {fecha}", None
                )
            return standard_response(200, "Tasa encontrada", dict(row))
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def update_tasa(self, tasa_id: int, data: TasaCambioUpdateRequest) -> dict:
        try:
            existing = await self.db.execute(
                text(st.SELECT_TASA_BY_ID), {"tasa_id": tasa_id}
            )
            if not existing.mappings().first():
                return standard_response(404, "Tasa no encontrada", None)

            payload = data.model_dump(exclude_unset=True)
            payload["tasa_id"] = tasa_id

            result = await self.db.execute(text(st.UPDATE_TASA), payload)
            row = result.mappings().first()
            await self.db.commit()
            return standard_response(200, "Tasa actualizada", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)

    async def delete_tasa(self, tasa_id: int) -> dict:
        try:
            result = await self.db.execute(
                text(st.DELETE_TASA), {"tasa_id": tasa_id}
            )
            row = result.mappings().first()
            if not row:
                return standard_response(404, "Tasa no encontrada", None)
            await self.db.commit()
            return standard_response(200, "Tasa eliminada", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)
