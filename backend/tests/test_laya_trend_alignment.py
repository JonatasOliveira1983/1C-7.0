"""
TDD Tests for Laya Sovereign 2H/30M Trend Alignment & Pullback Hunter Engine.
Enforces:
1. Strict 2H Directional Subordination:
   - SMA 8 < SMA 21 (2H) -> SHORT_ONLY regime, all LONG setups strictly vetoed.
   - SMA 8 > SMA 21 (2H) -> LONG_ONLY regime, all SHORT setups strictly vetoed.
2. 30M Pullback Hunter Trigger:
   - Identifies pullback retests towards SMA 8 / SMA 21 on 30M with rejection.
3. Directional Quarantine:
   - A stop on LONG penalizes only LONG, leaving SHORT 100% eligible.
"""

import pytest
import time
from unittest.mock import MagicMock


def test_2h_directional_subordination_short_only():
    """Validates that a pair with SMA 8 < SMA 21 in 2H is strictly SHORT_ONLY."""
    from app.services.laya_router_service import laya_router_service

    # Mock candles where SMA 8 is well below SMA 21
    # 2H candles formatted as [ts, open, high, low, close, vol]
    # Decreasing close prices from 1.20 down to 0.85
    c2h = []
    base_ts = int(time.time()) - (50 * 7200)
    for i in range(50):
        px = 1.30 - (i * 0.009) # Downtrend
        c2h.append([str(base_ts + i * 7200), str(px + 0.01), str(px + 0.02), str(px - 0.01), str(px), "1000000"])

    regime_info = laya_router_service.enforce_2h_directional_regime("SUI-USDT-SWAP", c2h)
    
    assert regime_info["regime"] == "SHORT_ONLY"
    assert regime_info["allowed_direction"] == "SHORT"
    assert regime_info["long_vetoed"] is True
    assert regime_info["short_vetoed"] is False


def test_2h_directional_subordination_long_only():
    """Validates that a pair with SMA 8 > SMA 21 in 2H is strictly LONG_ONLY."""
    from app.services.laya_router_service import laya_router_service

    # Increasing close prices from 10.0 to 18.0
    c2h = []
    base_ts = int(time.time()) - (50 * 7200)
    for i in range(50):
        px = 10.0 + (i * 0.15) # Uptrend
        c2h.append([str(base_ts + i * 7200), str(px - 0.05), str(px + 0.1), str(px - 0.1), str(px), "1000000"])

    regime_info = laya_router_service.enforce_2h_directional_regime("SOL-USDT-SWAP", c2h)
    
    assert regime_info["regime"] == "LONG_ONLY"
    assert regime_info["allowed_direction"] == "LONG"
    assert regime_info["long_vetoed"] is False
    assert regime_info["short_vetoed"] is True


def test_30m_pullback_trigger_rejection():
    """Validates 30M pullback retest detection towards SMA 8/21."""
    from app.services.laya_router_service import laya_router_service

    # In a downtrend, price bounces to touch SMA 8/21 and leaves an upper wick (rejection)
    c30m = []
    base_ts = int(time.time()) - (30 * 1800)
    # 25 candles declining around 0.90
    for i in range(25):
        px = 1.00 - (i * 0.005)
        c30m.append([str(base_ts + i * 1800), str(px), str(px + 0.005), str(px - 0.005), str(px), "500000"])
    
    # Recent candle 28-29: pullback up to touch SMA, then rejected downwards
    # Candle with high upper wick
    c30m.append([str(base_ts + 26 * 1800), "0.875", "0.890", "0.870", "0.872", "800000"])
    c30m.append([str(base_ts + 27 * 1800), "0.872", "0.888", "0.868", "0.870", "950000"])

    current_price = 0.870
    pullback = laya_router_service.calculate_30m_pullback_trigger(
        symbol="SUI-USDT-SWAP",
        klines_30m=c30m,
        current_price=current_price,
        macro_direction="SHORT"
    )

    assert pullback["has_pullback_setup"] is True
    assert pullback["score_boost"] >= 10
    assert "PULLBACK_REJEICAO" in pullback["reason"]


def test_directional_quarantine_independence():
    """Validates that a stop on LONG penalizes only LONG, leaving SHORT eligible."""
    from app.services.laya_router_service import laya_router_service

    sym = "TEST-USDT-SWAP"
    # Apply a penalty on LONG direction
    laya_router_service.register_directional_penalty(sym, direction="LONG", penalty_pts=20, reason="Stop em LONG")

    assert laya_router_service.is_direction_penalized(sym, "LONG") is True
    assert laya_router_service.is_direction_penalized(sym, "SHORT") is False
    assert laya_router_service.get_directional_penalty(sym, "LONG") == 20
    assert laya_router_service.get_directional_penalty(sym, "SHORT") == 0
