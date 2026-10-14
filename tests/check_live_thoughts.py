import httpx

r = httpx.get("http://127.0.0.1:8085/api/v1/hermes/laya/thought", timeout=10.0)
print("STATUS CODE:", r.status_code)
data = r.json()
thoughts = data.get("thoughts", [])
print(f"TOTAL THOUGHTS: {len(thoughts)}")
for t in thoughts[-10:]:
    print(f"[{t.get('time')}] [{t.get('symbol')}] ({t.get('action')}) -> {t.get('thought')}")
