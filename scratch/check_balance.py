# -*- coding: utf-8 -*-
import asyncio
import os
import sys

sys.path.append(os.path.join(os.getcwd(), "1CRYPTEN_SPACE_V4.0", "backend"))
from services.database_service import database_service

async def verify():
    try:
        await database_service.initialize()
        banca = await database_service.get_banca_status()
        print(f"SALDO_ATUAL: {banca.get('saldo_total')}")
    except Exception as e:
        print(f"ERRO: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
