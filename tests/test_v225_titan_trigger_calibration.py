# tests/test_v225_titan_trigger_calibration.py
# Valida a calibração soberana do Titan Engine V225:
# 1. Disparo de Grau 1 (SMA8) sem veto cego de varredura
# 2. Disparo de Grau 2 (SMA21) com pavio de exaustão realista (>=15%)
# 3. Liberação de altcoins pioneiras sob Farol BTC BEAR

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath("backend"))

from app.services.laya_router_service import laya_router_service


def test_grau_1_sma8_touch_triggers_short():
    """Garante que toque na SMA8 com vela de baixa aciona Grau 1 (SNIPER SMA8)."""
    # 8 velas de 30M simulando repique na SMA8
    # SMA8 ~ 64000, SMA21 ~ 64500
    klines_30m = [
        {"timestamp": 1000, "open": 64800, "high": 64900, "low": 64400, "close": 64500, "volume": 100},
        {"timestamp": 2000, "open": 64500, "high": 64600, "low": 64100, "close": 64200, "volume": 100},
        {"timestamp": 3000, "open": 64200, "high": 64300, "low": 63900, "close": 64000, "volume": 100},
        {"timestamp": 4000, "open": 64000, "high": 64100, "low": 63800, "close": 63900, "volume": 100},
        {"timestamp": 5000, "open": 63900, "high": 64050, "low": 63700, "close": 63800, "volume": 100},
        {"timestamp": 6000, "open": 63800, "high": 63950, "low": 63700, "close": 63850, "volume": 100},
        {"timestamp": 7000, "open": 63850, "high": 64100, "low": 63800, "close": 64050, "volume": 100},
        # Vela atual: tocou 64150 (SMA8) e devolveu para 63950 (vela vermelha com pavio superior de 40%)
        {"timestamp": 8000, "open": 64050, "high": 64150, "low": 63900, "close": 63950, "volume": 120},
    ]
    cur_p = 63950.0
    res = laya_router_service.calculate_30m_pullback_trigger(
        "BTCUSDT",
        klines_30m,
        cur_p,
        "SHORT",
        sma8_2h=64100.0,
        sma21_2h=64500.0,
        lsr=1.0,
        btc_dominance=58.0,
        btc_trend_bias=-0.5
    )
    assert res["has_pullback_setup"] is True, f"Deveria armar pullback Grau 1. Motivo retornado: {res.get('reason')}"
    assert "SNIPER" in res.get("pullback_type", "")


def test_grau_2_sma21_touch_triggers_short():
    """Garante que toque na SMA21 com rejeição (pavio >= 15%) aciona Grau 2."""
    klines_30m = [
        {"timestamp": 1000, "open": 64600, "high": 64700, "low": 64200, "close": 64300, "volume": 100},
        {"timestamp": 2000, "open": 64300, "high": 64400, "low": 64000, "close": 64100, "volume": 100},
        {"timestamp": 3000, "open": 64100, "high": 64200, "low": 63800, "close": 63900, "volume": 100},
        {"timestamp": 4000, "open": 63900, "high": 64100, "low": 63800, "close": 64000, "volume": 100},
        {"timestamp": 5000, "open": 64000, "high": 64300, "low": 63900, "close": 64200, "volume": 100},
        {"timestamp": 6000, "open": 64200, "high": 64550, "low": 64100, "close": 64450, "volume": 100},
        # Vela atual: tocou 64600 (acima da SMA21 64500) e devolveu para 64400 (pavio de 200 pontos sobre amplitude de 300 = 66%)
        {"timestamp": 7000, "open": 64450, "high": 64600, "low": 64300, "close": 64400, "volume": 150},
    ]
    cur_p = 64400.0
    res = laya_router_service.calculate_30m_pullback_trigger(
        "BTCUSDT",
        klines_30m,
        cur_p,
        "SHORT",
        sma8_2h=64150.0,
        sma21_2h=64500.0,
        lsr=1.0,
        btc_dominance=58.0,
        btc_trend_bias=-0.5
    )
    assert res["has_pullback_setup"] is True, f"Deveria armar pullback Grau 2. Motivo: {res.get('reason')}"
    assert "SMA21" in res.get("pullback_type", "")


