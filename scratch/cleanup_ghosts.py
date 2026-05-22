import sys
import os
import asyncio
import logging

# Adiciona o caminho do backend para importar os serviços
sys.path.append(os.path.join(os.getcwd(), "1CRYPTEN_SPACE_V4.0", "backend"))

from services.database_service import database_service
from services.sovereign_service import sovereign_service
from models.database import Slot, Moonbag
from sqlalchemy import select, delete

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CLEANUP")

async def run_cleanup():
    logger.info("🧹 Iniciando Faxina de Dados (Slots e Moonbags)...")
    
    async with database_service.AsyncSessionLocal() as session:
        # 1. Identificar Moonbags Duplicadas (mesmo order_id)
        query = select(Moonbag)
        result = await session.execute(query)
        moons = result.scalars().all()
        
        seen_orders = {}
        duplicates_removed = 0
        
        for m in moons:
            if not m.order_id: continue
            
            if m.order_id in seen_orders:
                logger.warning(f"🗑️ Removendo duplicata de Moonbag: {m.symbol} ({m.order_id})")
                await session.delete(m)
                duplicates_removed += 1
            else:
                seen_orders[m.order_id] = m.uuid
        
        # 2. Identificar Slots que já foram emancipados
        query_slots = select(Slot).where(Slot.symbol != None)
        result_slots = await session.execute(query_slots)
        slots = result_slots.scalars().all()
        
        slots_cleared = 0
        for s in slots:
            if s.order_id and s.order_id in seen_orders:
                logger.warning(f"🧹 Limpando Slot {s.id} que já está no Vault: {s.symbol}")
                await database_service._reset_slot_in_session(s)
                slots_cleared += 1
            elif s.symbol and not s.order_id:
                # Slot fantasma sem ID de ordem (provavelmente crash na abertura)
                logger.warning(f"🧹 Limpando Slot {s.id} Fantasma (sem order_id): {s.symbol}")
                await database_service._reset_slot_in_session(s)
                slots_cleared += 1

        await session.commit()
        logger.info(f"✅ Faxina Completa: {duplicates_removed} duplicatas removidas, {slots_cleared} slots limpos.")
        
        # 3. Forçar atualização do cache do SovereignService
        await sovereign_service.get_active_slots(force_refresh=True)

if __name__ == "__main__":
    asyncio.run(run_cleanup())
