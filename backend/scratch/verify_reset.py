import asyncio
import sys
import os

backend_dir = r"c:\Users\spcom\Desktop\10D REAL 5.0\1CRYPTEN_SPACE_V4.0\backend"
sys.path.append(backend_dir)

async def check():
    from services.database_service import database_service
    status = await database_service.get_banca_status()
    print(f"SALDO: {status.get('saldo_total')}")
    
    slots = await database_service.get_active_slots()
    print(f"SLOTS ATIVOS: {len([s for s in slots if s.get('symbol')])}")

if __name__ == "__main__":
    asyncio.run(check())
