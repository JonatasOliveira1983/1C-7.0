import sqlite3

def diag():
    try:
        conn = sqlite3.connect('local_sniper.db')
        cur = conn.cursor()
        
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cur.fetchall()
        print(f"Tables: {tables}")
        
        for table in tables:
            t_name = table[0]
            print(f"\nColumns in {t_name}:")
            cur.execute(f"PRAGMA table_info({t_name});")
            cols = cur.fetchall()
            for col in cols:
                print(col)
                
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    diag()
