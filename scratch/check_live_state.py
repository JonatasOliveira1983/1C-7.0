import asyncio
import os
import sys
import json

# Add backend to path
sys.path.append(os.getcwd())

from services.redis_service import redis_service

async def check_state():
    await redis_service.connect()
    
    # Check Radar signals
    signals_raw = await redis_service.client.get("radar_signals")
    signals = json.loads(signals_raw) if signals_raw else []
    print(f"RADAR SIGNALS COUNT: {len(signals)}")
    for s in signals[:5]:
        print(f" - {s.get('symbol')} | Score: {s.get('score')} | Side: {s.get('side')}")
        
    # Check Slots
    slots_raw = await redis_service.client.get("active_slots")
    slots = json.loads(slots_raw) if slots_raw else []
    print(f"ACTIVE SLOTS COUNT: {len(slots)}")
    for i, s in enumerate(slots):
        if s.get('symbol'):
            print(f" Slot {i+1}: {s.get('symbol')} | ROI: {s.get('pnl_percent')}%")
        else:
            print(f" Slot {i+1}: EMPTY")
            
    await redis_service.client.aclose()

if __name__ == "__main__":
    asyncio.run(check_state())
