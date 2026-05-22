
import asyncio
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import create_async_engine

async def list_pg_tables():
    db_url = "postgresql+asyncpg://postgres:JSLsEfBVPywKuYJSAypuNPVvIgYwGXzz@centerbeam.proxy.rlwy.net:54059/railway"
    engine = create_async_engine(db_url)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = result.fetchall()
            print("Postgres Tables:")
            for table in tables:
                print(f" - {table[0]}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(list_pg_tables())
