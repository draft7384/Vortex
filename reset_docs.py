import asyncio, asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://postgres:1234@localhost:5432/Vortex')
    # Limpiar todo lo transaccional
    await conn.execute('''
        DELETE FROM aplicaciones_cxc;
        DELETE FROM override_credito_log;
        DELETE FROM movimientos_cxc;
        DELETE FROM documentos_ventas_detalle;
        DELETE FROM documentos_ventas;
        UPDATE secuencias_documentos SET numero_actual = 0, proximo_numero = 1;
    ''')
    print('Documentos limpios')
    # Confirmar estado
    for tab in ['documentos_ventas', 'movimientos_cxc', 'aplicaciones_cxc', 'override_credito_log']:
        n = await conn.fetchval(f'SELECT count(*) FROM {tab}')
        print(f'  {tab}: {n}')
    await conn.close()

asyncio.run(main())
