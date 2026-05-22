import sqlite3
import os

db_path = "backtest_data.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Table info for 'klines':")
    cursor.execute("PRAGMA table_info(klines);")
    for row in cursor.fetchall():
        print(row)
        
    print("\nDistinct intervals in 'klines':")
    cursor.execute("SELECT DISTINCT interval FROM klines;")
    for row in cursor.fetchall():
        print(row)
        
    print("\nSample rows (first 3):")
    cursor.execute("SELECT * FROM klines LIMIT 3;")
    for row in cursor.fetchall():
        print(row)
        
    conn.close()
else:
    print(f"DB not found: {db_path}")
