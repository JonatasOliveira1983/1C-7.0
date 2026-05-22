
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def check_balance():
    db_url = "postgresql+asyncpg://postgres:JSLsEfBVPywKuYJSAypuNPVvIgYwGXzz@centerbeam.proxy.rlwy.net:54059/railway"
    engine = create_async_engine(db_url)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT saldo_total FROM banca_status WHERE id = 1"))
            row = result.fetchone()
            if row:
                print(f"FINAL_BALANCE: {row[0]}")
            else:
                print("BALANCE_NOT_FOUND")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_balance())
