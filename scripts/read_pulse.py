import httpx

r = httpx.get('http://127.0.0.1:8085/api/v1/hermes/laya/pulse', timeout=20.0)
data = r.json()
print("Sovereign:", data.get("sovereign"))
print("Regime:", data.get("regime"), "| Mode:", data.get("regime_mode"))
print("Total thoughts:", len(data.get("thoughts", [])))
print("-" * 60)
for t in data.get("thoughts", [])[-12:]:
    print(f"[{t.get('time')}] {t.get('symbol')} ({t.get('action')}, conf={t.get('confidence')}%): {t.get('thought')}")
