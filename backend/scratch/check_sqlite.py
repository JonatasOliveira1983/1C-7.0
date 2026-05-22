import sqlite3
import json

try:
    conn = sqlite3.connect('local_sniper.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM slots")
    rows = cursor.fetchall()
    colnames = [description[0] for description in cursor.description]
    results = [dict(zip(colnames, row)) for row in rows]
    print(json.dumps(results, indent=2))
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
