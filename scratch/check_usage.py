import sqlite3
import os

db_path = "data/prospecton.db"
if not os.path.exists(db_path):
    print(f"Banco de dados não encontrado em {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM usage_stats")
        rows = cursor.fetchall()
        print("Service | Today | Total | Last Used")
        print("-" * 40)
        for row in rows:
            print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]}")
    except sqlite3.OperationalError as e:
        print(f"Erro ao acessar tabela usage_stats: {e}")
    conn.close()
