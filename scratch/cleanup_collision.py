import asyncio
import logging
import sys
import os

# Ajusta o path para importar os serviços do backend
sys.path.append(os.path.join(os.getcwd(), "1CRYPTEN_SPACE_V4.0", "backend"))

from services.sovereign_service import sovereign_service
from services.database_service import database_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CleanupSlot3")

async def cleanup_slot_3():
    logger.info("🧹 Iniciando limpeza manual do Slot 3 (Colisão IMXUSDT)...")
    
    # 1. Busca o estado atual do Slot 3
    slots = await database_service.get_active_slots()
    slot3 = next((s for s in slots if s.get("id") == 3), None)
    
    if slot3 and slot3.get("symbol") == "IMXUSDT":
        logger.info(f"🚨 Slot 3 detectado com {slot3.get('symbol')}. Realizando Hard Reset...")
        
        # Faz o reset atômico sem registrar no histórico (para não duplicar PnL, já que Slot 1 é o mestre)
        # Se for Paper Mode, o SlotOperator de 1 vai cuidar do fechamento real na Bybit se necessário.
        # Aqui apenas limpamos o registro do slot.
        
        await sovereign_service.hard_reset_slot(3, reason="COLLISION_CLEANUP_IMXUSDT")
        logger.info("✅ Slot 3 limpo com sucesso.")
    else:
        logger.warning("⚠️ Slot 3 não contém IMXUSDT ou já está livre.")
        if slot3:
            logger.info(f"Conteúdo atual do Slot 3: {slot3.get('symbol') or 'LIVRE'}")

if __name__ == "__main__":
    asyncio.run(cleanup_slot_3())
