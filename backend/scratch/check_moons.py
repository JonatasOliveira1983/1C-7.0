import asyncio
import json
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.getcwd())

# Load .env
load_dotenv('.env')

async def main():
    try:
        from services.database_service import database_service
        # Initialize database service if needed
        if not database_service.is_active:
            await database_service.initialize()
            
        moons = await database_service.get_moonbags()
        print(f"MOONBAGS_COUNT: {len(moons)}")
        print(f"MOONBAGS_LIST: {json.dumps(moons, indent=2)}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
