import asyncio, asyncpg, sys
from pathlib import Path

async def main():
    if len(sys.argv) < 2:
        print('Uso: python ejecutar_sql.py <archivo_sql>')
        return

    sql_file = sys.argv[1]
    try:
        sql = Path(sql_file).read_text(encoding='utf-8')
        conn = await asyncpg.connect('postgresql://postgres:1234@localhost:5432/Vortex')
        try:
            await conn.execute(sql)
            print(f'OK - {sql_file} ejecutado sin errores')
        except Exception as e:
            print(f'ERROR: {e}')
        finally:
            await conn.close()
    except Exception as e:
        print(f'ERROR al leer archivo: {e}')

asyncio.run(main())
