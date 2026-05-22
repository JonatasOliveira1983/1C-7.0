import sqlite3
import json

def diag():
    try:
        conn = sqlite3.connect('local_sniper.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        print("=== LOCAL SQLITE SLOTS ===")
        cur.execute("SELECT id, symbol, status_risco, vision_url, score, genesis_id FROM slots")
        rows = cur.fetchall()
        for row in rows:
            print(dict(row))
            
        print("\n=== LOCAL SQLITE ORDER GENESIS (SUI/AVAX) ===")
        cur.execute("SELECT order_id, genesis_id, symbol, data FROM order_genesis WHERE symbol LIKE '%SUI%' OR symbol LIKE '%AVAX%'")
        rows = cur.fetchall()
        for row in rows:
            d = dict(row)
            # Try to parse JSON data
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
