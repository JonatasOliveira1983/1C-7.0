import asyncio
import os
import sys

# Adicionar o diretório atual ao path para importar database_service
sys.path.append(os.getcwd())

from services.database_service import database_service

async def main():
    await database_service.initialize()
    trades = await database_service.get_trade_history(limit=5, symbol="OPUSDT")
    print(f"Found {len(trades)} trades for OPUSDT")
    for t in trades:
        print(f"ID: {t.get('id')}")
        print(f"Order ID: {t.get('order_id')}")
        print(f"Genesis ID: {t.get('genesis_id')}")
        print(f"Symbol: {t.get('symbol')}")
        print(f"PNL%: {t.get('pnl_percent')}%")
        print(f"Reason: {t.get('close_reason')}")
        print(f"Vision URL: {t.get('vision_url')}")
        print(f"Data Vision Intel: {t.get('data', {}).get('vision_intel') is not None}")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(main())
