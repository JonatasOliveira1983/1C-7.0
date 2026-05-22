import asyncio
import os
import sys
from sqlalchemy import select

# Add backend to path
sys.path.append(os.getcwd())

from services.database_service import database_service, OrderGenesis, Slot, TradeHistory

async def diag():
    await database_service.initialize()
    async with database_service.AsyncSessionLocal() as session:
        print("--- DIAGNOSTIC FOR SUI & AVAX ---")
        
        for sym in ["SUIUSDT", "AVAXUSDT"]:
            print(f"\nChecking {sym}...")
            
            # Check Slots
            res_slots = await session.execute(select(Slot).where(Slot.symbol.like(f"%{sym}%")))
            slots = res_slots.scalars().all()
            for s in slots:
                print(f"Slot {s.id}: Status={s.status_risco}, VisionURL={s.vision_url}, Score={s.score}, Genesis={s.genesis_id}")
                if s.fleet_intel:
                    vision = s.fleet_intel.get("vision", {})
                    print(f"  Fleet Intel Vision: {vision}")
            
            # Check OrderGenesis
            res_gen = await session.execute(select(OrderGenesis).where(OrderGenesis.symbol.like(f"%{sym}%")).order_by(OrderGenesis.timestamp.desc()).limit(1))
            gen = res_gen.scalars().first()
            if gen:
                print(f"Genesis Found: {gen.genesis_id} at {gen.timestamp}")
                print(f"  Vision URL in Data: {gen.data.get('vision_url')}")
                print(f"  Vision Screenshot in Data: {gen.data.get('vision', {}).get('screenshot')}")
                print(f"  Unified Confidence: {gen.data.get('unified_confidence')}")
                if gen.data.get('fleet_intel'):
                    print(f"  Fleet Intel Vision: {gen.data.get('fleet_intel', {}).get('vision')}")
            else:
                print("No Genesis found in DB.")

        # Also check vision_history.json
        import json
        if os.path.exists("vision_history.json"):
            with open("vision_history.json", "r", encoding="utf-8") as f:
                history = json.load(f)
                print("\nRecent Vision History Entries:")
                for entry in history[:5]:
                    print(f"  {entry['timestamp']} - {entry['payload'].get('symbol')}: {entry['payload'].get('decision')} - {entry['payload'].get('screenshot_url')}")

if __name__ == "__main__":
    asyncio.run(diag())
