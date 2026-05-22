import asyncio
import json
import os
import sys

# Add backend to path
sys.path.append(os.getcwd())

async def main():
    try:
        from services.database_service import database_service
        slots = await database_service.get_active_slots()
        print(f"ALL SLOTS DB: {json.dumps(slots, indent=2)}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
