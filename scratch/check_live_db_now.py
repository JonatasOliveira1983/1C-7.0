
import asyncio
import os
import psycopg2
from urllib.parse import urlparse

async def check_db():
    db_url = "postgresql://postgres:JSLsEfBVPywKuYJSAypuNPVvIgYwGXzz@centerbeam.proxy.rlwy.net:54059/railway"
    
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        print("--- CHECKING SLOTS ---")
        cur.execute("SELECT id, symbol, status_risco, pnl_percent FROM slots ORDER BY id;")
        rows = cur.fetchall()
        for row in rows:
            print(row)
            
        print("\n--- CHECKING BANCA ---")
        cur.execute("SELECT id, saldo_total, status FROM banca_status;")
        rows = cur.fetchall()
        for row in rows:
            print(row)
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_db())
