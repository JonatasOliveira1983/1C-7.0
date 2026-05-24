import urllib.request
import json
import time

url = "http://localhost:8085/api/market/study?symbol=BTCUSDT.P&interval=30&limit=10"
print(f"Testando requisição para BTCUSDT na rota do cockpit local: {url}")
start_time = time.time()
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode('utf-8'))
        elapsed = time.time() - start_time
        klines = data.get("klines", [])
        print(f"Sucesso! Cockpit respondeu em {elapsed:.2f}s!")
        print(f"Klines recebidas: {len(klines)}")
        if klines:
            print(f"Última vela (Close): {klines[-1][4]}")
except Exception as e:
    elapsed = time.time() - start_time
    print(f"Erro em {elapsed:.2f}s: {e}")
