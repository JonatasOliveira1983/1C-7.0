import asyncio
import os
import sys

sys.path.append(os.path.join(os.getcwd(), "1CRYPTEN_SPACE_V4.0", "backend"))

async def check():
    try:
        from services.database_service import database_service
        await database_service.initialize()
        slots = await database_service.get_active_slots()
        active = [s for s in slots if s.get('symbol')]
        print(f"ACTIVE_SLOTS_COUNT: {len(active)}")
        for s in active:
            print(f"SLOT {s.get('id')}: {s.get('symbol')}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(check())
