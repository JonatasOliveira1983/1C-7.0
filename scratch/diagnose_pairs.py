import urllib.request
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

PAIRS = [
    "BTCUSDT", "ETHUSDT", "AVAXUSDT", "PYTHUSDT", "APTUSDT", "SUIUSDT",
    "OPUSDT", "ARBUSDT", "RENDERUSDT", "NEARUSDT", "INJUSDT", "TIAUSDT",
    "LINKUSDT", "DOTUSDT", "ADAUSDT", "POLUSDT", "ATOMUSDT", "LTCUSDT",
    "BCHUSDT", "XLMUSDT", "XRPUSDT", "TRXUSDT", "SEIUSDT", "FILUSDT",
    "FTMUSDT", "AAVEUSDT", "ALGOUSDT", "IMXUSDT", "GALAUSDT", "GRTUSDT",
    "CRVUSDT", "EGLDUSDT"
]

print("=========================================================")
print("DIAGNOSTICANDO COCKPIT SNIPER - 32 PARES CONCORRENTE RESILIENTE")
print("=========================================================")

def test_pair(pair):
    url = f"http://localhost:8085/api/market/study?symbol={pair}.P&interval=30&limit=10"
    start_time = time.time()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5.5) as response:
            data = json.loads(response.read().decode('utf-8'))
            elapsed = time.time() - start_time
            klines = data.get("klines", [])
            if klines:
                return pair, True, f"{len(klines)} klines", elapsed, f"Close: {klines[-1][4]}"
            else:
                return pair, False, "Vazio", elapsed, "Retorno vazio da API"
    except Exception as e:
        elapsed = time.time() - start_time
        return pair, False, "Erro", elapsed, str(e)

results = []
success_count = 0
fail_count = 0

with ThreadPoolExecutor(max_workers=32) as executor:
    futures = {executor.submit(test_pair, pair): pair for pair in PAIRS}
    for future in as_completed(futures):
        pair, success, status, elapsed, detail = future.result()
        results.append((pair, success, status, elapsed, detail))
        if success:
            success_count += 1
            print(f"[OK] {pair:<12} | {status:<9} | {elapsed:.2f}s | {detail}")
        else:
            fail_count += 1
            print(f"[FALHA] {pair:<12} | {status:<9} | {elapsed:.2f}s | {detail}")

print("=========================================================")
print(f"DIAGNÓSTICO CONCLUÍDO | SUCESSOS: {success_count} | FALHAS/VAZIOS: {fail_count}")
print("=========================================================")
