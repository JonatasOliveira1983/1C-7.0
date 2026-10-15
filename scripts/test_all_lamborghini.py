import urllib.request
import json
import sys

tests = [
    # Rotas de Páginas
    ("Cockpit (/cockpit)", "http://127.0.0.1:8085/cockpit", ["Cockpit Lamborghini", "FLASH MAP", "charts-grid-container", "setChartGridMode", "viewport-fit=cover"]),
    ("Root (/)", "http://127.0.0.1:8085/", ["Cockpit Lamborghini", "FLASH MAP", "charts-grid-container", "tv-frame-0", "tv-frame-3"]),
    ("Sandbox (/sandbox)", "http://127.0.0.1:8085/sandbox", ["Cockpit", "viewport-fit=cover"]),
    ("Hermes (/hermes)", "http://127.0.0.1:8085/hermes", ["HERMES ORCHESTRATOR", "grid-mobile-stack", "chat-viewport-card"]),
    ("Market (/mercado -> Redirect Cockpit)", "http://127.0.0.1:8085/mercado", ["Cockpit", "viewport-fit=cover"]),
    
    # Assets & Responsividade
    ("CSS (/static/css/lamborghini.css)", "http://127.0.0.1:8085/static/css/lamborghini.css", ["charts-grid-quad", "charts-grid-solo", "charts-grid-dual", "table-responsive-wrap", "grid-mobile-stack"]),
    ("Shell JS (/static/shell.js)", "http://127.0.0.1:8085/static/shell.js", ["mountLamborghiniShell", "app-bottom-bar", "bbar-item"]),
    
    # APIs
    ("API Unified State", "http://127.0.0.1:8085/api/sandbox/unified-state", ["virtual_balance"]),
    ("API Health Check", "http://127.0.0.1:8085/api/health", ["status"]),
    ("API Slots", "http://127.0.0.1:8085/api/slots", []),
    ("API Hermes History", "http://127.0.0.1:8085/api/v1/hermes/history", ["messages"]),
    ("API Radar Pulse", "http://127.0.0.1:8085/api/radar/pulse", []),
    ("API Kronos Projection", "http://127.0.0.1:8085/api/v1/hermes/laya/kronos-projection?symbol=SOLUSDT&side=SHORT&current_price=120.02", ["target_price", "direction", "conviction"]),
    ("API RAG Search", "http://127.0.0.1:8085/api/v1/hermes/rag/search?q=Kronos", ["results", "relevance_score"]),
    ("API ML & Fine-Tuning Status", "http://127.0.0.1:8085/api/v1/ml/status", ["laya", "kronos", "conductor"]),
]

print("=" * 75)
print("  VALIDAÇÃO COMPLETA: 4 GRÁFICOS & RESPONSIVIDADE MOBILE (PORTA 8085)")
print("=" * 75)

all_ok = True
for name, url, expected_tokens in tests:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "1CryptenTester", "Connection": "close"})
        with urllib.request.urlopen(req, timeout=8) as r:
            resp = r.read().decode()
        missing = [tok for tok in expected_tokens if tok.lower() not in resp.lower()]
        if missing:
            print(f"  [FAIL]  {name:<40} -> Ausente: {missing}")
            all_ok = False
        else:
            print(f"  [PASS]  {name:<40} (Tamanho: {len(resp)} bytes)")
    except Exception as e:
        print(f"  [ERROR] {name:<40} -> {e}")
        all_ok = False

print("=" * 75)
if all_ok:
    print("  100% DAS ROTAS, 4 GRÁFICOS E RESPONSIVIDADE MOBILE CONFIRMADOS!")
else:
    print("  ATENÇÃO: Houve falhas na validação.")
print("=" * 75)

if not all_ok:
    sys.exit(1)
