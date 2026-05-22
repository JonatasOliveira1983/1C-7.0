import asyncio
import os
import sys
import json

# Add backend to path
sys.path.append(os.getcwd())

from services.database_service import database_service, OrderGenesis, Slot

async def diag():
    try:
        await database_service.initialize()
        async with database_service.AsyncSessionLocal() as session:
            from sqlalchemy import select
            
            # Check Slots
            res_slots = await session.execute(select(Slot))
            slots = res_slots.scalars().all()
            
            data = []
            for s in slots:
                data.append({
                    "id": s.id,
                    "symbol": s.symbol,
                    "status": s.status_risco,
                    "vision_url": s.vision_url,
                    "score": s.score,
                    "genesis_id": s.genesis_id,
                    "unified_confidence": s.unified_confidence
                })
            
            print("=== SLOTS DATA ===")
            print(json.dumps(data, indent=2))
            
            # Check OrderGenesis for SUI and AVAX
            for sym in ["SUIUSDT", "AVAXUSDT"]:
                res_gen = await session.execute(
                    select(OrderGenesis)
                    .where(OrderGenesis.symbol.like(f"%{sym}%"))
                    .order_by(OrderGenesis.timestamp.desc())
                    .limit(1)
                )
                gen = res_gen.scalars().first()
                if gen:
                    print(f"\n=== GENESIS {sym} ===")
                    print(f"ID: {gen.genesis_id}")
                    print(f"Data: {json.dumps(gen.data, indent=2)}")
                else:
                    print(f"\nNo Genesis found for {sym}")
                    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Prevent "Event loop is closed" error by not closing it manually if managed by run
        pass

if __name__ == "__main__":
    asyncio.run(diag())
