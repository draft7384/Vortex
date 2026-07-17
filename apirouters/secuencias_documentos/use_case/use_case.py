"""
Logica de negocio del modulo Secuencias de Documentos.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.responses import standard_response
from apirouters.secuencias_documentos.models.models import (
    SecuenciaCreateRequest,
    SecuenciaUpdateRequest,
    InicializarSecuenciasRequest,
)
from apirouters.secuencias_documentos.statement import statement as st


# Secuencias estandar que se crean por defecto al inicializar un punto de emision
SECUENCIAS_DEFAULT = [
    ("FACTURA", "FAC"),
    ("NOTA_ENTREGA", "NE"),
    ("PRESUPUESTO", "PRES"),
    ("PEDIDO", "PED"),
    ("NOTA_CREDITO", "NC"),
    ("NOTA_DEBITO", "ND"),
]


class SecuenciasDocumentosUseCase:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_secuencia(self, data: SecuenciaCreateRequest) -> dict:
        try:
            existing = await self.db.execute(
                text(st.SELECT_SECUENCIA_BY_PUNTO_TIPO),
                {"punto_emision_id": data.punto_emision_id, "tipo_documento": data.tipo_documento},
            )
            if existing.mappings().first():
                return standard_response(
                    409, f"REGISTRO_DUPLICADO: ya existe secuencia para ({data.punto_emision_id}, {data.tipo_documento})", None
                )

            result = await self.db.execute(text(st.INSERT_SECUENCIA), data.model_dump())
            row = result.mappings().first()
            await self.db.commit()
            return standard_response(201, "Secuencia creada exitosamente", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)

    async def inicializar_secuencias(self, data: InicializarSecuenciasRequest) -> dict:
        """
        Crea las 6 secuencias estandar (FACTURA, NC, ND, NE, PRES, PED)
        para un punto de emision si no existen.
        """
        try:
            creadas = []
            for tipo, prefijo in SECUENCIAS_DEFAULT:
                existing = await self.db.execute(
                    text(st.SELECT_SECUENCIA_BY_PUNTO_TIPO),
                    {"punto_emision_id": data.punto_emision_id, "tipo_documento": tipo},
                )
                if existing.mappings().first():
                    continue
                result = await self.db.execute(
                    text(st.INSERT_SECUENCIA),
                    {
                        "punto_emision_id": data.punto_emision_id,
                        "tipo_documento": tipo,
                        "prefijo": prefijo,
                        "proximo_numero": 1,
                        "numero_actual": 0,
                        "activo": True,
                    },
                )
                creadas.append(dict(result.mappings().first()))

            await self.db.commit()
            return standard_response(
                201,
                f"Secuencias inicializadas ({len(creadas)} nuevas)",
                {"punto_emision_id": data.punto_emision_id, "secuencias_creadas": creadas},
            )
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)

    async def get_secuencias(self, limit: int = 50, offset: int = 0) -> dict:
        try:
            result = await self.db.execute(
                text(st.SELECT_SECUENCIAS_PAGINATED), {"limit": limit, "offset": offset}
            )
            rows = [dict(r) for r in result.mappings().all()]
            total_result = await self.db.execute(text(st.SELECT_SECUENCIAS_COUNT))
            total = total_result.scalar() or 0
            return standard_response(
                200,
                f"Listado de secuencias (total={total})",
                {"items": rows, "total": total, "limit": limit, "offset": offset},
            )
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def get_secuencia_by_id(self, secuencia_id: int) -> dict:
        try:
            result = await self.db.execute(
                text(st.SELECT_SECUENCIA_BY_ID), {"secuencia_id": secuencia_id}
            )
            row = result.mappings().first()
            if not row:
                return standard_response(404, "Secuencia no encontrada", None)
            return standard_response(200, "Secuencia encontrada", dict(row))
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def get_secuencias_by_punto(self, punto_emision_id: int) -> dict:
        try:
            result = await self.db.execute(
                text(st.SELECT_SECUENCIAS_BY_PUNTO), {"punto_emision_id": punto_emision_id}
            )
            rows = [dict(r) for r in result.mappings().all()]
            return standard_response(
                200, f"Secuencias del punto {punto_emision_id} ({len(rows)} total)", rows
            )
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def update_secuencia(self, secuencia_id: int, data: SecuenciaUpdateRequest) -> dict:
        try:
            existing = await self.db.execute(
                text(st.SELECT_SECUENCIA_BY_ID), {"secuencia_id": secuencia_id}
            )
            if not existing.mappings().first():
                return standard_response(404, "Secuencia no encontrada", None)

            payload = data.model_dump(exclude_unset=True)
            payload["secuencia_id"] = secuencia_id

            result = await self.db.execute(text(st.UPDATE_SECUENCIA), payload)
            row = result.mappings().first()
            await self.db.commit()
            return standard_response(200, "Secuencia actualizada", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)

    async def delete_secuencia(self, secuencia_id: int) -> dict:
        try:
            result = await self.db.execute(
                text(st.DELETE_SECUENCIA), {"secuencia_id": secuencia_id}
            )
            row = result.mappings().first()
            if not row:
                return standard_response(404, "Secuencia no encontrada", None)
            await self.db.commit()
            return standard_response(200, "Secuencia desactivada", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)
