
import asyncio
import os
import sys
from datetime import datetime

# Garantir que o path inclua o backend
sys.path.append(os.getcwd())

from services.sovereign_service import sovereign_service

async def clear_rtdb_pnl():
    print("--- Limpando fantasmas de PnL no RTDB ---")
    
    # IMPORTANTE: Inicializar o sovereign_service para conectar no RTDB
    await sovereign_service.initialize()
    
    if not sovereign_service.rtdb:
        print("ERROR: RTDB nao inicializado apos tentativa de init.")
        return

    try:
        # Zerar o PnL ao vivo
        sovereign_service.rtdb.child("live_pnl").update({
            "total_float_roi": 0,
            "total_float_pnl": 0,
            "active_count": 0,
            "slots_roi": {},
            "slots_pnl": {}
        })
        print("DONE: live_pnl zerado.")

        # Zerar o pulso do sistema (que contém a banca e integridade)
        sovereign_service.rtdb.child("system_pulse").update({
            "global_pnl_usd": 0,
            "global_pnl_percent": 0,
            "equity": 100.0,
            "balance": 100.0
        })
        print("DONE: system_pulse purificado.")
        
    except Exception as e:
        print(f"ERROR: Erro ao limpar RTDB: {e}")

if __name__ == "__main__":
    asyncio.run(clear_rtdb_pnl())
