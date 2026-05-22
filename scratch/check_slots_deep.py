import asyncio
import asyncpg

async def check():
    conn = await asyncpg.connect('postgresql://postgres:JSLsEfBVPywKuYJSAypuNPVvIgYwGXzz@centerbeam.proxy.rlwy.net:54059/railway')
    rows = await conn.fetch('SELECT id, symbol, status_risco, status_operacional FROM slots ORDER BY id')
    for row in rows:
        print(row)
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check())