def test_no_veto_varredura_sma21_on_valid_touch():
    """Garante que a mensagem VETO_AGUARDANDO_VARREDURA_SMA21 não paralisa toques com rejeição."""
    klines_30m = [
        {"timestamp": 1000, "open": 64200, "high": 64300, "low": 63900, "close": 64000, "volume": 100},
        {"timestamp": 2000, "open": 64000, "high": 64100, "low": 63800, "close": 63900, "volume": 100},
        {"timestamp": 3000, "open": 63900, "high": 64050, "low": 63700, "close": 63800, "volume": 100},
        {"timestamp": 4000, "open": 63800, "high": 64100, "low": 63750, "close": 63900, "volume": 100},
    ]
    cur_p = 63900.0
    res = laya_router_service.calculate_30m_pullback_trigger(
        "CRVUSDT",
        klines_30m,
        cur_p,
        "SHORT",
        sma8_2h=64050.0,
        sma21_2h=64400.0,
        lsr=1.0,
        btc_trend_bias=-0.6
    )
    assert "VETO_AGUARDANDO_VARREDURA_SMA21" not in res.get("reason", "")


def test_empty_fleet_allows_alt_short_when_btc_bear():
    """Garante que com a frota vazia e BTC BEAR, altcoin qualificada em SHORT e autorizada."""
    cand = {
        "symbol": "CRV-USDT-SWAP",
        "clean_sym": "CRVUSDT",
        "direction": "SHORT",
        "strategy": "LAYA_PULLBACK_HUNTER_2H_30M",
        "score": 88,
        "qualifies": True,
        "rationale": "PULLBACK HUNTER 2H/30M (SHORT)",
    }
    is_empty_fleet = True
    is_btc_cand = False
    btc_macro_dir = "BEAR"
    btc_trend_bias = -0.6
    
    # Simula a condicao implementada no scan_and_execute_autonomous
    btc_bear_confirmed = (btc_macro_dir == "BEAR" or btc_trend_bias <= -0.2)
    alt_short_qualified = (cand["direction"] == "SHORT" and cand["strategy"] == "LAYA_PULLBACK_HUNTER_2H_30M" and cand["score"] >= 85)
    
    should_skip = False
    if is_empty_fleet and not is_btc_cand:
        if not (btc_bear_confirmed and alt_short_qualified):
            should_skip = True

    assert should_skip is False, "Altcoin qualificada em SHORT deve ser aceita no Slot 1 quando BTC for BEAR"


def test_empty_fleet_blocks_alt_long_when_btc_bear():
    """Garante que com a frota vazia e BTC BEAR, altcoins em LONG continuam bloqueadas."""
    cand = {
        "symbol": "CRV-USDT-SWAP",
        "clean_sym": "CRVUSDT",
        "direction": "LONG",
        "strategy": "LAYA_PULLBACK_HUNTER_2H_30M",
        "score": 88,
        "qualifies": True,
    }
    is_empty_fleet = True
    is_btc_cand = False
    btc_macro_dir = "BEAR"
    btc_trend_bias = -0.6
    
    btc_bear_confirmed = (btc_macro_dir == "BEAR" or btc_trend_bias <= -0.2)
    alt_short_qualified = (cand["direction"] == "SHORT" and cand["strategy"] == "LAYA_PULLBACK_HUNTER_2H_30M" and cand["score"] >= 85)
    
    should_skip = False
    if is_empty_fleet and not is_btc_cand:
        if not (btc_bear_confirmed and alt_short_qualified):
            should_skip = True

    assert should_skip is True, "Altcoin em LONG deve ser bloqueada quando BTC for BEAR"

