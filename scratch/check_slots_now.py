import asyncio
import sys
import os

sys.path.append(os.path.join(os.getcwd(), "1CRYPTEN_SPACE_V4.0", "backend"))

from services.database_service import database_service

async def check():
    slots = await database_service.get_active_slots()
    for s in slots:
        print(f"Slot {s['id']}: {s.get('symbol') or 'LIVRE'} | Status: {s.get('status_risco') or s.get('status', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(check())
