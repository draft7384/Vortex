"""
Logica de negocio del modulo Documentos de Venta.
Es el nucleo transaccional: crea el documento + detalle + mov_cxc + descuento de stock
en una sola transaccion. Tambien implementa la anulacion segura.
Soporta FACTURA, NOTA_ENTREGA, PRESUPUESTO, PEDIDO, NOTA_CREDITO y NOTA_DEBITO.
"""
from datetime import date as date_type
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apirouters.auth.use_case.use_case import CurrentUser
from apirouters.clientes.statement import statement as cli_st
from apirouters.documentos_ventas.models.models import (
    DocumentoVentaAnularRequest,
    DocumentoVentaCreateRequest,
)
from apirouters.documentos_ventas.statement import statement as st
from apirouters.monedas.statement import statement as mon_st
from apirouters.productos.statement import statement as prod_st
from apirouters.puntos_emision.statement import statement as pe_st
from apirouters.secuencias_documentos.statement import statement as seq_st
from apirouters.tasas_cambio.statement import statement as tc_st
from apirouters.vendedores.statement import statement as ven_st
from core.responses import standard_response


def _d(x) -> Decimal:
    """Convierte a Decimal para evitar problemas de punto flotante con NUMERIC de PG."""
    if x is None:
        return Decimal("0")
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x))


