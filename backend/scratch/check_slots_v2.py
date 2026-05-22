import asyncio
import os
import sys

# Adiciona o diretório do backend ao sys.path
sys.path.append("c:\\Users\\spcom\\Desktop\\10D REAL 4.0\\1CRYPTEN_SPACE_V4.0\\backend")

from services.database_service import database_service

async def check_db():
    print("Initializing database...")
    await database_service.initialize()
    print("Fetching active slots...")
    slots = await database_service.get_active_slots()
    print("--- ACTIVE SLOTS ---")
    for s in slots:
        print(f"Slot {s['id']}: {s['symbol']} | {s['side']} | {s['slot_type']} | {s['status_risco']} | Order: {s['order_id']}")
    
    print("\n--- BANCA STATUS ---")
    banca = await database_service.get_banca_status()
    print(banca)

if __name__ == "__main__":
    asyncio.run(check_db())
