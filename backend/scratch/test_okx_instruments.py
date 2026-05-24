import urllib.request
import json

url = "https://www.okx.com/api/v5/public/instruments?instType=SWAP"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode('utf-8'))
    print("Code:", data.get("code"))
    print("Keys of first item:", data["data"][0].keys() if data.get("data") else "Empty data")
    if data.get("data"):
        usdt_swaps = [item for item in data["data"] if item.get("instId", "").endswith("-USDT-SWAP")]
        print("Total USDT SWAP pairs:", len(usdt_swaps))
        for item in usdt_swaps[:5]:
            print(f"instId: {item.get('instId')}, state: {item.get('state')}, lever: {item.get('lever')}, maxLvrg: {item.get('maxLvrg')}")
except Exception as e:
    print("Error:", e)
