import asyncio
import os
import sys

backend_path = os.path.abspath("backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from services.database_service import database_service

async def main():
    await database_service.initialize()
    
    # 1. Closed and Active Sandbox Trades
    trades = await database_service.get_sandbox_trades(active_only=False)
    print(f"TOTAL SANDBOX TRADES: {len(trades)}")
    
    total_realized_usd = 0.0
    active_floating_usd = 0.0
    
    closed_trades = [t for t in trades if t.status != "ACTIVE"]
    active_trades = [t for t in trades if t.status == "ACTIVE"]
    
    print(f"CLOSED TRADES: {len(closed_trades)} | ACTIVE TRADES: {len(active_trades)}")
    
    print("\n--- DETALHES DOS ÚLTIMOS 20 TRADES FECHADOS ---")
    for t in closed_trades[-20:]:
        meta = t.contract_meta or {}
        margin = meta.get("margin", 200.0)
        lev = meta.get("leverage", 15)
        # Check how pnl was recorded
        print(f"[{t.symbol}] {t.direction} | Status: {t.status} | ROI%: {t.current_roi:.2f}% | PnL%: {t.pnl_pct:.2f}% | Margin: {margin} | Lev: {lev}")

    # Check database_service total realized pnl calculation
    realized_bal = await database_service.get_sandbox_realized_balance()
    print(f"\nREALIZED BALANCE FROM DB: {realized_bal}")
    print(f"EQUITY DEFENSE LEVEL: {database_service.equity_defense_level}")
    print(f"EQUITY FLOOR: {database_service.equity_floor}")

asyncio.run(main())
