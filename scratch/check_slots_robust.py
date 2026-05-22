import asyncio
import sys
import os

sys.path.append(os.path.join(os.getcwd(), "1CRYPTEN_SPACE_V4.0", "backend"))

from services.database_service import database_service

async def check():
    try:
        slots = await database_service.get_active_slots()
        print("--- ESTADO DOS SLOTS ---")
        for s in slots:
            sym = s.get('symbol') or 'LIVRE'
            status = s.get('status_risco') or s.get('status', 'N/A')
            print(f"Slot {s['id']}: {sym} | Status: {status}")
        print("------------------------")
    finally:
        # Força o encerramento limpo se possível
        pass

if __name__ == "__main__":
    asyncio.run(check())
