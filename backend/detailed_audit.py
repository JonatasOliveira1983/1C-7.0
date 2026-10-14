import sqlite3
import json

conn = sqlite3.connect('local_sniper.db')
c = conn.cursor()

c.execute("SELECT pnl_pct, contract_meta, opened_at, closed_at, symbol, status FROM sandbox_trades WHERE status != 'ACTIVE';")
rows = c.fetchall()

total_pnl_usd = 0.0
win_count = 0
loss_count = 0
total_win_usd = 0.0
total_loss_usd = 0.0

time_stamps = []

for pnl_pct, meta_str, opened_at, closed_at, symbol, status in rows:
    pnl = float(pnl_pct or 0.0)
    meta = json.loads(meta_str) if isinstance(meta_str, str) else (meta_str or {})
    margin = float(meta.get("margin", 200.0))
    pnl_usd = (pnl / 100.0) * margin
    total_pnl_usd += pnl_usd
    if pnl_usd > 0:
        win_count += 1
        total_win_usd += pnl_usd
    else:
        loss_count += 1
        total_loss_usd += pnl_usd
    if opened_at:
        time_stamps.append(opened_at)

print(f"TOTAL CLOSED TRADES: {len(rows)}")
print(f"WINS: {win_count} | LOSSES: {loss_count} | WIN RATE: {win_count/len(rows)*100:.1f}%")
print(f"GROSS PROFIT: ${total_win_usd:.2f} | GROSS LOSS: ${total_loss_usd:.2f}")
print(f"NET REALIZED PNL USD: ${total_pnl_usd:.2f}")
print(f"CALCULATED BALANCE: ${10000.0 + total_pnl_usd:.2f}")

if time_stamps:
    min_t = min(time_stamps)
    max_t = max(time_stamps)
    duration_hours = (max_t - min_t) / 3600.0
    print(f"DURATION: {duration_hours:.2f} hours (from ts {min_t} to {max_t})")
    print(f"TRADES PER HOUR: {len(rows) / max(0.1, duration_hours):.1f}")
