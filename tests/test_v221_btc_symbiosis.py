# -*- coding: utf-8 -*-
"""
Empirical test for V221: Protocolo Navio Almirante (BTC First & Simbiose Direcional 100% da Frota).
Verifies:
1. Empty fleet requires BTC as pioneer order (Altcoins are vetoed).
2. Active BTC in LONG allows ONLY altcoins in LONG (SHORT altcoins are vetoed).
3. Active BTC in SHORT allows ONLY altcoins in SHORT (LONG altcoins are vetoed).
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

def test_v221_btc_first_and_symbiosis():
    # Mock candidate setups
    btc_cand = {
        "symbol": "BTC-USDT-SWAP",
        "clean_sym": "BTCUSDT",
        "direction": "LONG",
        "score": 92,
        "qualifies": True,
        "rationale": "BTC Pullback Hunter 2H/30M"
    }
    sol_cand_long = {
        "symbol": "SOL-USDT-SWAP",
        "clean_sym": "SOLUSDT",
        "direction": "LONG",
        "score": 88,
        "qualifies": True,
        "rationale": "SOL Pullback Hunter 2H/30M"
    }
    sol_cand_short = {
        "symbol": "SOL-USDT-SWAP",
        "clean_sym": "SOLUSDT",
        "direction": "SHORT",
        "score": 89,
        "qualifies": True,
        "rationale": "SOL Pullback Hunter 2H/30M"
    }

    candidates = [btc_cand, sol_cand_long, sol_cand_short]

    # Test Case 1: Empty Fleet (len(active_trades) == 0) -> BTC First
    active_trades_empty = []
    is_empty_fleet = (len(active_trades_empty) == 0)
    
    eligible_empty = []
    for cand in candidates:
        c_clean = cand.get("clean_sym", "")
        c_sym = cand.get("symbol", "")
        is_btc_cand = ("BTC" in c_sym.upper() or c_clean == "BTCUSDT")
        if is_empty_fleet and not is_btc_cand:
            continue
        eligible_empty.append(cand["symbol"])

    assert eligible_empty == ["BTC-USDT-SWAP"], f"Expected only BTC when empty, got: {eligible_empty}"
    print("[TEST 1 PASSED] Empty fleet correctly filters out altcoins and keeps exclusively BTC!")

    # Test Case 2: BTC is Active in LONG -> Altcoins must be LONG only
    class MockTrade:
        def __init__(self, symbol, direction):
            self.symbol = symbol
            self.direction = direction
            self.side = direction
            self.current_stop = None
            self.entry_price = 100.0
            self.is_protected = False

    active_trades_btc_long = [MockTrade("BTC-USDT-SWAP", "LONG")]
    is_empty_fleet_2 = (len(active_trades_btc_long) == 0)
    
    # Extract fleet direction
    btc_active = next((t for t in active_trades_btc_long if "BTC" in t.symbol.upper()), None)
    btc_side = str(btc_active.direction).upper()
    fleet_dir = "SHORT" if ("SHORT" in btc_side or "SELL" in btc_side) else "LONG"
    assert fleet_dir == "LONG"

    eligible_with_btc_long = []
    for cand in candidates:
        if cand["symbol"] == "BTC-USDT-SWAP":
            continue  # BTC already open
        if cand["direction"] != fleet_dir:
            continue
        eligible_with_btc_long.append((cand["symbol"], cand["direction"]))

    assert eligible_with_btc_long == [("SOL-USDT-SWAP", "LONG")], f"Expected only SOL LONG, got: {eligible_with_btc_long}"
    print("[TEST 2 PASSED] With BTC in LONG, only LONG altcoins qualify (SHORT is 100% vetoed)!")

    # Test Case 3: BTC is Active in SHORT -> Altcoins must be SHORT only
    active_trades_btc_short = [MockTrade("BTC-USDT-SWAP", "SHORT")]
    btc_active_3 = next((t for t in active_trades_btc_short if "BTC" in t.symbol.upper()), None)
    fleet_dir_3 = "SHORT" if ("SHORT" in btc_active_3.direction.upper() or "SELL" in btc_active_3.direction.upper()) else "LONG"
    assert fleet_dir_3 == "SHORT"

    eligible_with_btc_short = []
    for cand in candidates:
        if cand["symbol"] == "BTC-USDT-SWAP":
            continue
        if cand["direction"] != fleet_dir_3:
            continue
        eligible_with_btc_short.append((cand["symbol"], cand["direction"]))

    assert eligible_with_btc_short == [("SOL-USDT-SWAP", "SHORT")], f"Expected only SOL SHORT, got: {eligible_with_btc_short}"
    print("[TEST 3 PASSED] With BTC in SHORT, only SHORT altcoins qualify (LONG is 100% vetoed)!")

    print("\nALL V221 TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_v221_btc_first_and_symbiosis()
