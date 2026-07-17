"""
Logica de negocio del modulo Vendedores.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.responses import standard_response
from apirouters.vendedores.models.models import (
    VendedorCreateRequest,
    VendedorUpdateRequest,
)
from apirouters.vendedores.statement import statement as st


class VendedoresUseCase:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_vendedor(self, data: VendedorCreateRequest) -> dict:
        try:
            existing = await self.db.execute(
                text(st.SELECT_VENDEDOR_BY_CODIGO), {"codigo": data.codigo}
            )
            if existing.mappings().first():
                return standard_response(
                    409, "REGISTRO_DUPLICADO: ya existe un vendedor con ese codigo", None
                )

            result = await self.db.execute(text(st.INSERT_VENDEDOR), data.model_dump())
            row = result.mappings().first()
            await self.db.commit()
            return standard_response(201, "Vendedor creado exitosamente", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)

    async def get_vendedores(self, limit: int = 50, offset: int = 0) -> dict:
        try:
            result = await self.db.execute(
                text(st.SELECT_VENDEDORES_PAGINATED), {"limit": limit, "offset": offset}
            )
            rows = [dict(r) for r in result.mappings().all()]
            total_result = await self.db.execute(text(st.SELECT_VENDEDORES_COUNT))
            total = total_result.scalar() or 0
            return standard_response(
                200,
                f"Listado de vendedores (total={total})",
                {"items": rows, "total": total, "limit": limit, "offset": offset},
            )
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def get_vendedor_by_id(self, vendedor_id: int) -> dict:
        try:
            result = await self.db.execute(
                text(st.SELECT_VENDEDOR_BY_ID), {"vendedor_id": vendedor_id}
            )
            row = result.mappings().first()
            if not row:
                return standard_response(404, "Vendedor no encontrado", None)
            return standard_response(200, "Vendedor encontrado", dict(row))
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def search_vendedores(self, keyword: str) -> dict:
        try:
            if not keyword or len(keyword.strip()) < 2:
                return standard_response(400, "KEYWORD_REQUERIDO: minimo 2 caracteres", None)
            result = await self.db.execute(
                text(st.SEARCH_VENDEDORES_BY_KEYWORD), {"keyword": f"%{keyword.strip()}%"}
            )
            rows = [dict(r) for r in result.mappings().all()]
            return standard_response(200, f"{len(rows)} resultados para '{keyword}'", rows)
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def update_vendedor(self, vendedor_id: int, data: VendedorUpdateRequest) -> dict:
        try:
            existing = await self.db.execute(
                text(st.SELECT_VENDEDOR_BY_ID), {"vendedor_id": vendedor_id}
            )
            if not existing.mappings().first():
                return standard_response(404, "Vendedor no encontrado", None)

            # COALESCE espera TODOS los params nombrados; enviamos los no seteados como None
            payload = data.model_dump()
            payload["vendedor_id"] = vendedor_id

            result = await self.db.execute(text(st.UPDATE_VENDEDOR), payload)
            row = result.mappings().first()
            await self.db.commit()
            return standard_response(200, "Vendedor actualizado", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)

    async def delete_vendedor(self, vendedor_id: int) -> dict:
        try:
            result = await self.db.execute(
                text(st.DELETE_VENDEDOR), {"vendedor_id": vendedor_id}
            )
            row = result.mappings().first()
            if not row:
                return standard_response(404, "Vendedor no encontrado", None)
            await self.db.commit()
            return standard_response(200, "Vendedor desactivado", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)
