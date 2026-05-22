
import asyncio
import os
import sys

# Adiciona o diretório backend ao path
backend_dir = r"C:\Users\spcom\Desktop\10D REAL 5.0\1CRYPTEN_SPACE_V4.0\backend"
sys.path.append(backend_dir)

from services.database_service import database_service

async def check():
    await database_service.initialize()
    status = await database_service.get_banca_status()
    print(f"BANCA_STATUS: {status}")
    slots = await database_service.get_active_slots()
    print(f"SLOTS: {len(slots)} total slots fetched.")
    for s in slots:
        print(f"  Slot {s.get('id')}: {s.get('symbol')} | {s.get('status_risco')}")

if __name__ == "__main__":
    asyncio.run(check())
