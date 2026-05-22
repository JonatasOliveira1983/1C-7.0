# emergency_slot_cleanup.py
import asyncio
import os
import sys
import logging
from sqlalchemy import text

# Adicionar o diretório backend ao sys.path para poder importar database_service
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, "..", "1CRYPTEN_SPACE_V4.0", "backend")
services_dir = os.path.join(backend_dir, "services")
sys.path.append(backend_dir)
sys.path.append(services_dir)

from database_service import DatabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Cleanup")

async def cleanup():
    # Carregar DATABASE_URL do .env
    env_path = os.path.join(backend_dir, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("DATABASE_URL="):
                    db_url = line.split("=", 1)[1].strip()
                    os.environ["DATABASE_URL"] = db_url
                    break

    db = DatabaseService()
    async with db.engine.begin() as conn:
        logger.info("🧹 LIMPANDO SLOTS FANTASMAS NO POSTGRES (RAILWAY)...")
        await conn.execute(text("""
            UPDATE slots 
            SET symbol = NULL, 
                side = NULL, 
                qty = 0.0, 
                entry_price = 0.0, 
                entry_margin = 0.0, 
                current_stop = 0.0, 
                initial_stop = 0.0, 
                target_price = 0.0, 
                liq_price = 0.0, 
                pnl_percent = 0.0, 
                status_risco = 'LIVRE',
                order_id = NULL,
                genesis_id = NULL
        """))
        logger.info("✅ Todos os slots no Postgres foram resetados.")

    # 2. Limpar Estado Paper no Firestore/RTDB
    logger.info("🧹 LIMPANDO ESTADO PAPER NO FIRESTORE/RTDB...")
    try:
        from sovereign_service import sovereign_service
        # Reset total do estado paper
        empty_state = {
            "positions": [],
            "moonbags": [],
            "balance": 100.0,
            "history": []
        }
        await sovereign_service.update_paper_state(empty_state)
        # Limpar bankroll central
        await sovereign_service.update_bankroll(100.0)
        
        # Limpar slots no RTDB também
        if sovereign_service.rtdb:
            for i in range(1, 5):
                await asyncio.to_thread(sovereign_service.rtdb.child("active_slots").child(str(i)).remove)
        
        logger.info("✅ Estado Paper e RTDB purificados.")
    except Exception as e:
        logger.error(f"❌ Erro ao limpar estado cloud: {e}")

if __name__ == "__main__":
    asyncio.run(cleanup())
