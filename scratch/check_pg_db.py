import psycopg2
import json

def run():
    url = "postgresql://postgres:JSLsEfBVPywKuYJSAypuNPVvIgYwGXzz@centerbeam.proxy.rlwy.net:54059/railway"
    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        cur.execute("SELECT * FROM slots WHERE symbol IS NOT NULL AND symbol != '' ORDER BY id LIMIT 5;")
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]
        
        filtered_data = []
        for row in rows:
            data_dict = dict(zip(cols, row))
            essential = {k: v for k, v in data_dict.items() if k in ['id', 'symbol', 'side', 'status_risco', 'entry_price', 'current_stop', 'target_price', 'leverage', 'pnl_percent', 'roi']}
            filtered_data.append(essential)
            
        print(json.dumps(filtered_data, indent=2, default=str))
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    run()
