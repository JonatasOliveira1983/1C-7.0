
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

async def session_balance_reset():
    db_url = "postgresql+asyncpg://postgres:JSLsEfBVPywKuYJSAypuNPVvIgYwGXzz@centerbeam.proxy.rlwy.net:54059/railway"
    engine = create_async_engine(db_url)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("UPDATE banca_status SET saldo_total = 100.0 WHERE id = 1"))
            await session.commit()
            print("SESSION_COMMIT_SUCCESS")
            
            result = await session.execute(text("SELECT saldo_total FROM banca_status WHERE id = 1"))
            row = result.fetchone()
            print(f"VERIFIED_BALANCE: {row[0]}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(session_balance_reset())