class DocumentosVentasUseCase:
    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================
    # CREATE
    # =========================================================
    async def create_documento(
        self, data: DocumentoVentaCreateRequest, current_user: CurrentUser
    ) -> dict:
        try:
            # ---- FASE 1: Validaciones sin escritura ----
            fecha_emision = data.fecha_emision or date_type.today()

            # 1) Cliente
            cli_row = (await self.db.execute(
                text(cli_st.SELECT_CLIENTE_BY_ID), {"cliente_id": data.cliente_id}
            )).mappings().first()
            if not cli_row or not cli_row["activo"]:
                return standard_response(404, "CLIENTE_NO_ENCONTRADO: cliente no existe o esta inactivo", None)

            # 2) Vendedor (opcional)
            if data.vendedor_id is not None:
                ven_row = (await self.db.execute(
                    text(ven_st.SELECT_VENDEDOR_BY_ID), {"vendedor_id": data.vendedor_id}
                )).mappings().first()
                if not ven_row or not ven_row["activo"]:
                    return standard_response(404, "VENDEDOR_NO_ENCONTRADO: vendedor no existe o esta inactivo", None)

            # 3) Punto de emision
            pe_row = (await self.db.execute(
                text(pe_st.SELECT_PUNTO_EMISION_BY_ID), {"punto_id": data.punto_emision_id}
            )).mappings().first()
            if not pe_row or not pe_row["activo"]:
                return standard_response(404, "PUNTO_EMISION_NO_ENCONTRADO: punto no existe o esta inactivo", None)

            # 4) Moneda
            mon_row = (await self.db.execute(
                text(mon_st.SELECT_MONEDA_BY_ID), {"moneda_id": data.moneda_id}
            )).mappings().first()
            if not mon_row or not mon_row["activo"]:
                return standard_response(404, "MONEDA_NO_ENCONTRADA: moneda no existe o esta inactiva", None)

            # 5) Detalles: validar cada producto y stock
            detalles_resueltos = []
            for i, det in enumerate(data.detalles, start=1):
                # Si el renglon no tiene producto (ej: NC con "ajuste"), skip validacion de producto
                if det.producto_id is None:
                    detalles_resueltos.append({
                        "producto_id": None,
                        "descripcion": det.descripcion or "Ajuste",
                        "cantidad": det.cantidad,
                        "precio_unitario": det.precio_unitario,
                        "descuento_pct": det.descuento_pct,
                        "impuesto_pct": det.impuesto_pct,
                        "es_servicio": True,  # trata como servicio para que no afecte stock
                    })
                    continue
                prod_row = (await self.db.execute(
                    text(prod_st.SELECT_PRODUCTO_BY_ID), {"producto_id": det.producto_id}
                )).mappings().first()
                if not prod_row or not prod_row["activo"]:
                    return standard_response(
                        404,
                        f"PRODUCTO_NO_ENCONTRADO: producto id={det.producto_id} no existe o esta inactivo",
                        None,
                    )
                if not prod_row["es_servicio"] and float(prod_row["existencia"]) < det.cantidad:
                    return standard_response(
                        409,
                        "STOCK_INSUFICIENTE: stock insuficiente para el producto",
                        {
                            "producto_id": det.producto_id,
                            "codigo": prod_row["codigo"],
                            "existencia_disponible": float(prod_row["existencia"]),
                            "cantidad_solicitada": det.cantidad,
                        },
                    )
                detalles_resueltos.append({
                    "producto_id": det.producto_id,
                    "descripcion": det.descripcion or prod_row["descripcion"],
                    "cantidad": det.cantidad,
                    "precio_unitario": det.precio_unitario,
                    "descuento_pct": det.descuento_pct,
                    "impuesto_pct": det.impuesto_pct,
                    "es_servicio": prod_row["es_servicio"],
                })

            # 6) Tasa de cambio del dia
            tasa_row = (await self.db.execute(
                text(tc_st.SELECT_TASA_BY_MONEDA_FECHA),
                {"moneda_id": data.moneda_id, "fecha": fecha_emision},
            )).mappings().first()
            if not tasa_row:
                return standard_response(
                    400,
                    f"DEBE_CARGAR_TASA_DEL_DIA: no hay tasa registrada para la moneda {data.moneda_id} en la fecha {fecha_emision}",
                    None,
                )
            tasa = float(tasa_row["tasa"])

            # 7) Limite de credito (solo FACTURA + cliente CREDITO)
            debe_crear_cxc = (
                data.tipo == "FACTURA" and cli_row["condicion_pago"] == "CREDITO"
            )
            necesita_override = False
            excedente = 0.0
            suma_pendiente = 0.0

            if debe_crear_cxc:
                # Calcular suma pendiente del cliente
                saldo_row = (await self.db.execute(
                    text(cli_st.SELECT_SUM_SALDO_PENDIENTE_CLIENTE),
                    {"cliente_id": data.cliente_id},
                )).mappings().first()
                suma_pendiente = float(saldo_row["total_pendiente"] or 0)

                # Leer parametro de bloqueo
                param_row = (await self.db.execute(
                    text(st.SELECT_PARAMETRO_BLOQUEO_CREDITO)
                )).mappings().first()
                param_valor = param_row["valor"] if param_row else True
                # jsonb 'true' / 'false' llega como string 'true'/'false' o bool
                if isinstance(param_valor, str):
                    param_valor = param_valor.lower() == "true"

                # Calcular total provisional (necesario para comparar con limite)
                total_neto_provisional = 0.0
                for d in detalles_resueltos:
                    sub = round(d["cantidad"] * d["precio_unitario"], 2)
                    desc = round(sub * (d["descuento_pct"] / 100), 2)
                    base = round(sub - desc, 2)
                    imp = round(base * (d["impuesto_pct"] / 100), 2)
                    total_neto_provisional = round(total_neto_provisional + base + imp, 2)

                limite = float(cli_row["limite_credito"] or 0)
                if (suma_pendiente + total_neto_provisional) > limite:
                    if param_valor:
                        # Bloqueado: solo procede con forzar_credito+motivo_override
                        if not (data.forzar_credito and data.motivo_override):
                            return standard_response(
                                409,
                                "LIMITE_CREDITO_EXCEDIDO: el cliente supera su limite de credito",
                                {
                                    "suma_pendiente_actual": suma_pendiente,
                                    "monto_nueva_factura": total_neto_provisional,
                                    "limite_credito": limite,
                                    "excedente": round((suma_pendiente + total_neto_provisional) - limite, 2),
                                    "mensaje_para_override": "Envie forzar_credito=true y motivo_override (min 5 chars) para forzar la operacion",
                                },
                            )
                        necesita_override = True
                        excedente = round((suma_pendiente + total_neto_provisional) - limite, 2)
                    # else: param_valor = false, continuar sin override (warning, no bloquea)

            # ---- FASE 2: Calculo de totales definitivo ----
            subtotal = 0.0
            total_descuentos = 0.0
            total_impuestos = 0.0
            total_neto = 0.0
            renglones = []
            for idx, d in enumerate(detalles_resueltos, start=1):
                sub_r = round(d["cantidad"] * d["precio_unitario"], 2)
                desc_m = round(sub_r * (d["descuento_pct"] / 100), 2)
                base = round(sub_r - desc_m, 2)
                imp_m = round(base * (d["impuesto_pct"] / 100), 2)
                tot_r = round(base + imp_m, 2)
                subtotal = round(subtotal + sub_r, 2)
                total_descuentos = round(total_descuentos + desc_m, 2)
                total_impuestos = round(total_impuestos + imp_m, 2)
                total_neto = round(total_neto + tot_r, 2)
                renglones.append({
                    "producto_id": d["producto_id"],
                    "nro_renglon": idx,
                    "descripcion": d["descripcion"],
                    "cantidad": d["cantidad"],
                    "precio_unitario": d["precio_unitario"],
                    "descuento_pct": d["descuento_pct"],
                    "impuesto_pct": d["impuesto_pct"],
                    "total_renglon": tot_r,
                })
            total_neto_local = round(total_neto * tasa, 2)

            # ---- FASE 2.5: Validaciones NC/ND ----
            ref_doc = None  # datos del documento referenciado (NC/ND)
            mov_factura_ref = None  # movimiento_cxc de la factura referenciada (NC/ND)
            if data.tipo in ("NOTA_CREDITO", "NOTA_DEBITO"):
                ref_doc = (await self.db.execute(
                    text(st.SELECT_DOCUMENTO_REFERENCIA_VALIDO),
                    {"documento_referencia_id": data.documento_referencia_id}
                )).mappings().first()
                if not ref_doc:
                    await self.db.rollback()
                    return standard_response(
                        404,
                        "DOCUMENTO_REFERENCIA_NO_ENCONTRADO: el documento referenciado no existe",
                        {"documento_referencia_id": data.documento_referencia_id},
                    )
                if ref_doc["tipo"] != "FACTURA":
                    await self.db.rollback()
                    return standard_response(
                        400,
                        "DOCUMENTO_REFERENCIA_NO_ES_FACTURA: NC/ND solo referencian FACTURAS",
                        {"documento_referencia_id": data.documento_referencia_id, "tipo_referenciado": ref_doc["tipo"]},
                    )
                if ref_doc["estado"] == "ANULADO":
                    await self.db.rollback()
                    return standard_response(
                        400,
                        "DOCUMENTO_REFERENCIA_ANULADO: la factura referenciada esta anulada",
                        {"documento_referencia_id": data.documento_referencia_id},
                    )
                if int(ref_doc["cliente_id"]) != int(data.cliente_id):
                    await self.db.rollback()
                    return standard_response(
                        400,
                        "DOCUMENTO_REFERENCIA_OTRO_CLIENTE: la factura referenciada es de otro cliente",
                        {"documento_referencia_id": data.documento_referencia_id, "cliente_factura": int(ref_doc["cliente_id"]), "cliente_nc": data.cliente_id},
                    )

                # Buscar el movimiento_cxc espejo de la factura referenciada
                mov_factura_ref = (await self.db.execute(
                    text(st.SELECT_MOVIMIENTO_CXC_BY_DOCUMENTO),
                    {"documento_venta_id": data.documento_referencia_id}
                )).mappings().first()
                if not mov_factura_ref:
                    await self.db.rollback()
                    return standard_response(
                        400,
                        "FACTURA_SIN_MOVIMIENTO_CXC: la factura referenciada no tiene movimiento CxC (¿es CONTADO o no fue creada via este sistema?)",
                        {"documento_referencia_id": data.documento_referencia_id},
                    )

            # ---- FASE 3: Transaccion atomica ----
            try:
                # 8) Lockear secuencia con FOR UPDATE
                seq_row = (await self.db.execute(
                    text(seq_st.INCREMENTAR_SECUENCIA),
                    {"punto_emision_id": data.punto_emision_id, "tipo_documento": data.tipo},
                )).mappings().first()
                if not seq_row:
                    await self.db.rollback()
                    return standard_response(
                        400,
                        f"SECUENCIA_NO_CONFIGURADA: no existe secuencia para (punto={data.punto_emision_id}, tipo={data.tipo})",
                        None,
                    )

                # 9) Incrementar correlativo
                await self.db.execute(
                    text(seq_st.UPDATE_INCREMENTAR_SECUENCIA),
                    {"secuencia_id": seq_row["id"]},
                )
                nuevo_numero = int(seq_row["numero_actual"]) + 1
                codigo = f"{seq_row['prefijo']}-{nuevo_numero:06d}"

                # 10) INSERT encabezado
                doc_row = (await self.db.execute(
                    text(st.INSERT_DOCUMENTO_VENTA),
                    {
                        "codigo": codigo,
                        "numero_control": data.numero_control,
                        "tipo": data.tipo,
                        "cliente_id": data.cliente_id,
                        "vendedor_id": data.vendedor_id,
                        "punto_emision_id": data.punto_emision_id,
                        "documento_referencia_id": data.documento_referencia_id,
                        "motivo": data.motivo,
                        "fecha_emision": fecha_emision,
                        "fecha_vencimiento": data.fecha_vencimiento,
                        "moneda_id": data.moneda_id,
                        "tasa_cambio": _d(tasa),
                        "subtotal": _d(subtotal),
                        "total_impuestos": _d(total_impuestos),
                        "total_descuentos": _d(total_descuentos),
                        "total_neto": _d(total_neto),
                        "total_neto_local": _d(total_neto_local),
                        "estado": "EMITIDO",
                        "observaciones": data.observaciones,
                        "creado_por": current_user.id,
                    },
                )).mappings().first()
                documento_id = doc_row["id"]

                # 11) INSERT detalles
                for r in renglones:
                    r["documento_id"] = documento_id
                    # Asegurar tipos Decimal en params monetarios
                    r["precio_unitario"] = _d(r["precio_unitario"])
                    r["total_renglon"] = _d(r["total_renglon"])
                    await self.db.execute(text(st.INSERT_DOCUMENTO_DETALLE), r)

                # 12) Si FACTURA + CREDITO: INSERT movimiento CxC espejo
                if debe_crear_cxc:
                    await self.db.execute(
                        text(st.INSERT_MOVIMIENTO_CXC_FACTURA),
                        {
                            "cliente_id": data.cliente_id,
                            "tipo_movimiento": "FACTURA",
                            "documento_venta_id": documento_id,
                            "numero_documento": codigo,
                            "fecha_movimiento": fecha_emision,
                            "fecha_vencimiento": data.fecha_vencimiento,
                            "moneda_id": data.moneda_id,
                            "tasa_cambio": _d(tasa),
                            "monto_original": _d(total_neto),
                            "saldo_original": _d(total_neto),
                            "monto_local": _d(total_neto_local),
                            "saldo_local": _d(total_neto_local),
                            "estado": "EMITIDO",
                            "registrado_por": current_user.id,
                        },
                    )

                # 12.5) Si NC: INSERT movimiento NOTA_CREDITO y aplicar contra la factura
                if data.tipo == "NOTA_CREDITO":
                    # Crear el movimiento de la NC con saldo_original = total_neto (inicia con todo a favor)
                    mov_nc = (await self.db.execute(
                        text(st.INSERT_MOVIMIENTO_CXC_FACTURA),
                        {
                            "cliente_id": data.cliente_id,
                            "tipo_movimiento": "NOTA_CREDITO",
                            "documento_venta_id": documento_id,
                            "numero_documento": codigo,
                            "fecha_movimiento": fecha_emision,
                            "fecha_vencimiento": None,
                            "moneda_id": data.moneda_id,
                            "tasa_cambio": _d(tasa),
                            "monto_original": _d(total_neto),
                            "saldo_original": _d(total_neto),
                            "monto_local": _d(total_neto_local),
                            "saldo_local": _d(total_neto_local),
                            "estado": "EMITIDO",
                            "registrado_por": current_user.id,
                        },
                    )).mappings().first()
                    mov_nc_id = mov_nc["id"]

                    # Aplicar contra la factura si tiene saldo pendiente
                    saldo_factura = float(mov_factura_ref["saldo_original"])
                    monto_a_aplicar = 0.0
                    if saldo_factura > 0.005:
                        monto_a_aplicar = min(total_neto, round(saldo_factura, 2))
                        # Conversion a local: ambos movimientos estan en su propia moneda
                        # y guardan el equivalente en local (monto_local = monto_original * tasa).
                        # El monto_a_aplicar_local = monto_a_aplicar * tasa_factura.
                        tasa_factura = float(mov_factura_ref["tasa_cambio"])
                        monto_a_aplicar_local = round(monto_a_aplicar * tasa_factura, 2)

                        # INSERT aplicacion (NC -> factura)
                        await self.db.execute(
                            text(st.INSERT_APLICACION_CXC),
                            {
                                "movimiento_pago_id": mov_nc_id,
                                "movimiento_deuda_id": int(mov_factura_ref["id"]),
                                "monto_aplicado_original": _d(monto_a_aplicar),
                                "monto_aplicado_local": _d(monto_a_aplicar_local),
                                "aplicado_por": current_user.id,
                            },
                        )

                        # UPDATE saldo de la factura (restar)
                        result_fac = await self.db.execute(
                            text(st.UPDATE_MOVIMIENTO_SALDO_RESTAR),
                            {
                                "movimiento_id": int(mov_factura_ref["id"]),
                                "monto": _d(monto_a_aplicar),
                                "monto_local": _d(monto_a_aplicar_local),
                            },
                        )
                        if result_fac.rowcount == 0:
                            await self.db.rollback()
                            return standard_response(
                                409,
                                "SALDO_INSUFICIENTE_EN_TRANSACCION_FACTURA: el saldo de la factura referenciada cambio entre validacion y aplicacion",
                                {"factura_movimiento_id": int(mov_factura_ref["id"])},
                            )

                        # Si la NC cubre exactamente la factura, saldo NC = 0.
                        # Si cubre mas, rebajar el saldo NC por lo aplicado (queda el excedente a favor).
                        if monto_a_aplicar < total_neto - 0.005:
                            await self.db.execute(
                                text(st.UPDATE_MOVIMIENTO_SALDO_RESTAR),
                                {
                                    "movimiento_id": mov_nc_id,
                                    "monto": _d(monto_a_aplicar),
                                    "monto_local": _d(monto_a_aplicar_local),
                                },
                            )

                    # Devolver stock proporcional a la factura original (solo no-servicios)
                    # Solo aplica si la NC efectivamente cubre algo de la factura
                    if monto_a_aplicar > 0.005:
                        det_factura = (await self.db.execute(
                            text(st.SELECT_DETALLES_BY_DOCUMENTO),
                            {"documento_id": data.documento_referencia_id},
                        )).mappings().all()
                        # Factor de devolucion: cuanto de la factura estamos devolviendo
                        total_factura = float(ref_doc["total_neto"])
                        if total_factura > 0:
                            factor_devolucion = monto_a_aplicar / total_factura
                        else:
                            factor_devolucion = 1.0
                        for d in det_factura:
                            if d["producto_id"] is None:
                                continue
                            prod_row = (await self.db.execute(
                                text(prod_st.SELECT_PRODUCTO_BY_ID),
                                {"producto_id": d["producto_id"]},
                            )).mappings().first()
                            if prod_row and not prod_row["es_servicio"]:
                                cant_devolver = round(float(d["cantidad"]) * factor_devolucion, 4)
                                if cant_devolver > 0:
                                    await self.db.execute(
                                        text(prod_st.UPDATE_DEVOLVER_EXISTENCIA),
                                        {"producto_id": d["producto_id"], "cantidad": cant_devolver},
                                    )

                # 12.6) Si ND: INSERT movimiento NOTA_DEBITO (deuda nueva, no aplica contra la factura)
                elif data.tipo == "NOTA_DEBITO":
                    # La ND es una deuda nueva: saldo_original = total_neto.
                    # La ND NO se aplica contra la factura referenciada (queda como cuenta aparte).
                    # documento_venta_id apunta a la ND misma.
                    await self.db.execute(
                        text(st.INSERT_MOVIMIENTO_CXC_FACTURA),
                        {
                            "cliente_id": data.cliente_id,
                            "tipo_movimiento": "NOTA_DEBITO",
                            "documento_venta_id": documento_id,
                            "numero_documento": codigo,
                            "fecha_movimiento": fecha_emision,
                            "fecha_vencimiento": data.fecha_vencimiento or fecha_emision,
                            "moneda_id": data.moneda_id,
                            "tasa_cambio": _d(tasa),
                            "monto_original": _d(total_neto),
                            "saldo_original": _d(total_neto),
                            "monto_local": _d(total_neto_local),
                            "saldo_local": _d(total_neto_local),
                            "estado": "EMITIDO",
                            "registrado_por": current_user.id,
                        },
                    )
                    # ND NO descuenta stock (decision de diseno: es recargo financiero, no fisico)

                # 13) Descontar stock (solo FACTURA y NOTA_ENTREGA; solo no-servicios)
                if data.tipo in ("FACTURA", "NOTA_ENTREGA"):
                    for d in detalles_resueltos:
                        if d["es_servicio"]:
                            continue
                        result = await self.db.execute(
                            text(prod_st.UPDATE_DESCONTAR_EXISTENCIA),
                            {"producto_id": d["producto_id"], "cantidad": _d(d["cantidad"])},
                        )
                        if result.rowcount == 0:
                            await self.db.rollback()
                            return standard_response(
                                409,
                                f"STOCK_INSUFICIENTE_EN_TRANSACCION: stock del producto {d['producto_id']} cambio entre la validacion y el descuento",
                                None,
                            )

                # 14) Si override de credito: INSERT log
                if necesita_override:
                    await self.db.execute(
                        text(st.INSERT_OVERRIDE_CREDITO_LOG),
                        {
                            "cliente_id": data.cliente_id,
                            "documento_venta_id": documento_id,
                            "usuario_id": current_user.id,
                            "limite_vigente": _d(float(cli_row["limite_credito"] or 0)),
                            "saldo_antes_emision": _d(suma_pendiente),
                            "monto_nueva_factura": _d(total_neto),
                            "monto_excedente": _d(excedente),
                            "motivo": data.motivo_override,
                        },
                    )

                # 15) COMMIT
                await self.db.commit()

                # 16) Devolver documento completo
                return await self.get_documento_by_id(documento_id)

            except IntegrityError as e:
                await self.db.rollback()
                return standard_response(
                    409,
                    f"REGISTRO_DUPLICADO: {str(e.orig)}",
                    None,
                )

        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)

    # =========================================================
    # LIST
    # =========================================================
    async def get_documentos(
        self,
        cliente_id=None,
        tipo=None,
        estado=None,
        fecha_desde=None,
        fecha_hasta=None,
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
                "limit": limit,
                "offset": offset,
            }
            result = await self.db.execute(text(st.SELECT_DOCUMENTOS_PAGINATED), params)
            rows = [dict(r) for r in result.mappings().all()]
            total = (await self.db.execute(text(st.SELECT_DOCUMENTOS_COUNT), params)).scalar() or 0
            return standard_response(
                200,
                f"Listado de documentos (total={total})",
                {"items": rows, "total": total, "limit": limit, "offset": offset},
            )
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    # =========================================================
    # GET BY ID (con detalle)
    # =========================================================
    async def get_documento_by_id(self, documento_id: int) -> dict:
        try:
            doc_row = (await self.db.execute(
                text(st.SELECT_DOCUMENTO_BY_ID), {"documento_id": documento_id}
            )).mappings().first()
            if not doc_row:
                return standard_response(404, "DOCUMENTO_NO_ENCONTRADO: documento no existe", None)

            det_rows = (await self.db.execute(
                text(st.SELECT_DETALLES_BY_DOCUMENTO), {"documento_id": documento_id}
            )).mappings().all()

            doc = dict(doc_row)
            doc["detalles"] = [dict(d) for d in det_rows]
            return standard_response(200, "Documento encontrado", doc)
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    # =========================================================
    # ANULAR (regla de anulacion segura)
    # =========================================================
    async def anular_documento(
        self, documento_id: int, data: DocumentoVentaAnularRequest, current_user: CurrentUser
    ) -> dict:
        try:
            # 1) Leer documento
            doc_row = (await self.db.execute(
                text(st.SELECT_DOCUMENTO_BY_ID), {"documento_id": documento_id}
            )).mappings().first()
            if not doc_row:
                return standard_response(404, "DOCUMENTO_NO_ENCONTRADO: documento no existe", None)

            estado = doc_row["estado"]
            if estado == "ANULADO":
                return standard_response(400, "DOCUMENTO_YA_ANULADO: el documento ya fue anulado", None)
            if estado == "PAGADO":
                return standard_response(400, "DOCUMENTO_YA_PAGADO: el documento esta marcado como PAGADO", None)

            # 2) Buscar movimiento CxC espejo (si existe)
            mov_cxc = (await self.db.execute(
                text(st.SELECT_MOVIMIENTO_CXC_BY_DOCUMENTO),
                {"documento_venta_id": documento_id},
            )).mappings().first()
            tiene_mov_cxc = mov_cxc is not None

            # 3) Si hay movimiento espejo, verificar si tiene aplicaciones
            if tiene_mov_cxc:
                count = (await self.db.execute(
                    text(st.SELECT_DOCUMENTO_TIENE_APLICACIONES),
                    {"documento_venta_id": documento_id},
                )).scalar() or 0
                if count > 0 and not data.forzar_anulacion:
                    return standard_response(
                        409,
                        "DOCUMENTO_CON_PAGOS_APLICADOS: el documento tiene pagos/retenciones aplicados. Use forzar_anulacion=true con motivo para anular de todos modos",
                        {
                            "aplicaciones_count": count,
                            "mensaje_para_override": "Envie forzar_anulacion=true con motivo (min 5 chars) para anular excepcionalmente",
                        },
                    )

            # 4) Transaccion de anulacion
            try:
                # Marcar documento como ANULADO
                await self.db.execute(
                    text(st.UPDATE_ANULAR_DOCUMENTO),
                    {
                        "documento_id": documento_id,
                        "anulado_por": current_user.id,
                        "motivo": data.motivo,
                    },
                )

                # Si hay mov_cxc espejo, marcarlo ANULADO
                if tiene_mov_cxc:
                    await self.db.execute(
                        text(st.UPDATE_MOVIMIENTO_CXC_ANULAR),
                        {"documento_venta_id": documento_id},
                    )

                # Devolver stock si el documento habia descontado (solo FACTURA y NOTA_ENTREGA)
                if doc_row["tipo"] in ("FACTURA", "NOTA_ENTREGA"):
                    det_rows = (await self.db.execute(
                        text(st.SELECT_DETALLES_BY_DOCUMENTO), {"documento_id": documento_id}
                    )).mappings().all()
                    for d in det_rows:
                        if d["producto_id"] is None:
                            continue
                        # Si es servicio, no aplica; si no, devolver
                        prod_row = (await self.db.execute(
                            text(prod_st.SELECT_PRODUCTO_BY_ID),
                            {"producto_id": d["producto_id"]},
                        )).mappings().first()
                        if prod_row and not prod_row["es_servicio"]:
                            await self.db.execute(
                                text(prod_st.UPDATE_DEVOLVER_EXISTENCIA),
                                {"producto_id": d["producto_id"], "cantidad": d["cantidad"]},
                            )

                await self.db.commit()
                return await self.get_documento_by_id(documento_id)

            except IntegrityError as e:
                await self.db.rollback()
                return standard_response(409, f"REGISTRO_DUPLICADO: {str(e.orig)}", None)

        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error: {str(e)}", None)
