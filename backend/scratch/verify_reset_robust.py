import asyncio
import os
import sys
import json

# Add backend to path
backend_dir = r"c:\Users\spcom\Desktop\10D REAL 4.0\1CRYPTEN_SPACE_V4.0\backend"
sys.path.append(backend_dir)

from services.database_service import database_service

async def check_state():
    await database_service.initialize()
    
    banca = await database_service.get_banca_status()
    # Remove potentially problematic chars for Windows console
    print(f"BANCA_SALDO: {banca.get('saldo_total')}")
    print(f"BANCA_SLOTS_DISP: {banca.get('slots_disponiveis')}")
    print(f"BANCA_RISCO: {banca.get('risco_real_percent')}")
    
    slots = await database_service.get_active_slots()
    active_count = 0
    for s in slots:
        if s.get('symbol'):
            active_count += 1
            print(f"SLOT_{s['id']}_ACTIVE: {s['symbol']} {s['side']} QTY:{s['qty']}")
    print(f"TOTAL_ACTIVE_SLOTS: {active_count}")
    
    history = await database_service.get_trade_history(limit=10)
    print(f"TRADE_HISTORY_COUNT: {len(history)}")

if __name__ == "__main__":
    asyncio.run(check_state())
