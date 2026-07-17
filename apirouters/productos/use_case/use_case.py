"""
Logica de negocio del modulo Productos.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.responses import standard_response
from apirouters.productos.models.models import (
    ProductoCreateRequest,
    ProductoUpdateRequest,
)
from apirouters.productos.statement import statement as st


class ProductosUseCase:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_producto(self, data: ProductoCreateRequest) -> dict:
        try:
            existing = await self.db.execute(
                text(st.SELECT_PRODUCTO_BY_CODIGO), {"codigo": data.codigo}
            )
            if existing.mappings().first():
                return standard_response(
                    409, "REGISTRO_DUPLICADO: ya existe un producto con ese codigo", None
                )

            result = await self.db.execute(text(st.INSERT_PRODUCTO), data.model_dump())
            row = result.mappings().first()
            await self.db.commit()
            return standard_response(201, "Producto creado exitosamente", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)

    async def get_productos(self, limit: int = 50, offset: int = 0) -> dict:
        try:
            result = await self.db.execute(
                text(st.SELECT_PRODUCTOS_PAGINATED), {"limit": limit, "offset": offset}
            )
            rows = [dict(r) for r in result.mappings().all()]
            total_result = await self.db.execute(text(st.SELECT_PRODUCTOS_COUNT))
            total = total_result.scalar() or 0
            return standard_response(
                200,
                f"Listado de productos (total={total})",
                {"items": rows, "total": total, "limit": limit, "offset": offset},
            )
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def get_producto_by_id(self, producto_id: int) -> dict:
        try:
            result = await self.db.execute(
                text(st.SELECT_PRODUCTO_BY_ID), {"producto_id": producto_id}
            )
            row = result.mappings().first()
            if not row:
                return standard_response(404, "Producto no encontrado", None)
            return standard_response(200, "Producto encontrado", dict(row))
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def search_productos(self, keyword: str) -> dict:
        try:
            if not keyword or len(keyword.strip()) < 2:
                return standard_response(400, "KEYWORD_REQUERIDO: minimo 2 caracteres", None)
            result = await self.db.execute(
                text(st.SEARCH_PRODUCTOS_BY_KEYWORD), {"keyword": f"%{keyword.strip()}%"}
            )
            rows = [dict(r) for r in result.mappings().all()]
            return standard_response(200, f"{len(rows)} resultados para '{keyword}'", rows)
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def get_productos_bajo_stock(self, umbral: float) -> dict:
        try:
            result = await self.db.execute(
                text(st.SELECT_PRODUCTOS_BAJO_STOCK), {"umbral": umbral}
            )
            rows = [dict(r) for r in result.mappings().all()]
            return standard_response(
                200,
                f"{len(rows)} producto(s) con existencia <= {umbral}",
                rows,
            )
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def update_producto(self, producto_id: int, data: ProductoUpdateRequest) -> dict:
        try:
            existing = await self.db.execute(
                text(st.SELECT_PRODUCTO_BY_ID), {"producto_id": producto_id}
            )
            if not existing.mappings().first():
                return standard_response(404, "Producto no encontrado", None)

            # COALESCE espera TODOS los params nombrados; enviamos los no seteados como None
            payload = data.model_dump()
            payload["producto_id"] = producto_id

            result = await self.db.execute(text(st.UPDATE_PRODUCTO), payload)
            row = result.mappings().first()
            await self.db.commit()
            return standard_response(200, "Producto actualizado", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)

    async def delete_producto(self, producto_id: int) -> dict:
        try:
            result = await self.db.execute(
                text(st.DELETE_PRODUCTO), {"producto_id": producto_id}
            )
            row = result.mappings().first()
            if not row:
                return standard_response(404, "Producto no encontrado", None)
            await self.db.commit()
            return standard_response(200, "Producto desactivado", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)
