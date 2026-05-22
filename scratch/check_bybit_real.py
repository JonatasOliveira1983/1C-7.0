
import asyncio
import os
import sys
from pybit.unified_trading import HTTP

# Configurações do .env
BYBIT_API_KEY = "ggAuWk4lVoMaKDkxsH"
BYBIT_API_SECRET = "aAHZbYUmRY9ukf0eIW9yVbOA3CuO0wgRKUs7"

async def check_positions():
    session = HTTP(
        testnet=False,
        api_key=BYBIT_API_KEY,
        api_secret=BYBIT_API_SECRET,
    )
    
    print("--- POSIÇÕES REAIS NA BYBIT ---")
    try:
        response = session.get_positions(category="linear", settleCoin="USDT")
        positions = response.get("result", {}).get("list", [])
        
        active = [p for p in positions if float(p.get("size", 0)) > 0]
        
        if not active:
            print("Nenhuma posição ativa encontrada na Bybit.")
        else:
            for p in active:
                print(f"Symbol: {p['symbol']} | Side: {p['side']} | Size: {p['size']} | Entry: {p['avgPrice']} | UnrealPnl: {p['unrealisedPnl']}")
                
    except Exception as e:
        print(f"Erro ao consultar Bybit: {e}")

if __name__ == "__main__":
    asyncio.run(check_positions())
