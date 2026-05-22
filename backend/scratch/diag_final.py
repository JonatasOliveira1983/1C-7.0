import sqlite3
import json

def diag():
    try:
        conn = sqlite3.connect('local_sniper.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        print("=== LOCAL SQLITE SLOTS ===")
        cur.execute("SELECT id, symbol, status_risco, vision_url, unified_confidence, genesis_id FROM slots WHERE symbol IS NOT NULL")
        rows = cur.fetchall()
        for row in rows:
            print(dict(row))
            
        print("\n=== RECENT ORDER GENESIS ===")
        cur.execute("SELECT symbol, timestamp, genesis_id, data FROM order_genesis ORDER BY timestamp DESC LIMIT 5")
        rows = cur.fetchall()
        for row in rows:
            d = dict(row)
            try:
                d['data'] = json.loads(d['data'])
            except:
                pass
            print(d)
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    diag()
