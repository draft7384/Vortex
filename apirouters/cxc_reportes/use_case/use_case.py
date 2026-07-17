"""
Logica de negocio del modulo Reportes CxC.
- GET /cxc-reportes/movimientos  (listado con filtros)
- GET /cxc-reportes/movimientos/{id} (detalle + aplicaciones)
- GET /cxc-reportes/estado-cuenta/{cliente_id}
- GET /cxc-reportes/antiguedad-saldos (rangos configurables)
"""
import json
import logging
from datetime import date as date_type, date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apirouters.auth.use_case.use_case import CurrentUser
from apirouters.clientes.statement import statement as cli_st
from apirouters.cxc_reportes.statement import statement as st
from core.responses import standard_response

logger = logging.getLogger(__name__)

# Default si no existe el parametro 'cxc_rangos_antiguedad'
# Formato: cotas superiores (sin 0 inicial). Genera buckets: 0-30, 31-60, 61-90, +90
RANGOS_DEFAULT = [30, 60, 90]


class CxcReportesUseCase:
    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================
    # LISTADO DE MOVIMIENTOS
    # =========================================================
    async def get_movimientos(
        self,
        cliente_id: int | None = None,
        tipo: str | None = None,
        estado: str | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        solo_pendientes: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        try:
            params = {
                "cliente_id": cliente_id,
                "tipo": tipo,
                "estado": estado,
                "fecha_desde": fecha_desde,
                "fecha_hasta": fecha_hasta,
                "solo_pendientes": solo_pendientes,
                "limit": limit,
                "offset": offset,
            }
            result = await self.db.execute(text(st.SELECT_MOVIMIENTOS_PAGINATED), params)
            rows = [dict(r) for r in result.mappings().all()]
            items = [_serializar_movimiento(r) for r in rows]

            total = (await self.db.execute(
                text(st.SELECT_MOVIMIENTOS_COUNT), params
            )).scalar() or 0

            return standard_response(
                200,
                f"Listado de movimientos (total={total})",
                {"items": items, "total": int(total), "limit": limit, "offset": offset},
            )
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    # =========================================================
    # DETALLE DE MOVIMIENTO
    # =========================================================
    async def get_movimiento_by_id(self, movimiento_id: int) -> dict:
        try:
            mov_row = (await self.db.execute(
                text(st.SELECT_MOVIMIENTO_BY_ID), {"movimiento_id": movimiento_id}
            )).mappings().first()
            if not mov_row:
                return standard_response(404, "MOVIMIENTO_NO_ENCONTRADO: movimiento no existe", None)

            aplic_rows = (await self.db.execute(
                text(st.SELECT_APLICACIONES_BY_MOVIMIENTO), {"movimiento_id": movimiento_id}
            )).mappings().all()

            mov = _serializar_movimiento(dict(mov_row))
            mov["aplicaciones"] = [_serializar_aplicacion(dict(a)) for a in aplic_rows]

            return standard_response(200, "Movimiento encontrado", mov)
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    # =========================================================
    # ESTADO DE CUENTA POR CLIENTE
    # =========================================================
    async def get_estado_cuenta(self, cliente_id: int) -> dict:
        try:
            cli_row = (await self.db.execute(
                text(cli_st.SELECT_CLIENTE_BY_ID), {"cliente_id": cliente_id}
            )).mappings().first()
            if not cli_row or not cli_row["activo"]:
                return standard_response(404, "CLIENTE_NO_ENCONTRADO: cliente no existe o esta inactivo", None)

            movs = (await self.db.execute(
                text(st.SELECT_ESTADO_CUENTA), {"cliente_id": cliente_id}
            )).mappings().all()

            # Saldo total pendiente = suma de saldos de movimientos tipo FACTURA / NOTA_DEBITO
            TIPOS_DEUDA = ("FACTURA", "NOTA_DEBITO")
            saldo_total_pendiente = sum(
                float(m["saldo_original"]) for m in movs if m["tipo_movimiento"] in TIPOS_DEUDA
            )
            saldo_total_pendiente_local = sum(
                float(m["saldo_local"]) for m in movs if m["tipo_movimiento"] in TIPOS_DEUDA
            )

            movimientos = [_serializar_movimiento(dict(m)) for m in movs]
            # Anotar el tipo para cada uno
            for i, m in enumerate(movs):
                movimientos[i]["es_deuda"] = m["tipo_movimiento"] in TIPOS_DEUDA

            return standard_response(
                200,
                f"Estado de cuenta de {cli_row['nombre_razon_social']}",
                {
                    "cliente_id": int(cli_row["id"]),
                    "cliente_nombre": cli_row["nombre_razon_social"],
                    "saldo_total_pendiente": round(saldo_total_pendiente, 2),
                    "saldo_total_pendiente_local": round(saldo_total_pendiente_local, 2),
                    "movimientos": movimientos,
                },
            )
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    # =========================================================
    # ANTIGUEDAD DE SALDOS
    # =========================================================
    async def get_antiguedad_saldos(
        self,
        cliente_id: int | None = None,
        rangos_override: str | None = None,
    ) -> dict:
        try:
            rangos = await self._resolver_rangos(rangos_override)
            hoy = date_type.today()

            rows = (await self.db.execute(
                text(st.SELECT_ANTIGUEDAD_SALDOS), {"cliente_id": cliente_id}
            )).mappings().all()

            # Inicializar buckets
            buckets_def = self._armar_buckets(rangos)
            buckets_data = [
                {
                    "rango": label,
                    "desde_dias": desde,
                    "hasta_dias": hasta,
                    "cantidad_documentos": 0,
                    "monto_total": 0.0,
                    "monto_total_local": 0.0,
                }
                for (label, desde, hasta) in buckets_def
            ]

            total_pendiente = 0.0
            total_pendiente_local = 0.0

            for r in rows:
                dias = int(r["dias_vencidos"])
                monto = float(r["saldo_original"])
                monto_local = float(r["saldo_local"])
                total_pendiente += monto
                total_pendiente_local += monto_local

                # Clasificar en bucket
                idx = self._clasificar_bucket(dias, rangos)
                buckets_data[idx]["cantidad_documentos"] += 1
                buckets_data[idx]["monto_total"] += monto
                buckets_data[idx]["monto_total_local"] += monto_local

            for b in buckets_data:
                b["monto_total"] = round(b["monto_total"], 2)
                b["monto_total_local"] = round(b["monto_total_local"], 2)

            return standard_response(
                200,
                "Antiguedad de saldos generada",
                {
                    "fecha_corte": hoy.isoformat(),
                    "rangos_usados": rangos,
                    "total_pendiente": round(total_pendiente, 2),
                    "total_pendiente_local": round(total_pendiente_local, 2),
                    "buckets": buckets_data,
                },
            )
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    # ---------------------------------------------------------
    # Helpers privados
    # ---------------------------------------------------------
    async def _resolver_rangos(self, rangos_override: str | None) -> list[int]:
        """Resuelve los rangos en orden: query param > parametro_sistema > default."""
        if rangos_override:
            try:
                parsed = [int(x.strip()) for x in rangos_override.split(",") if x.strip()]
                if len(parsed) >= 2 and all(parsed[i] < parsed[i+1] for i in range(len(parsed)-1)):
                    return parsed
                logger.warning("Override de rangos invalido, uso default: %s", rangos_override)
            except (ValueError, AttributeError):
                logger.warning("Override de rangos no parseable, uso default: %s", rangos_override)

        # Leer de parametros_sistema
        try:
            row = (await self.db.execute(
                text(st.SELECT_RANGOS_ANTIGUEDAD)
            )).mappings().first()
            if row and row["valor"]:
                valor = row["valor"]
                # asyncpg con JSONB devuelve ya deserializado (list/dict). Si llega como string, parsearlo.
                if isinstance(valor, str):
                    parsed = json.loads(valor)
                else:
                    parsed = valor
                if isinstance(parsed, list) and len(parsed) >= 2:
                    parsed_int = [int(x) for x in parsed]
                    if all(parsed_int[i] < parsed_int[i+1] for i in range(len(parsed_int)-1)):
                        return parsed_int
                logger.warning("Parametro cxc_rangos_antiguedad con formato invalido: %s", row["valor"])
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning("Error parseando cxc_rangos_antiguedad: %s", e)
        except Exception as e:
            logger.warning("Error leyendo cxc_rangos_antiguedad: %s", e)

        return RANGOS_DEFAULT

    def _armar_buckets(self, rangos: list[int]) -> list[tuple[str, int, int | None]]:
        """
        A partir de [30, 60, 90] genera los buckets:
          [('0-30', 0, 30), ('31-60', 31, 60), ('61-90', 61, 90), ('+90', 91, None)]
        'rangos' se interpreta como las COTAS SUPERIORES de cada bucket:
        - bucket 0: 0..rangos[0]   (ej. 0..30)
        - bucket 1: rangos[0]+1..rangos[1]   (ej. 31..60)
        - bucket N: rangos[N-1]+1..rangos[N]
        - bucket final: rangos[-1]+1..inf

        Esto significa que el cliente debe pasar [30, 60, 90], no [0, 30, 60, 90].
        Si pasa [0, 30, 60, 90] (con cero inicial), se lo descartamos para evitar
        un bucket "0-0" sin sentido.
        """
        # Si el primer elemento es 0, descartarlo
        if rangos and rangos[0] == 0:
            rangos = rangos[1:]
        if len(rangos) < 1:
            rangos = [30, 60, 90]

        result = []
        for i, cota in enumerate(rangos):
            desde = 0 if i == 0 else rangos[i-1] + 1
            hasta = cota
            label = f"{desde}-{hasta}"
            result.append((label, desde, hasta))
        # Bucket "y mas" para lo que exceda el ultimo rango
        result.append((f"+{rangos[-1]}", rangos[-1] + 1, None))
        return result

    def _clasificar_bucket(self, dias_vencidos: int, rangos: list[int]) -> int:
        """
        Retorna el indice del bucket. 'rangos' son las cotas superiores.
        dias_vencidos <= 0 (no vencido o vence hoy) -> bucket 0.
        dias_vencidos > 0 -> busca el primer i tal que dias_vencidos <= rangos[i].
        Si supera todas las cotas -> bucket final (len(rangos)).
        """
        if rangos and rangos[0] == 0:
            rangos = rangos[1:]
        if dias_vencidos <= 0:
            return 0
        for i, cota in enumerate(rangos):
            if dias_vencidos <= cota:
                return i
        return len(rangos)


def _serializar_movimiento(d: dict) -> dict:
    for k, v in list(d.items()):
        if hasattr(v, "isoformat"):
            d[k] = v.isoformat()
        elif hasattr(v, "__float__") and not isinstance(v, (int, float, bool, str)):
            d[k] = float(v)
    return d


def _serializar_aplicacion(d: dict) -> dict:
    for k, v in list(d.items()):
        if hasattr(v, "isoformat"):
            d[k] = v.isoformat()
        elif hasattr(v, "__float__") and not isinstance(v, (int, float, bool, str)):
            d[k] = float(v)
    return d
