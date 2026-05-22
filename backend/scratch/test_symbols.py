import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.getcwd())

from services.bybit_rest import bybit_rest_service
import logging
logging.basicConfig(level=logging.INFO)

async def test():
    await bybit_rest_service.initialize()
    res_fet = await bybit_rest_service.get_klines('FETUSDT', '60', 10)
    print(f"FET klines: {len(res_fet)}")
    res_asi = await bybit_rest_service.get_klines('ASIUSDT', '60', 10)
    print(f"ASI klines: {len(res_asi)}")
    
    # Check tickers too
    tick_fet = await bybit_rest_service.get_tickers('FETUSDT')
    print(f"FET ticker: {len(tick_fet.get('result', {}).get('list', []))}")
    tick_asi = await bybit_rest_service.get_tickers('ASIUSDT')
    print(f"ASI ticker: {len(tick_asi.get('result', {}).get('list', []))}")

if __name__ == "__main__":
    asyncio.run(test())
