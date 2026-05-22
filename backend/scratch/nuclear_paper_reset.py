
import asyncio
import json
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from services.sovereign_service import sovereign_service

async def nuclear_reset():
    print("--- INICIANDO RESET NUCLEAR (V110.506) ---")
    
    # 1. Limpar Postgres (Paper Engine State)
    db_url = "postgresql+asyncpg://postgres:JSLsEfBVPywKuYJSAypuNPVvIgYwGXzz@centerbeam.proxy.rlwy.net:54059/railway"
    engine = create_async_engine(db_url)
    try:
        async with engine.connect() as conn:
            # Deleta o estado do motor paper
            await conn.execute(text("DELETE FROM system_state WHERE key = 'paper_engine_state'"))
            await conn.commit()
            print("[DB] Estado do motor Paper deletado no Postgres.")
    except Exception as e:
        print(f"[ERROR] Erro ao limpar Postgres: {e}")
    finally:
        await engine.dispose()

    # 2. Limpar Slots no Firestore e RTDB
    print("[CLEAN] Limpando slots no Firestore e RTDB...")
    for i in range(1, 5):
        empty_slot = {
            "id": i,
            "symbol": None,
            "side": None,
            "entry_price": 0,
            "current_price": 0,
            "leverage": 0,
            "pnl_percent": 0,
            "pnl_usd": 0,
            "status_risco": "LIVRE",
            "opened_at": 0,
            "genesis_id": None,
            "order_id": None,
            "qty": 0
        }
        try:
            await sovereign_service.update_slot(i, empty_slot)
            if sovereign_service.rtdb:
                sovereign_service.rtdb.child("live_slots").child(str(i)).set(empty_slot)
            print(f"Slot {i} resetado.")
        except Exception as e:
            print(f"[ERROR] Erro ao resetar Slot {i}: {e}")

    print("[DONE] RESET NUCLEAR CONCLUIDO. Aguarde o proximo deploy para purificacao total.")

if __name__ == "__main__":
    asyncio.run(nuclear_reset())
