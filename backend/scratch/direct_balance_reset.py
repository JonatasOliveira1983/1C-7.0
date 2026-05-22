
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def direct_balance_reset():
    db_url = "postgresql+asyncpg://postgres:JSLsEfBVPywKuYJSAypuNPVvIgYwGXzz@centerbeam.proxy.rlwy.net:54059/railway"
    engine = create_async_engine(db_url)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("UPDATE banca_status SET saldo_total = 100.0 WHERE id = 1"))
            await conn.commit()
            print("SQL_UPDATE_SUCCESS")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(direct_balance_reset())
