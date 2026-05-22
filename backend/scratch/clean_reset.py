import asyncio
import logging
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "1CRYPTEN_SPACE_V4.0", "backend"))

from services.database_service import database_service

async def run_reset():
    logging.basicConfig(level=logging.INFO)
    print("--- Iniciando Protocolo de Reset Nuclear (V5.7) ---")
    
    # Em ambientes locais, o .env deve ser carregado
    from config import settings
    print(f"Banco de Dados Alvo: {settings.FIREBASE_DATABASE_URL or 'Postgres/Railway'}")
    
    success = await database_service.reset_system_data()
    
    if success:
        print("OK: SISTEMA RESETADO: Vault limpo, Banca em $100.00, Slots liberados.")
    else:
        print("ERR: FALHA NO RESET: Verifique os logs do DatabaseService.")

if __name__ == "__main__":
    asyncio.run(run_reset())
