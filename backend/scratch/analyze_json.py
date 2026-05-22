import json
import os

backup_path = r'c:\Users\spcom\Desktop\10D REAL 4.0\1CRYPTEN_SPACE_V4.0\backend\trade_history_backup.json'
if os.path.exists(backup_path):
    with open(backup_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        print(f"\nRecent 10 trades from trade_history_backup.json:")
        for r in data[-10:]:
            print(f"{r.get('symbol')} | {r.get('side')} | PNL: {r.get('pnl_percent')} | Reason: {r.get('close_reason')}")
            if 'trap' in str(r.get('close_reason')).lower() or 'armadilha' in str(r.get('close_reason')).lower():
                print("  -> TRAP DETECTED IN LOG!")
