import sqlite3
import json

conn = sqlite3.connect('backend/local_sniper.db')
c = conn.cursor()

c.execute("SELECT id, symbol, direction, entry_price, current_price, pnl_pct, contract_meta, status FROM sandbox_trades WHERE status != 'ACTIVE';")
rows = c.fetchall()

total_recorded_usd = 0.0
total_corrected_15x_usd = 0.0

for tid, sym, direction, ep, cp, pnl_pct, meta_str, status in rows:
    meta = json.loads(meta_str) if isinstance(meta_str, str) else (meta_str or {})
    margin = float(meta.get("margin", 200.0))
    recorded_pnl = float(pnl_pct or 0.0)
    
    # What was recorded
    total_recorded_usd += (recorded_pnl / 100.0) * margin
    
    # Corrected with 15x leverage:
    # Since recorded_pnl was computed with 50x:
    corrected_pnl = recorded_pnl * (15.0 / 50.0)
    total_corrected_15x_usd += (corrected_pnl / 100.0) * margin

print(f"TOTAL TRADES ANALYZED: {len(rows)}")
print(f"TOTAL RECORDED PROFIT (AT 50x BUG): ${total_recorded_usd:.2f}")
print(f"CORRECTED PROFIT (AT 15x REAL):     ${total_corrected_15x_usd:.2f}")
print(f"RATIO: {total_recorded_usd / max(1, total_corrected_15x_usd):.2f}x inflated")
