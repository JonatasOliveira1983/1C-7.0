import sys
import sqlite3
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from services.openviking_context_service import openviking_context_service

def retrofit():
    conn = sqlite3.connect("backend/local_sniper.db")
    c = conn.cursor()
    c.execute("""
        SELECT id, symbol, direction, strategy, entry_price, current_price, pnl_pct, status, closed_at, contract_meta 
        FROM sandbox_trades 
        WHERE status LIKE 'CLOSED%' 
        ORDER BY closed_at DESC 
        LIMIT 10
    """)
    rows = c.fetchall()
    conn.close()

    count = 0
    for r in rows:
        trade_id = r[0]
        symbol = r[1]
        direction = r[2]
        strategy = r[3]
        entry_price = r[4]
        exit_price = r[5]
        pnl_pct = r[6]
        status = r[7]
        closed_at = r[8]
        meta = r[9]

        clean_sym = symbol.replace("-USDT-SWAP", "").replace("USDT", "")
        slug = f"case_{clean_sym.lower()}_{trade_id}"
        uri = f"viking://user/memories/cases/{slug}"

        # If already exists, skip
        if uri in openviking_context_service.nodes:
            print(f"Skipping already recorded: {uri}")
            continue

        node = openviking_context_service.record_trade_closure({
            "id": trade_id,
            "symbol": symbol,
            "direction": direction,
            "strategy": strategy,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl_pct": pnl_pct,
            "exit_reason": status,
            "contract_meta": meta
        })
        print(f"Recorded to OpenViking & Journal: {node.uri} | {node.title}")
        count += 1

    print(f"Total retrofitted: {count}")

if __name__ == "__main__":
    retrofit()
