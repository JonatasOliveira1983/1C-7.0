import urllib.request
import json
import time

print("Testando conexão direta com a Bybit pública...")
url = "https://api.bybit.com/v5/market/kline?category=linear&symbol=BTCUSDT&interval=30&limit=10"
start_time = time.time()
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=5) as response:
        data = json.loads(response.read().decode('utf-8'))
        elapsed = time.time() - start_time
        print(f"Bybit respondeu em {elapsed:.2f}s!")
        print(f"Retorno: {data.get('retMsg')}")
except Exception as e:
    elapsed = time.time() - start_time
    print(f"Erro na Bybit em {elapsed:.2f}s: {e}")
