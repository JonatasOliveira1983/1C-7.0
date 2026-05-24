import urllib.request
import json
import time
import sys

# Garante que o console use UTF-8 ou trate strings de forma segura
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

PAIRS = [
    "BTCUSDT", "ETHUSDT", "AVAXUSDT", "PYTHUSDT", "APTUSDT", "SUIUSDT", "OPUSDT", "ARBUSDT", "RENDERUSDT", 
    "NEARUSDT", "INJUSDT", "TIAUSDT", "LINKUSDT", "DOTUSDT", "ADAUSDT", "POLUSDT", 
    "ATOMUSDT", "LTCUSDT", "BCHUSDT", "XLMUSDT", "XRPUSDT", "TRXUSDT", "SEIUSDT", 
    "FILUSDT", "FTMUSDT", "AAVEUSDT", "ALGOUSDT", "IMXUSDT", "GALAUSDT", "GRTUSDT", 
    "CRVUSDT", "EGLDUSDT"
]

def audit():
    print("=========================================================")
    print("        AUDITORIA DE PORTAS E PARES DO SNIPER STUDY API")
    print("=========================================================")
    
    success_count = 0
    fail_count = 0
    
    for pair in PAIRS:
        symbol = f"{pair}.P"
        url = f"http://127.0.0.1:8085/api/market/study?symbol={symbol}&interval=30&limit=100"
        
        start = time.time()
        try:
            req = urllib.request.Request(url)
            # Timeout aumentado para 15s para a primeira carga do backend/OKX
            with urllib.request.urlopen(req, timeout=15) as response:
                status = response.status
                body = response.read().decode('utf-8')
                data = json.loads(body)
                klines = data.get("klines", [])
                
                if status == 200 and len(klines) > 0:
                    print(f"[OK] {pair:<12} | Status: 200 | Velas: {len(klines):<4} | Tempo: {time.time() - start:.2f}s")
                    success_count += 1
                else:
                    print(f"[SEM_DADOS] {pair:<12} | Status: {status} | Velas: {len(klines):<4}")
                    fail_count += 1
        except urllib.error.HTTPError as he:
            try:
                err_body = he.read().decode('utf-8')
                print(f"[ERRO_HTTP] {pair:<12} | Status: {he.code} | Resposta: {err_body}")
            except:
                print(f"[ERRO_HTTP] {pair:<12} | Status: {he.code}")
            fail_count += 1
        except Exception as e:
            print(f"[FALHA] {pair:<12} | Erro: {e}")
            fail_count += 1
            
    print("=========================================================")
    print(f"AUDITORIA CONCLUÍDA | SUCESSO: {success_count} | FALHAS: {fail_count}")
    print("=========================================================")

if __name__ == "__main__":
    time.sleep(2)
    audit()
