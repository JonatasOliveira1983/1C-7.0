import sys
import os
import json
from fastapi.testclient import TestClient

# Adiciona o diretório do backend ao sys.path para os imports funcionarem
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "1CRYPTEN_SPACE_V4.0", "backend")))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "1CRYPTEN_SPACE_V4.0", "backend")))

from main import app

client = TestClient(app)

def test_symbol(symbol):
    print(f"\n--- Testing Symbol: {symbol} ---")
    url = f"/api/market/study?symbol={symbol}&interval=30&limit=600"
    try:
        response = client.get(url)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            klines_count = len(data.get("klines", []))
            patterns_123 = len(data.get("patterns_123", []))
            patterns_abcd = len(data.get("patterns_abcd", []))
            patterns_mola = len(data.get("patterns_mola", []))
            
            print(f"Klines: {klines_count}")
            print(f"Patterns 1-2-3: {patterns_123}")
            print(f"Patterns ABCD: {patterns_abcd}")
            print(f"Patterns Mola: {patterns_mola}")
            
            # Salva o json para inspeção
            out_file = f"scratch/{symbol.lower().replace('.', '_')}_study.json"
            os.makedirs("scratch", exist_ok=True)
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"Saved JSON response to {out_file}")
        else:
            print(f"Error Response: {response.text}")
    except Exception as e:
        print(f"Exception during request: {e}")

if __name__ == "__main__":
    test_symbol("AVAXUSDT.P")
    test_symbol("IMXUSDT.P")
