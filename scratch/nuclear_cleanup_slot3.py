import asyncio
import sys
import os
from sqlalchemy import update

sys.path.append(os.path.join(os.getcwd(), "1CRYPTEN_SPACE_V4.0", "backend"))

from services.database_service import database_service, Slot

async def hard_cleanup_slot_3():
    print("[NUCLEAR-CLEANUP] Forcando limpeza atomica do Slot 3 no Postgres...")
    async with database_service.AsyncSessionLocal() as session:
        try:
            q = update(Slot).where(Slot.id == 3).values(
                symbol=None,
                side=None,
                qty=0.0,
                entry_price=0.0,
                current_stop=0.0,
                status_risco="LIVRE",
                pnl_percent=0.0,
                order_id=None,
                genesis_id=None,
                opened_at=0.0,
                vision_url=None,
                pensamento="Limpeza manual de colisao (V110.657)"
            )
            await session.execute(q)
            await session.commit()
            print("[NUCLEAR-CLEANUP] Slot 3 limpo diretamente no banco de dados.")
        except Exception as e:
            print(f"[NUCLEAR-CLEANUP] Erro ao limpar Slot 3: {e}")

if __name__ == "__main__":
    asyncio.run(hard_cleanup_slot_3())
