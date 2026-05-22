import sqlite3
import json
import os

db_path = r'c:\Users\spcom\Desktop\10D REAL 4.0\1CRYPTEN_SPACE_V4.0\backend\local_sniper.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in c.fetchall()]
    
    if 'trade_history' in tables:
        c.execute("SELECT * FROM trade_history ORDER BY closed_at DESC LIMIT 20;")
        rows = c.fetchall()
        print("\nRecent 20 trades from trade_history:")
        for r in rows:
            print(dict(r))
    conn.close()

backup_path = r'c:\Users\spcom\Desktop\10D REAL 4.0\1CRYPTEN_SPACE_V4.0\backend\trade_history_backup.json'
if os.path.exists(backup_path):
    with open(backup_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        print(f"\nRecent 5 trades from trade_history_backup.json:")
        for r in data[-5:]:
            print(f"{r.get('symbol')} | {r.get('side')} | PNL: {r.get('pnl_percent')} | Reason: {r.get('close_reason')} | At: {r.get('closed_at')}")
