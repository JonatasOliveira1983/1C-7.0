import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def check():
    url = os.getenv("DATABASE_URL")
    if not url:
        print("No DATABASE_URL found")
        return
    
    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        cur.execute("SELECT id, symbol, vision_url, unified_confidence FROM slots WHERE symbol IS NOT NULL;")
        rows = cur.fetchall()
        print("=== POSTGRES SLOTS ===")
        for row in rows:
            print(row)
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check()
