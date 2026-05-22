import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backtest_data.db")
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "count_klines_res.txt")

def check():
    lines = []
    lines.append(f"Lendo banco em: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        lines.append("Banco de dados não encontrado!")
        with open(OUT_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return
        
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Listar as tabelas
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = c.fetchall()
        lines.append(f"Tabelas: {[t[0] for t in tables]}")
        
        # Contar por par e intervalo
        c.execute("""
            SELECT symbol, interval, COUNT(*), MIN(start_time), MAX(start_time)
            FROM klines
            GROUP BY symbol, interval
            ORDER BY COUNT(*) DESC
            LIMIT 50
        """)
        rows = c.fetchall()
        lines.append("\nTop 50 Contagem de Klines por Símbolo e Intervalo:")
        lines.append(f"{'Símbolo':20} | {'Intervalo':10} | {'Contagem':10} | {'Min Time':15} | {'Max Time':15}")
        lines.append("-" * 80)
        for r in rows:
            import datetime
            min_dt = datetime.datetime.fromtimestamp(r[3]/1000).strftime('%Y-%m-%d %H:%M') if r[3] else "N/A"
            max_dt = datetime.datetime.fromtimestamp(r[4]/1000).strftime('%Y-%m-%d %H:%M') if r[4] else "N/A"
            lines.append(f"{r[0]:20} | {r[1]:10} | {r[2]:10} | {min_dt} | {max_dt}")
            
        conn.close()
    except Exception as e:
        lines.append(f"Erro: {e}")
        
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("Salvo em:", OUT_PATH)

if __name__ == "__main__":
    check()
