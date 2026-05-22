import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.backtest import data_extractor

async def test():
    print("Testing download_klines for AVAXUSDT.P, interval 4h...")
    symbol = "AVAXUSDT.P"
    interval = "4h"
    limit = 5
    
    res = data_extractor.download_klines(symbol, interval, limit=limit)
    print(f"Result: {res} records saved.")

if __name__ == "__main__":
    asyncio.run(test())
