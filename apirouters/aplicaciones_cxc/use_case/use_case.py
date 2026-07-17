"""
Logica de negocio del modulo Aplicaciones CxC.
Crea aplicaciones manuales entre pagos y deudas, y permite reversar aplicaciones.
"""
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apirouters.aplicaciones_cxc.models.models import (
    AplicacionCxcCreateRequest,
    AplicacionCxcReverseRequest,
)
from apirouters.aplicaciones_cxc.statement import statement as st
from apirouters.auth.use_case.use_case import CurrentUser
from core.responses import standard_response


# Tipos de movimiento que son "deuda" (origen: factura, ND)
TIPOS_DEUDA = ("FACTURA", "NOTA_DEBITO")
# Tipos de movimiento que son "pago" (origen: abono, retencion, anticipo, NC)
TIPOS_PAGO = ("ABONO", "RETENCION_IVA", "RETENCION_ISLR", "ANTICIPO", "NOTA_CREDITO")


def _d(x) -> Decimal:
    """Convierte a Decimal para evitar problemas de punto flotante con NUMERIC de PG."""
    if x is None:
        return Decimal("0")
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x))


class AplicacionesCxcUseCase:
    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================
    # CREATE aplicacion manual
    # =========================================================
    async def create_aplicacion(
        self, data: AplicacionCxcCreateRequest, current_user: CurrentUser
    ) -> dict:
        try:
            # 1) Validar ambos movimientos
            mov_pago = (await self.db.execute(
                text(st.SELECT_MOVIMIENTO_BY_ID), {"movimiento_id": data.movimiento_pago_id}
            )).mappings().first()
            if not mov_pago:
                return standard_response(404, "MOVIMIENTO_NO_ENCONTRADO: el movimiento de pago no existe",
                                         {"movimiento_id": data.movimiento_pago_id})

            mov_deuda = (await self.db.execute(
                text(st.SELECT_MOVIMIENTO_BY_ID), {"movimiento_id": data.movimiento_deuda_id}
            )).mappings().first()
            if not mov_deuda:
                return standard_response(404, "MOVIMIENTO_NO_ENCONTRADO: el movimiento de deuda no existe",
                                         {"movimiento_id": data.movimiento_deuda_id})

            # 2) Mismo cliente
            if mov_pago["cliente_id"] != mov_deuda["cliente_id"]:
                return standard_response(400, "MOVIMIENTOS_NO_COMPATIBLES: el pago y la deuda no son del mismo cliente",
                                         {"cliente_pago": int(mov_pago["cliente_id"]), "cliente_deuda": int(mov_deuda["cliente_id"])})

            # 3) Tipos correctos
            if mov_pago["tipo_movimiento"] not in TIPOS_PAGO:
                return standard_response(400, "MOVIMIENTO_NO_ES_PAGO: el movimiento_pago_id no es un pago/retencion/anticipo/NC",
                                         {"movimiento_id": data.movimiento_pago_id, "tipo_movimiento": mov_pago["tipo_movimiento"]})
            if mov_deuda["tipo_movimiento"] not in TIPOS_DEUDA:
                return standard_response(400, "MOVIMIENTO_NO_ES_DEUDA: el movimiento_deuda_id no es FACTURA ni NOTA_DEBITO",
                                         {"movimiento_id": data.movimiento_deuda_id, "tipo_movimiento": mov_deuda["tipo_movimiento"]})

            # 4) Estados
            if mov_pago["estado"] != "EMITIDO":
                return standard_response(400, "MOVIMIENTO_NO_APLICABLE: el pago no esta en estado EMITIDO",
                                         {"movimiento_id": data.movimiento_pago_id, "estado_actual": mov_pago["estado"]})
            if mov_deuda["estado"] != "EMITIDO":
                return standard_response(400, "MOVIMIENTO_NO_APLICABLE: la deuda no esta en estado EMITIDO",
                                         {"movimiento_id": data.movimiento_deuda_id, "estado_actual": mov_deuda["estado"]})

            # 5) Saldo suficiente
            saldo_deuda = float(mov_deuda["saldo_original"])
            if data.monto_aplicado > saldo_deuda + 0.005:
                return standard_response(400, "MONTO_APLICADO_EXCEDE_SALDO",
                                         {"saldo_actual": round(saldo_deuda, 2), "monto_intentado": round(data.monto_aplicado, 2)})

            # 6) Conversion a local
            tasa_pago = float(mov_pago["tasa_cambio"])
            tasa_deuda = float(mov_deuda["tasa_cambio"])
            factor = tasa_deuda / tasa_pago if tasa_pago > 0 else 1.0
            monto_aplicado_local = round(data.monto_aplicado * factor, 2)

            # 7) Transaccion
            try:
                aplic_row = (await self.db.execute(
                    text(st.INSERT_APLICACION_CXC), {
                        "movimiento_pago_id": data.movimiento_pago_id,
                        "movimiento_deuda_id": data.movimiento_deuda_id,
                        "monto_aplicado_original": _d(data.monto_aplicado),
                        "monto_aplicado_local": _d(monto_aplicado_local),
                        "aplicado_por": current_user.id,
                    }
                )).mappings().first()

                result = await self.db.execute(
                    text(st.UPDATE_MOVIMIENTO_SALDO_RESTAR_CONDICIONAL), {
                        "movimiento_id": data.movimiento_deuda_id,
                        "monto": _d(data.monto_aplicado),
                        "monto_local": _d(monto_aplicado_local),
                    }
                )
                if result.rowcount == 0:
                    await self.db.rollback()
                    return standard_response(409, "SALDO_INSUFICIENTE_EN_TRANSACCION: race condition",
                                             {"movimiento_id": data.movimiento_deuda_id})

                await self.db.commit()
                return standard_response(201, "Aplicacion creada", _serializar_aplicacion(dict(aplic_row)))

            except IntegrityError as e:
                await self.db.rollback()
                return standard_response(409, f"REGISTRO_DUPLICADO: {str(e.orig)}", None)

        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)

    # =========================================================
    # REVERSAR aplicacion
    # =========================================================
    async def reversar_aplicacion(
        self, aplicacion_id: int, data: AplicacionCxcReverseRequest, current_user: CurrentUser
    ) -> dict:
        try:
            aplic_row = (await self.db.execute(
                text(st.SELECT_APLICACION_BY_ID), {"aplicacion_id": aplicacion_id}
            )).mappings().first()

            if not aplic_row:
                return standard_response(404, "APLICACION_NO_ENCONTRADA: aplicacion no existe",
                                         {"aplicacion_id": aplicacion_id})

            if aplic_row["reversada"]:
                return standard_response(400, "APLICACION_YA_REVERSADA: esta aplicacion ya fue reversada",
                                         {"aplicacion_id": aplicacion_id,
                                          "reversada_por": int(aplic_row["reversada_por"]) if aplic_row["reversada_por"] else None,
                                          "reversada_en": aplic_row["reversada_en"].isoformat() if aplic_row["reversada_en"] else None})

            # Transaccion
            try:
                result_rev = await self.db.execute(
                    text(st.UPDATE_APLICACION_REVERSAR), {
                        "aplicacion_id": aplicacion_id,
                        "usuario_id": current_user.id,
                        "motivo": data.motivo,
                    }
                )
                if result_rev.rowcount == 0:
                    await self.db.rollback()
                    return standard_response(409, "APLICACION_YA_REVERSADA: race condition, otra TX la reverso primero",
                                             {"aplicacion_id": aplicacion_id})

                aplic_rev = result_rev.mappings().first()

                # Restaurar saldo del movimiento de deuda
                await self.db.execute(
                    text(st.UPDATE_MOVIMIENTO_SALDO_SUMAR), {
                        "movimiento_id": aplic_row["movimiento_deuda_id"],
                        "monto_aplicado": _d(aplic_row["monto_aplicado_original"]),
                        "monto_aplicado_local": _d(aplic_row["monto_aplicado_local"]),
                    }
                )

                await self.db.commit()
                return standard_response(200, "Aplicacion reversada", _serializar_aplicacion(dict(aplic_rev)))

            except IntegrityError as e:
                await self.db.rollback()
                return standard_response(409, f"REGISTRO_DUPLICADO: {str(e.orig)}", None)

        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)

    # =========================================================
    # READ aplicacion por id
    # =========================================================
    async def get_aplicacion_by_id(self, aplicacion_id: int) -> dict:
        try:
            row = (await self.db.execute(
                text(st.SELECT_APLICACION_BY_ID), {"aplicacion_id": aplicacion_id}
            )).mappings().first()
            if not row:
                return standard_response(404, "APLICACION_NO_ENCONTRADA: aplicacion no existe", None)
            return standard_response(200, "Aplicacion encontrada", _serializar_aplicacion(dict(row)))
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)


def _serializar_aplicacion(d: dict) -> dict:
    """Convierte tipos no-JSON a string/float."""
    for k, v in list(d.items()):
        if hasattr(v, "isoformat"):
            d[k] = v.isoformat()
        elif hasattr(v, "__float__") and not isinstance(v, (int, float, bool, str)):
            d[k] = float(v)
    return d
