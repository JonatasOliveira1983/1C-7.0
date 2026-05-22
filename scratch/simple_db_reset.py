
import asyncio
import os
import sys
from sqlalchemy import delete, update

# Adiciona o diretório backend ao path
backend_dir = r"C:\Users\spcom\Desktop\10D REAL 5.0\1CRYPTEN_SPACE_V4.0\backend"
sys.path.append(backend_dir)

from services.database_service import database_service, Slot, TradeHistory, Moonbag, OrderGenesis, BancaStatus

async def simple_reset():
    print("Iniciando Reset Simples...")
    await database_service.initialize()
    async with database_service.AsyncSessionLocal() as session:
        # Limpa tabelas
        await session.execute(delete(TradeHistory))
        await session.execute(delete(Moonbag))
        await session.execute(delete(OrderGenesis))
        
        # Limpa Slots
        await session.execute(update(Slot).values(
            symbol=None, side=None, qty=0.0, entry_price=0.0,
            status_risco="LIVRE", pnl_percent=0.0
        ))
        
        # Reset Banca
        banca = await session.get(BancaStatus, 1)
        if banca:
            banca.saldo_total = 100.0
            banca.status = "RESET_OK"
        else:
            session.add(BancaStatus(id=1, saldo_total=100.0, status="RESET_OK"))
            
        await session.commit()
    print("Reset concluído com sucesso.")

if __name__ == "__main__":
    asyncio.run(simple_reset())
