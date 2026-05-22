import sqlite3
import json

def dump_slots():
    try:
        conn = sqlite3.connect("c:\\Users\\spcom\\Desktop\\10D REAL 4.0\\1CRYPTEN_SPACE_V4.0\\backend\\local_sniper.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("--- DATABASE SLOTS ---")
        cursor.execute("SELECT * FROM slots")
        rows = cursor.fetchall()
        for row in rows:
            d = dict(row)
            print(f"Slot {d['id']}: {d['symbol']} | {d['side']} | {d['slot_type']} | {d['status_risco']} | Order: {d['order_id']}")
            
        print("\n--- BANCA STATUS ---")
        cursor.execute("SELECT * FROM banca_status")
        rows = cursor.fetchall()
        for row in rows:
            print(dict(row))
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    dump_slots()
