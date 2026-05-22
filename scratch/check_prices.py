import requests
import json

def get_prices():
    symbols = ["LINKUSDT", "SUIUSDT", "APTUSDT", "ATOMUSDT"]
    results = {}
    for s in symbols:
        try:
            url = f"https://api.bybit.com/v5/market/tickers?category=linear&symbol={s}"
            r = requests.get(url).json()
            price = r["result"]["list"][0]["lastPrice"]
            results[s] = float(price)
        except Exception as e:
            results[s] = str(e)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    get_prices()
