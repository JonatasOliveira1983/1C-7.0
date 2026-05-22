import asyncio
import os
import sys

# Ajustar path para importar serviços
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import database_service
from services.sovereign_service import sovereign_service
from sqlalchemy import text

async def execute_reset():
    print("Iniciando RESET NUCLEAR via Postgres...")
    
    # Garantir init apenas do DB, sem Firebase listeners
    
    async with database_service.AsyncSessionLocal() as session:
        # Banca e Vault
        print("Resetando Banca...")
        await session.execute(text("UPDATE banca_status SET saldo_total = 100.0, risco_real_percent = 0.0, slots_disponiveis = 4, status = 'ONLINE' WHERE id = 1"))
        
        print("Resetando Vault Cycles...")
        await session.execute(text("UPDATE vault_cycles SET sniper_wins = 0, cycle_number = 1, cycle_profit = 0.0, cycle_losses = 0.0, mega_cycle_wins = 0, mega_cycle_number = 1, accumulated_vault = 0.0, vault_total = 0.0, used_symbols_in_cycle = '[]', cycle_start_bankroll = 100.0 WHERE id = 1"))
        
        # Slots
        print("Limpando Slots...")
        await session.execute(text("TRUNCATE TABLE slots RESTART IDENTITY"))
        from services.database_service import Slot
        for i in range(1, 5):
            session.add(Slot(id=i, status_risco="LIVRE", leverage=50.0))
        
        # Outras Tabelas
        print("Truncando tabelas de historico (trade_history, moonbags, order_genesis, system_state)...")
        await session.execute(text("TRUNCATE TABLE trade_history RESTART IDENTITY CASCADE"))
        await session.execute(text("TRUNCATE TABLE moonbags RESTART IDENTITY CASCADE"))
        await session.execute(text("TRUNCATE TABLE order_genesis RESTART IDENTITY CASCADE"))
        await session.execute(text("TRUNCATE TABLE system_state RESTART IDENTITY CASCADE"))
        
        await session.commit()
        print("✅ Postgres Atomic Purge Complete.")

    print("--- FIM ---")
    sys.exit(0)

if __name__ == "__main__":
    try:
        asyncio.run(execute_reset())
    except SystemExit:
        pass
