
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def check_all_rows():
    db_url = "postgresql+asyncpg://postgres:JSLsEfBVPywKuYJSAypuNPVvIgYwGXzz@centerbeam.proxy.rlwy.net:54059/railway"
    engine = create_async_engine(db_url)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT id, saldo_total FROM banca_status"))
            rows = result.fetchall()
            print("Banca Status Rows:")
            for row in rows:
                print(f"ID: {row[0]}, Balance: {row[1]}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_all_rows())
