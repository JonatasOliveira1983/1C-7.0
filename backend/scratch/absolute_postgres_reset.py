
import asyncio
import os
import sys
from datetime import datetime

# Garantir que o path inclua o backend
sys.path.append(os.getcwd())

from services.database_service import database_service
from services.sovereign_service import sovereign_service
from sqlalchemy import text

async def absolute_postgres_reset():
    print("--- INICIANDO RESET ABSOLUTO POSTGRES (V110.506) ---")
    
    # 1. Inicializa Database
    await database_service.initialize()
    
    # 2. Limpar Slots no Postgres
    print("🧹 Limpando slots no Postgres...")
    for i in range(1, 5):
        empty_slot = {
            "symbol": None,
            "side": None,
            "qty": 0,
            "entry_price": 0,
            "entry_margin": 0,
            "current_stop": 0,
            "initial_stop": 0,
            "target_price": 0,
            "liq_price": 0,
            "pnl_percent": 0,
            "status_risco": "LIVRE",
            "order_id": None,
            "genesis_id": None,
            "pensamento": "Resetado via Nuclear Exorcism"
        }
        await database_service.update_slot(i, empty_slot)
        print(f"Postgres Slot {i} resetado.")

    # 3. Limpar Slots no Firestore e RTDB (via Sovereign)
    print("🧹 Limpando slots no Firestore e RTDB...")
    for i in range(1, 5):
        try:
            await sovereign_service.update_slot(i, {"status_risco": "LIVRE", "symbol": None})
            print(f"Firestore/RTDB Slot {i} resetado.")
        except Exception as e:
            print(f"Erro no Sovereign Slot {i}: {e}")

    # 4. Limpar Estado do Motor Paper no Postgres
    async with database_service.AsyncSessionLocal() as session:
        try:
            await session.execute(text("DELETE FROM system_state WHERE key = 'paper_engine_state'"))
            await session.commit()
            print("✅ Estado do motor Paper deletado no Postgres.")
        except Exception as e:
            print(f"Erro ao limpar system_state: {e}")

    print("🏁 RESET ABSOLUTO CONCLUIDO.")

if __name__ == "__main__":
    asyncio.run(absolute_postgres_reset())
