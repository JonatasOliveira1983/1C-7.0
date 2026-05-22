import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "1CRYPTEN_SPACE_V4.0", "backend"))

from services.database_service import database_service

async def check_bankroll():
    banca = await database_service.get_banca_status()
    print(f"SALDO_ATUAL: {banca.get('saldo_total')}")

if __name__ == "__main__":
    asyncio.run(check_bankroll())
