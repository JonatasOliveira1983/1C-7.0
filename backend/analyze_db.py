import sqlite3
import json

conn = sqlite3.connect('local_sniper.db')
c = conn.cursor()

c.execute("PRAGMA table_info(sandbox_trades);")
cols = [r[1] for r in c.fetchall()]
print("SANDBOX_TRADES COLUMNS:", cols)

c.execute("SELECT COUNT(*) FROM sandbox_trades;")
print("TOTAL ROWS:", c.fetchone()[0])

c.execute("SELECT status, count(*) FROM sandbox_trades GROUP BY status;")
print("STATUS BREAKDOWN:", c.fetchall())

c.execute("SELECT * FROM sandbox_trades ORDER BY opened_at DESC LIMIT 5;")
for r in c.fetchall():
    row_dict = dict(zip(cols, r))
    # print some fields
    print({k: row_dict[k] for k in ['id', 'symbol', 'direction', 'status', 'entry_price', 'current_price', 'pnl_pct', 'current_roi', 'max_roi']})
