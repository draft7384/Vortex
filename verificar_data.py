import asyncio, asyncpg
from pathlib import Path

async def main():
    sql = Path('data_prueba.sql').read_text(encoding='utf-8')
    conn = await asyncpg.connect('postgresql://postgres:1234@localhost:5432/Vortex')
    try:
        await conn.execute(sql)
    except Exception as e:
        print(f'ERROR: {e}')
        await conn.close()
        return

    print('=== Conteo de tablas ===')
    for tab in ['clientes', 'vendedores', 'productos', 'documentos_ventas',
                'documentos_ventas_detalle', 'movimientos_cxc',
                'aplicaciones_cxc', 'override_credito_log']:
        n = await conn.fetchval(f'SELECT count(*) FROM {tab}')
        print(f'  {tab:<30} {n}')

    print()
    print('=== Documentos generados ===')
    docs = await conn.fetch('SELECT codigo, tipo, estado, total_neto, moneda_id FROM documentos_ventas ORDER BY id')
    for d in docs:
        mn = float(d['total_neto'])
        print(f'  {d["codigo"]:<14} {d["tipo"]:<14} {d["estado"]:<10} ${mn:>10.2f}  (moneda_id={d["moneda_id"]})')

    print()
    print('=== Movimientos CxC ===')
    cxc = await conn.fetch('SELECT numero_documento, tipo_movimiento, monto_original, saldo_original, estado FROM movimientos_cxc ORDER BY id')
    for c in cxc:
        mo = float(c['monto_original'])
        so = float(c['saldo_original'])
        print(f'  {c["numero_documento"]:<22} {c["tipo_movimiento"]:<15} orig=${mo:>10.2f}  saldo=${so:>10.2f}  {c["estado"]}')

    print()
    print('=== Stock actual de productos (no servicios) ===')
    prods = await conn.fetch('SELECT codigo, descripcion, existencia FROM productos WHERE es_servicio = FALSE ORDER BY id')
    for p in prods:
        ex = float(p['existencia'])
        print(f'  {p["codigo"]:<6} {p["descripcion"]:<25} stock={ex:>6.1f}')

    print()
    print('=== Clientes activos ===')
    cli = await conn.fetch('SELECT codigo, nombre_razon_social, condicion_pago, limite_credito, es_contribuyente_especial FROM clientes WHERE activo ORDER BY id')
    for c in cli:
        lc = float(c['limite_credito'])
        ce = 'CE' if c['es_contribuyente_especial'] else '  '
        print(f'  {c["codigo"]:<5} {c["nombre_razon_social"]:<35} {c["condicion_pago"]:<10} limite=${lc:>10.2f} {ce}')

    await conn.close()

asyncio.run(main())
