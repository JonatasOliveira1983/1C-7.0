import asyncio
import os
import sys
import json

# Add backend to path
sys.path.append(os.getcwd())

from services.database_service import database_service

async def check():
    try:
        await database_service.initialize()
        from sqlalchemy import text
        async with database_service.AsyncSessionLocal() as session:
            res = await session.execute(text("SELECT id, symbol, vision_url FROM slots"))
            rows = res.fetchall()
            print("=== CURRENT SLOTS IN DB ===")
            for row in rows:
                print(f"Slot {row[0]}: {row[1]} -> {row[2]}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
