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

    async def import_productos_from_excel(self, file: UploadFile) -> dict:
        """Importa productos masivamente desde un archivo Excel."""
        try:
            import pandas as pd
            from io import BytesIO
            
            # Leer archivo Excel
            content = await file.read()
            df = pd.read_excel(BytesIO(content))
            
            # Validar columnas requeridas
            required_cols = ['codigo', 'descripcion', 'precio_base']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return standard_response(400, f"COLUMNAS_FALTANTES: {', '.join(missing_cols)}", None)
            
            total_registros = len(df)
            exitosos = 0
            fallidos = 0
            errores = []
            
            for idx, row in df.iterrows():
                try:
                    # Validar datos basicos
                    if not row['codigo'] or not row['descripcion']:
                        raise ValueError("Codigo y descripcion son requeridos")
                    if row['precio_base'] < 0:
                        raise ValueError("Precio base no puede ser negativo")
                    
                    # Verificar si ya existe
                    existing = await self.db.execute(
                        text(st.SELECT_PRODUCTO_BY_CODIGO), 
                        {"codigo": str(row['codigo'])}
                    )
                    if existing.mappings().first():
                        raise ValueError(f"Producto con codigo '{row['codigo']}' ya existe")
                    
                    # Crear producto
                    producto_data = {
                        "codigo": str(row['codigo']),
                        "descripcion": str(row['descripcion']),
                        "unidad_medida": str(row.get('unidad_medida', 'UND')),
                        "precio_base": float(row['precio_base']),
                        "impuesto_pct": float(row.get('impuesto_pct', 16.0)),
                        "existencia": float(row.get('existencia', 0.0)),
                        "es_servicio": bool(row.get('es_servicio', False)),
                        "activo": True
                    }
                    
                    result = await self.db.execute(text(st.INSERT_PRODUCTO), producto_data)
                    await self.db.commit()
                    exitosos += 1
                    
                except Exception as e:
                    fallidos += 1
                    errores.append({
                        "fila": idx + 2,  # +2 porque Excel inicia en 1 y hay header
                        "codigo": row.get('codigo', 'N/A'),
                        "error": str(e)
                    })
                    await self.db.rollback()
            
            return standard_response(
                200,
                f"Importacion completada: {exitosos} exitosos, {fallidos} fallidos",
                {
                    "total_registros": total_registros,
                    "exitosos": exitosos,
                    "fallidos": fallidos,
                    "errores": errores
                }
            )
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)
