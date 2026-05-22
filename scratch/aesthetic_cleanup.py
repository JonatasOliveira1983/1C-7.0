import asyncio
import sys
import os
from sqlalchemy import select, update

sys.path.append(os.path.join(os.getcwd(), "1CRYPTEN_SPACE_V4.0", "backend"))

from services.database_service import database_service, Slot
from services.utils.symbol_utils import normalize_symbol

async def aesthetic_cleanup():
    print("[AESTHETIC-CLEANUP] Padronizando nomes dos pares nos slots ativos...")
    async with database_service.AsyncSessionLocal() as session:
        try:
            res = await session.execute(select(Slot))
            slots = res.scalars().all()
            for s in slots:
                if s.symbol:
                    old_name = s.symbol
                    new_name = normalize_symbol(old_name)
                    if old_name != new_name:
                        print(f"Slot {s.id}: {old_name} -> {new_name}")
                        s.symbol = new_name
            await session.commit()
            print("[AESTHETIC-CLEANUP] Concluido com sucesso.")
        except Exception as e:
            print(f"[AESTHETIC-CLEANUP] Erro: {e}")

if __name__ == "__main__":
    asyncio.run(aesthetic_cleanup())
