"""
Logica de negocio del modulo Empresa (singleton).
La fila id=1 contiene los datos fiscales del emisor.
"""
import re

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.responses import standard_response
from apirouters.empresa.models.models import EmpresaConfigRequest
from apirouters.empresa.statement import statement as st


RIF_VENEZOLANO_REGEX = re.compile(r"^[VEJGvejg]-\d{7,10}(-\d)?$")


class EmpresaUseCase:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_empresa(self) -> dict:
        try:
            result = await self.db.execute(text(st.SELECT_EMPRESA))
            row = result.mappings().first()
            if not row:
                return standard_response(404, "Configuracion de empresa no encontrada", None)
            return standard_response(200, "Configuracion de empresa", dict(row))
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    async def upsert_empresa(self, data: EmpresaConfigRequest) -> dict:
        """
        Crea o actualiza la fila singleton (id=1).
        """
        if not RIF_VENEZOLANO_REGEX.match(data.rif):
            return standard_response(
                400, "RIF_INVALIDO: el RIF debe tener formato venezolano (ej. J-12345678-9)", None
            )

        # Validar que rango_desde <= rango_hasta cuando ambos vienen
        for prefix in ["factura", "nc", "nd"]:
            desde = getattr(data, f"rango_{prefix}_desde")
            hasta = getattr(data, f"rango_{prefix}_hasta")
            if desde is not None and hasta is not None and desde > hasta:
                return standard_response(
                    400, f"RANGO_INVALIDO: rango_{prefix}_desde ({desde}) no puede ser mayor que rango_{prefix}_hasta ({hasta})", None
                )

        try:
            result = await self.db.execute(text(st.UPSERT_EMPRESA), data.model_dump())
            row = result.mappings().first()
            await self.db.commit()
            return standard_response(200, "Configuracion de empresa guardada", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)
