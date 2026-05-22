import asyncio
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import select

# Add backend to path
sys.path.append(os.getcwd())
load_dotenv('.env')

async def main():
    try:
        from services.database_service import database_service
        from services.database_service import Moonbag
        
        # Initialize
        await database_service.initialize()
        
        async with database_service.AsyncSessionLocal() as session:
            result = await session.execute(select(Moonbag))
            moons = result.scalars().all()
            print("---START_MOONS---")
            for m in moons:
                print(f"SYMBOL:{m.symbol} ROI:{m.pnl_percent}")
            print("---END_MOONS---")
    except Exception as e:
        print(f"ERROR:{e}")

if __name__ == "__main__":
    asyncio.run(main())
