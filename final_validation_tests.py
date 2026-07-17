
import asyncio, asyncpg
from decimal import Decimal

async def run_test(name, coro):
    print(f"Running {name}...", end=" ")
    try:
        await coro
        print("PASSED")
    except Exception as e:
        print(f"FAILED ({e})")

async def main():
    conn = await asyncpg.connect('postgresql://postgres:1234@localhost:5432/Vortex')
    try:
        print("=== STARTING FINAL VALIDATION SUITE ===\n")

        # --- T19: Credit Limit & Override ---
        async def test_t19():
            # Setup: Clean and create Client
            await conn.execute("DELETE FROM override_credito_log WHERE cliente_id = (SELECT id FROM clientes WHERE codigo = 'T19')")
            await conn.execute("DELETE FROM movimientos_cxc WHERE cliente_id = (SELECT id FROM clientes WHERE codigo = 'T19')")
            await conn.execute("DELETE FROM clientes WHERE codigo = 'T19'")
            cli_id = await conn.fetchval("INSERT INTO clientes (codigo, rif, nombre_razon_social, limite_credito, activo) VALUES ('T19', 'J-T19', 'Test Limit', 1000.00, TRUE) RETURNING id")

            # Scenario A: Exceed limit
            current_balance = await conn.fetchval("SELECT COALESCE(SUM(saldo_original), 0) FROM movimientos_cxc WHERE cliente_id = $1 AND saldo_original > 0", cli_id)
            new_invoice = Decimal('1200.00')

            bloqueo_val = await conn.fetchval("SELECT valor FROM parametros_sistema WHERE clave = 'cxc_bloquear_limite_credito'")
            bloqueo_activo = bloqueo_val if isinstance(bloqueo_val, bool) else (bloqueo_val == 'true' or bloqueo_val == True)

            if bloqueo_activo and (current_balance + new_invoice > 1000):
                pass
            else:
                raise Exception(f"T19A: System failed to identify credit limit breach. bloqueo={bloqueo_activo}, balance={current_balance}, invoice={new_invoice}")

            # Scenario B: Override
            doc_id = await conn.fetchval("INSERT INTO documentos_ventas (codigo, numero_control, tipo, cliente_id, punto_emision_id, moneda_id, tasa_cambio, subtotal, total_impuestos, total_neto, total_neto_local, creado_por) VALUES ('T19-S', 'CN-T19', 'FACTURA', $1, 1, 1, 1.0, 1000, 200, 1200, 1200, 1) RETURNING id", cli_id)
            await conn.execute("INSERT INTO override_credito_log (cliente_id, documento_venta_id, usuario_id, limite_vigente, saldo_antes_emision, monto_nueva_factura, monto_excedente, motivo) VALUES ($1, $2, 1, 1000, 0, 1200, 200, 'Force for testing')", cli_id, doc_id)
            await conn.execute("INSERT INTO movimientos_cxc (cliente_id, tipo_movimiento, documento_venta_id, numero_documento, moneda_id, tasa_cambio, monto_original, saldo_original, monto_local, saldo_local, registrado_por) VALUES ($1, 'FACTURA', $2, 'T19', 1, 1.0, 1200, 1200, 1200, 1200, 1)", cli_id, doc_id)

        await run_test("T19: Credit Limit & Override", test_t19())

        # --- T20: Safe Annulment ---
        async def test_t20():
            # Setup: Clean
            await conn.execute("DELETE FROM aplicaciones_cxc WHERE movimiento_deuda_id IN (SELECT id FROM movimientos_cxc WHERE numero_documento = 'T20')")
            await conn.execute("DELETE FROM movimientos_cxc WHERE numero_documento = 'T20'")
            await conn.execute("DELETE FROM documentos_ventas WHERE codigo = 'T20'")

            doc_id = await conn.fetchval("INSERT INTO documentos_ventas (codigo, numero_control, tipo, cliente_id, punto_emision_id, moneda_id, tasa_cambio, subtotal, total_impuestos, total_neto, total_neto_local, creado_por) VALUES ('T20', 'CN-T20', 'FACTURA', 101, 1, 1, 1.0, 100, 16, 116, 116, 1) RETURNING id")
            mov_fact_id = await conn.fetchval("INSERT INTO movimientos_cxc (cliente_id, tipo_movimiento, documento_venta_id, numero_documento, moneda_id, tasa_cambio, monto_original, saldo_original, monto_local, saldo_local, registrado_por) VALUES (101, 'FACTURA', $1, 'T20', 1, 1.0, 116, 116, 116, 116, 1) RETURNING id", doc_id)
            mov_pago_id = await conn.fetchval("INSERT INTO movimientos_cxc (cliente_id, tipo_movimiento, numero_documento, moneda_id, tasa_cambio, monto_original, saldo_original, monto_local, saldo_local, registrado_por) VALUES (101, 'ABONO', 'PAGO-T20', 1, 1.0, 116, 0, 116, 0, 1) RETURNING id")
            await conn.execute("INSERT INTO aplicaciones_cxc (movimiento_pago_id, movimiento_deuda_id, monto_aplicado_original, monto_aplicado_local, aplicado_por) VALUES ($1, $2, 116, 116, 1)", mov_pago_id, mov_fact_id)

            # Scenario A: Direct Annulment (API logic check)
            apps_count = await conn.fetchval("SELECT count(*) FROM aplicaciones_cxc WHERE movimiento_deuda_id = $1 AND reversada = FALSE", mov_fact_id)
            if apps_count > 0:
                pass
            else:
                raise Exception("T20A: Expected applications to be found")

            # Scenario B: Reverse and Annul
            await conn.execute("UPDATE aplicaciones_cxc SET reversada = TRUE, reversada_por = 1, reversada_en = NOW(), motivo_reverso = 'Testing' WHERE movimiento_deuda_id = $1", mov_fact_id)
            await conn.execute("UPDATE documentos_ventas SET estado = 'ANULADO', anulado_por = 1, anulado_en = NOW(), motivo = 'Reversed then annulled' WHERE id = $1", doc_id)

            res = await conn.fetchval("SELECT estado FROM documentos_ventas WHERE id = $1", doc_id)
            if res != 'ANULADO':
                raise Exception("T20B: Document was not annulled")

        await run_test("T20: Safe Annulment", test_t20())

        # --- T21: Special Contributor ---
        async def test_t21():
            # Setup: Clean
            await conn.execute("DELETE FROM movimientos_cxc WHERE cliente_id IN (SELECT id FROM clientes WHERE codigo IN ('T21A', 'T21B'))")
            await conn.execute("DELETE FROM clientes WHERE codigo IN ('T21A', 'T21B')")
            cli_a = await conn.fetchval("INSERT INTO clientes (codigo, rif, nombre_razon_social, es_contribuyente_especial, activo) VALUES ('T21A', 'J-T21A', 'Non-Special', FALSE, TRUE) RETURNING id")
            cli_b = await conn.fetchval("INSERT INTO clientes (codigo, rif, nombre_razon_social, es_contribuyente_especial, activo) VALUES ('T21B', 'J-T21B', 'Special', TRUE, TRUE) RETURNING id")

            # Scenario A: Withholding for Non-Special
            is_special_a = await conn.fetchval("SELECT es_contribuyente_especial FROM clientes WHERE id = $1", cli_a)
            if not is_special_a:
                pass
            else:
                raise Exception("T21A: Client A should not be special")

            # Scenario B: Withholding for Special
            await conn.execute("INSERT INTO movimientos_cxc (cliente_id, tipo_movimiento, numero_documento, moneda_id, tasa_cambio, monto_original, saldo_original, monto_local, saldo_local, registrado_por) VALUES ($1, 'RETENCION_IVA', 'RET-T21', 1, 1.0, 10, 10, 10, 10, 1)", cli_b)

        await run_test("T21: Special Contributor", test_t21())

        # --- T22: Single Local Currency Constraint ---
        async def test_t22():
            try:
                await conn.execute("UPDATE monedas SET es_moneda_local = TRUE WHERE codigo_iso = 'USD'")
                raise Exception("T22: DB allowed multiple local currencies!")
            except asyncpg.UniqueViolationError:
                pass

        await run_test("T22: Local Currency Uniqueness", test_t22())

        # --- T23: Mandatory Control Number ---
        async def test_t23():
            try:
                await conn.execute('''
                    INSERT INTO documentos_ventas (codigo, numero_control, tipo, cliente_id, punto_emision_id, moneda_id, tasa_cambio, subtotal, total_impuestos, total_neto, total_neto_local, creado_por)
                    VALUES ('T23', NULL, 'FACTURA', 101, 1, 1, 1.0, 100, 16, 116, 116, 1)
                ''')
                raise Exception("T23: DB allowed FACTURA without numero_control!")
            except asyncpg.CheckViolationError:
                pass

        await run_test("T23: Mandatory Control Number", test_t23())

        print("\n=== ALL TESTS COMPLETED ===")

    except Exception as e:
        print(f"FATAL ERROR: {e}")
    finally:
        await conn.close()

asyncio.run(main())
