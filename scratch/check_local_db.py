
import sqlite3
import os

def check_local_db():
    db_path = r"c:\Users\spcom\Desktop\10D REAL 5.0\1CRYPTEN_SPACE_V4.0\backend\local_sniper.db"
    if not os.path.exists(db_path):
        print("local_sniper.db not found.")
        return
        
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        print("--- CHECKING SLOTS (LOCAL) ---")
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='slots';")
        if not cur.fetchone():
            print("Table 'slots' not found.")
        else:
            cur.execute("SELECT id, symbol, status_risco, pnl_percent FROM slots ORDER BY id;")
            rows = cur.fetchall()
            for row in rows:
                print(row)
            
        print("\n--- CHECKING BANCA (LOCAL) ---")
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='banca_status';")
        if not cur.fetchone():
            print("Table 'banca_status' not found.")
        else:
            cur.execute("SELECT id, saldo_total, status FROM banca_status;")
            rows = cur.fetchall()
            for row in rows:
                print(row)
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_local_db()
