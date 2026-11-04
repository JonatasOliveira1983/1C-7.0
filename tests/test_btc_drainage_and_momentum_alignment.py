# -*- coding: utf-8 -*-
import sys
import os
import pytest

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.laya_btc_specialist_service import laya_btc_specialist
from app.services.coinglass_heatmap_service import coinglass_heatmap_service
from app.services.laya_router_service import laya_router_service


def test_btc_drainage_allows_altcoin_long_leaders():
    # In BTC_DRAINAGE (BTC.D >= 59.0 and BTC >= 0.3%):
    res = laya_btc_specialist.classify_altcoin_climate(
        btc_change_24h=0.37,
        btc_dominance=59.55,
        dominance_trend="RISING",
        btc_trend_bias=0.5
    )
    assert res["climate"] == "BTC_DRAINAGE"
    assert res["altcoin_long_allowed"] is True
    assert res["altcoin_short_allowed"] is False


def test_heatmap_fast_uptrend_fallback():
    # When candles are in an uptrend, upper pool volume should be >= lower pool
    candles = [
        [1000, 1.0, 1.02, 0.99, 1.01, 50000],
        [1300, 1.01, 1.05, 1.00, 1.04, 80000]
    ]
    res = coinglass_heatmap_service._compute_liquidity_heatmap_fast(
        norm_sym="SUIUSDT",
        current_price=1.04,
        passed_candles=candles
    )
    assert res["dominant_magnet"] == "BULLISH_SWEEP"
    assert res["target_region"] == "ACIMA"


def test_aguia_fusion_stretch_tolerance_under_ignition():
    # SUI in uptrend with 48 hours of 1H candles to calculate 2H SMA21
    candles_1h = []
    base_p = 0.88
    for i in range(48):
        p = base_p + i * 0.003
        candles_1h.append([1000 + i * 3600, p, p + 0.005, p - 0.005, p, 10000])

    fusion = laya_router_service.evaluate_aguia_encryptos_fusion(
        symbol="SUIUSDT",
        current_price=candles_1h[-1][4],
        candles_1h=candles_1h,
        bot_ignition=True,
        c_exp=75.0,
        btc_trend_bias=0.5,
        lsr=1.0
    )
    assert fusion.get("direction") == "LONG"
    assert fusion.get("qualifies") is True
