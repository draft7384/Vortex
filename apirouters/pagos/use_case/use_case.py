"""
Logica de negocio del modulo Pagos / CxC.
Registra un pago (ABONO / RETENCION_IVA / RETENCION_ISLR / ANTICIPO / NC / ND)
y lo aplica contra deudas pendientes en una sola transaccion.

Modos de aplicacion:
- AUTO: backend aplica FIFO contra las deudas mas viejas con saldo pendiente.
- MANUAL: usa data.aplicaciones explicitamente, validando que los movimientos
  existan y que los montos no excedan los saldos.
"""
from datetime import date as date_type
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apirouters.auth.use_case.use_case import CurrentUser
from apirouters.clientes.statement import statement as cli_st
from apirouters.pagos.models.models import (
    AplicacionPagoItem,
    PagoCreateRequest,
)
from apirouters.pagos.statement import statement as st
from core.responses import standard_response


def _d(x) -> Decimal:
    """Convierte a Decimal para evitar problemas de punto flotante con NUMERIC de PG."""
    if x is None:
        return Decimal("0")
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x))


class PagosUseCase:
    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================
    # CREATE PAGO
    # =========================================================
    async def create_pago(
        self, data: PagoCreateRequest, current_user: CurrentUser
    ) -> dict:
        try:
            # ---- FASE 1: Validaciones sin escritura ----
            fecha_pago = data.fecha_pago or date_type.today()

            # 1) Cliente
            cli_row = (await self.db.execute(
                text(cli_st.SELECT_CLIENTE_BY_ID), {"cliente_id": data.cliente_id}
            )).mappings().first()
            if not cli_row or not cli_row["activo"]:
                return standard_response(404, "CLIENTE_NO_ENCONTRADO: cliente no existe o esta inactivo", None)

            # 2) Validacion de RETENCION_IVA: solo para contribuyentes especiales
            if data.tipo == "RETENCION_IVA" and not cli_row["es_contribuyente_especial"]:
                return standard_response(
                    400,
                    "CLIENTE_NO_ES_CONTRIBUYENTE_ESPECIAL: solo se acepta RETENCION_IVA de clientes con es_contribuyente_especial=TRUE",
                    {"cliente_id": data.cliente_id, "cliente_nombre": cli_row["nombre_razon_social"], "tipo_solicitado": data.tipo},
                )

            # 3) Moneda
            mon_row = (await self.db.execute(
                text(st.SELECT_MONEDA_BY_ID), {"moneda_id": data.moneda_id}
            )).mappings().first()
            if not mon_row or not mon_row["activo"]:
                return standard_response(404, "MONEDA_NO_ENCONTRADA: moneda no existe o esta inactiva", None)

            # 4) Tasa del dia
            tasa_row = (await self.db.execute(
                text(st.SELECT_TASA_BY_MONEDA_FECHA), {"moneda_id": data.moneda_id, "fecha": fecha_pago}
            )).mappings().first()
            if not tasa_row:
                return standard_response(
                    400,
                    "DEBE_CARGAR_TASA_DEL_DIA: no hay tasa de cambio cargada para esa moneda en esa fecha",
                    {"moneda_id": data.moneda_id, "fecha": fecha_pago.isoformat()},
                )
            tasa = float(tasa_row["tasa"])
            monto_local = round(data.monto_pago * tasa, 2)

            # 5) Resolver aplicaciones
            aplicaciones_resueltas = []  # lista de dicts {movimiento_deuda_id, monto_aplicado, monto_aplicado_local}
            saldo_a_favor = 0.0

            if data.tipo == "ANTICIPO":
                # Anticipo: no se aplica a ninguna deuda. Queda como saldo a favor.
                # No validamos data.aplicaciones (el validator ya rechazo MANUAL).
                pass
            elif data.modo_aplicacion == "MANUAL":
                for aplic in data.aplicaciones or []:
                    err, factor_conversion = await self._validar_aplicacion_manual(aplic, data, tasa)
                    if err is not None:
                        return err  # 400/404 envuelto en standard_response
                    aplicaciones_resueltas.append({
                        "movimiento_deuda_id": aplic.movimiento_deuda_id,
                        "monto_aplicado": round(aplic.monto_aplicado, 2),
                        "monto_aplicado_local": round(aplic.monto_aplicado * factor_conversion, 2),
                    })
            else:  # AUTO y no ANTICIPO
                aplicaciones_resueltas, saldo_a_favor = await self._resolver_aplicaciones_fifo(
                    cliente_id=data.cliente_id,
                    monto_pago=data.monto_pago,
                    tasa_pago=tasa,
                )

            # ---- FASE 2: Transaccion atomica ----
            try:
                # 1) INSERT del movimiento del pago
                mov_pago_id = (await self.db.execute(
                    text(st.INSERT_MOVIMIENTO_CXC_PAGO), {
                        "cliente_id": data.cliente_id,
                        "tipo_movimiento": data.tipo,
                        "documento_venta_id": None,
                        "numero_documento": data.numero_documento,
                        "fecha_movimiento": fecha_pago,
                        "fecha_vencimiento": None,
                        "moneda_id": data.moneda_id,
                        "tasa_cambio": _d(tasa),
                        "monto_original": _d(data.monto_pago),
                        "saldo_original": _d(data.monto_pago),
                        "monto_local": _d(monto_local),
                        "saldo_local": _d(monto_local),
                        "estado": "EMITIDO",
                        "registrado_por": current_user.id,
                    }
                )).mappings().first()["id"]

                # 2) INSERT aplicaciones + UPDATE saldos
                for aplic in aplicaciones_resueltas:
                    aplic_row = (await self.db.execute(
                        text(st.INSERT_APLICACION_CXC), {
                            "movimiento_pago_id": mov_pago_id,
                            "movimiento_deuda_id": aplic["movimiento_deuda_id"],
                            "monto_aplicado_original": _d(aplic["monto_aplicado"]),
                            "monto_aplicado_local": _d(aplic["monto_aplicado_local"]),
                            "aplicado_por": current_user.id,
                        }
                    )).mappings().first()

                    result = await self.db.execute(
                        text(st.UPDATE_MOVIMIENTO_SALDO_RESTAR), {
                            "movimiento_id": aplic["movimiento_deuda_id"],
                            "monto_aplicado": _d(aplic["monto_aplicado"]),
                            "monto_aplicado_local": _d(aplic["monto_aplicado_local"]),
                        }
                    )
                    if result.rowcount == 0:
                        await self.db.rollback()
                        return standard_response(
                            409,
                            "SALDO_INSUFICIENTE_EN_TRANSACCION: el saldo del movimiento deuda cambio entre validacion y aplicacion (race condition)",
                            {"movimiento_deuda_id": aplic["movimiento_deuda_id"]},
                        )

                # 3) Commit
                await self.db.commit()

                # 4) Devolver el movimiento con sus aplicaciones
                response = await self.get_movimiento_by_id(mov_pago_id)
                # Anotar saldo a favor si lo hubo (modo AUTO, no ANTICIPO, no se aplico todo)
                if saldo_a_favor > 0 and isinstance(response.get("data"), dict):
                    response["data"]["saldo_a_favor"] = round(saldo_a_favor, 2)
                if data.tipo == "ANTICIPO" and isinstance(response.get("data"), dict):
                    response["data"]["es_anticipo"] = True
                return response

            except IntegrityError as e:
                await self.db.rollback()
                return standard_response(409, f"REGISTRO_DUPLICADO: {str(e.orig)}", None)

        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)

    async def _validar_aplicacion_manual(
        self, aplic: AplicacionPagoItem, data: PagoCreateRequest, tasa_pago: float
    ) -> tuple[dict | None, float]:
        """
        Valida una aplicacion individual. Retorna (error_dict, tasa_deuda).
        Si error_dict no es None, la aplicacion es invalida.
        Si OK, tasa_deuda se usa para calcular monto_aplicado_local.
        """
        mov_row = (await self.db.execute(
            text(st.SELECT_MOVIMIENTO_BY_ID), {"movimiento_id": aplic.movimiento_deuda_id}
        )).mappings().first()

        if not mov_row:
            return standard_response(
                404,
                "MOVIMIENTO_NO_ENCONTRADO: el movimiento de deuda especificado no existe",
                {"movimiento_deuda_id": aplic.movimiento_deuda_id},
            ), 0.0

        if mov_row["cliente_id"] != data.cliente_id:
            return standard_response(
                400,
                "MOVIMIENTOS_NO_COMPATIBLES: el movimiento de deuda no pertenece al cliente del pago",
                {"movimiento_deuda_id": aplic.movimiento_deuda_id, "cliente_pago": data.cliente_id, "cliente_deuda": mov_row["cliente_id"]},
            ), 0.0

        if mov_row["estado"] != "EMITIDO":
            return standard_response(
                400,
                "MOVIMIENTO_NO_APLICABLE: el movimiento de deuda no esta en estado EMITIDO (ya fue pagado o anulado)",
                {"movimiento_deuda_id": aplic.movimiento_deuda_id, "estado_actual": mov_row["estado"]},
            ), 0.0

        if mov_row["tipo_movimiento"] not in ("FACTURA", "NOTA_DEBITO"):
            return standard_response(
                400,
                "MOVIMIENTO_NO_ES_DEUDA: solo se pueden aplicar pagos contra FACTURA o NOTA_DEBITO",
                {"movimiento_deuda_id": aplic.movimiento_deuda_id, "tipo_movimiento": mov_row["tipo_movimiento"]},
            ), 0.0

        saldo_actual = float(mov_row["saldo_original"])
        if aplic.monto_aplicado > saldo_actual + 0.005:
            return standard_response(
                400,
                "MONTO_APLICADO_EXCEDE_SALDO: el monto aplicado es mayor al saldo pendiente del movimiento",
                {
                    "movimiento_deuda_id": aplic.movimiento_deuda_id,
                    "saldo_actual": round(saldo_actual, 2),
                    "monto_intentado": round(aplic.monto_aplicado, 2),
                },
            ), 0.0

        # OK: devolver tasa_deuda / tasa_pago (factor para convertir a local)
        tasa_deuda = float(mov_row["tasa_cambio"])
        factor = tasa_deuda / tasa_pago if tasa_pago > 0 else 1.0
        return None, factor

    async def _resolver_aplicaciones_fifo(
        self, cliente_id: int, monto_pago: float, tasa_pago: float
    ) -> tuple[list[dict], float]:
        """Resuelve aplicaciones en modo AUTO siguiendo orden FIFO por fecha_vencimiento."""
        deudas = (await self.db.execute(
            text(st.SELECT_DEUDAS_PENDIENTES_FIFO), {"cliente_id": cliente_id}
        )).mappings().all()

        aplicaciones = []
        restante = round(monto_pago, 2)

        for deuda in deudas:
            if restante <= 0.005:
                break
            saldo_deuda = float(deuda["saldo_original"])
            aplicar = min(restante, saldo_deuda)
            aplicar = round(aplicar, 2)
            if aplicar <= 0:
                continue
            tasa_deuda = float(deuda["tasa_cambio"])
            aplicar_local = round(aplicar * (tasa_deuda / tasa_pago), 2)
            aplicaciones.append({
                "movimiento_deuda_id": int(deuda["id"]),
                "monto_aplicado": aplicar,
                "monto_aplicado_local": aplicar_local,
            })
            restante = round(restante - aplicar, 2)

        saldo_a_favor = max(restante, 0.0)
        return aplicaciones, saldo_a_favor

    # =========================================================
    # READ
    # =========================================================
    async def get_movimiento_by_id(self, movimiento_id: int) -> dict:
        """Devuelve un movimiento_cxc con sus aplicaciones."""
        try:
            mov_row = (await self.db.execute(
                text(st.SELECT_MOVIMIENTO_BY_ID), {"movimiento_id": movimiento_id}
            )).mappings().first()
            if not mov_row:
                return standard_response(404, "MOVIMIENTO_NO_ENCONTRADO: movimiento no existe", None)

            aplic_rows = (await self.db.execute(
                text(st.SELECT_APLICACIONES_BY_MOVIMIENTO), {"movimiento_id": movimiento_id}
            )).mappings().all()

            mov = dict(mov_row)
            # Convertir fechas y numeric a tipos JSON-serializables
            for k, v in list(mov.items()):
                if hasattr(v, "isoformat"):
                    mov[k] = v.isoformat()
                elif hasattr(v, "__float__") and not isinstance(v, (int, float, bool, str)):
                    mov[k] = float(v)

            mov["aplicaciones"] = []
            for a in aplic_rows:
                ad = dict(a)
                for k, v in list(ad.items()):
                    if hasattr(v, "isoformat"):
                        ad[k] = v.isoformat()
                    elif hasattr(v, "__float__") and not isinstance(v, (int, float, bool, str)):
                        ad[k] = float(v)
                mov["aplicaciones"].append(ad)

            return standard_response(200, "Movimiento encontrado", mov)
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)
