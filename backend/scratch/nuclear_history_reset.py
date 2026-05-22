
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def clear_history_and_reset_fixed():
    db_url = "postgresql+asyncpg://postgres:JSLsEfBVPywKuYJSAypuNPVvIgYwGXzz@centerbeam.proxy.rlwy.net:54059/railway"
    engine = create_async_engine(db_url)
    try:
        async with engine.connect() as conn:
            print("--- LIMPANDO HISTORICO (FIXED) ---")
            
            # 1. Limpar histórico de trades
            await conn.execute(text("DELETE FROM trade_history"))
            print("DONE: trade_history deletado.")
            
            # 2. Limpar ciclos do vault
            await conn.execute(text("DELETE FROM vault_cycles"))
            print("DONE: vault_cycles deletado.")
            
            # 3. Resetar banca_status apenas campos validos
            await conn.execute(text("UPDATE banca_status SET saldo_total = 100.0 WHERE id = 1"))
            print("DONE: banca_status resetada para $100.")
            
            await conn.commit()
            print("FINISH: Database limpo.")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(clear_history_and_reset_fixed())
