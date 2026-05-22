import asyncio
import logging
import sys
import os

# Adiciona o path do backend
sys.path.append(os.getcwd())

from services.database_service import database_service
from services.sovereign_service import sovereign_service

async def execute_reset():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("NuclearReset")
    
    print("\n" + "!"*50)
    print("!!! INICIANDO RESET NUCLEAR V2 (V110.518) !!!")
    print("!"*50 + "\n")
    
    try:
        # 1. Initialize DB
        await database_service.initialize()
        
        # 2. Execute SQL Reset
        success = await database_service.reset_system_data()
        
        if success:
            logger.info("✅ Dados do Postgres limpos com sucesso.")
            
            # 3. Clear memory caches (Sovereign)
            # Reseta o saldo localmente para refletir na UI imediatamente
            await sovereign_service.update_bankroll(100.0)
            
            # Limpa o radar pulse cache
            sovereign_service.radar_pulse_cache = {"signals": [], "decisions": [], "updated_at": 0}
            sovereign_service.signal_buffer.clear()
            sovereign_service.log_buffer.clear()
            
            logger.info("✅ Cache de Memória do Sovereign limpo.")
            print("\n" + "="*50)
            print("🚀 RESET CONCLUÍDO: Banca em $100.00, Slots Livres.")
            print("="*50 + "\n")
        else:
            logger.error("❌ Falha ao executar reset no banco de dados.")
            
    except Exception as e:
        logger.error(f"❌ Erro fatal no reset: {e}")

if __name__ == "__main__":
    asyncio.run(execute_reset())
