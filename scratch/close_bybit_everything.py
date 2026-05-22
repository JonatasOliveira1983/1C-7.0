import asyncio
import os
import sys

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(backend_dir, "..", "1CRYPTEN_SPACE_V4.0", "backend"))

from services.bybit_rest import bybit_rest_service
from config import settings

async def close_everything():
    print("[BYBIT-CLEANUP] Starting total position liquidation...")
    try:
        await bybit_rest_service.initialize()
    except Exception as init_err:
        print(f"Init error: {init_err}")
    
    # 1. Cancel all orders
    print("Canceling all pending orders...")
    try:
        # Since cancel_all_orders is missing, we use the session directly
        response = await asyncio.to_thread(bybit_rest_service.session.cancel_all_orders, category=settings.BYBIT_CATEGORY, settleCoin="USDT")
        print(f"Orders canceled: {response.get('retMsg')}")
    except Exception as e:
        print(f"Failed to cancel orders: {e}")

    # 2. Close all positions
    print("Fetching active positions...")
    try:
        positions = await bybit_rest_service.get_active_positions()
    except Exception as pos_err:
        print(f"Pos error: {pos_err}")
        positions = []
    
    if not positions:
        print("No active positions found.")
    else:
        print(f"Found {len(positions)} positions. Closing...")
        for pos in positions:
            symbol = pos["symbol"]
            side = pos["side"]
            qty = float(pos["size"])
            print(f"   - Closing {symbol} ({side}) | Qty: {qty}")
            try:
                success = await bybit_rest_service.close_position(symbol, side, qty, reason="NUCLEAR_RESET")
                if success:
                    print(f"     OK: {symbol} closed.")
                else:
                    print(f"     FAIL: {symbol} not closed.")
            except Exception as e:
                print(f"     ERROR closing {symbol}: {e}")

    print("\n[BYBIT-CLEANUP] Done.")

if __name__ == "__main__":
    asyncio.run(close_everything())
