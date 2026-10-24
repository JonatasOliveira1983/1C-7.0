# -*- coding: utf-8 -*-
"""
1CRYPTEN — V169 Trade Invariants Test Suite (TDD)
Tests the 5 core fixes:
1. Macro BTC Dump Veto on Altcoin LONGs (No buying alts during BTC bleed)
2. True Structural Stop Loss (2.0% to 3.8% price distance, no 1.2% mutilation)
3. 2-Hour Symbol Cooldown / Quarantine (Resilient across restarts)
4. Lower Timeframe (5M) Falling Knife Veto
5. Never Give Back Breakeven Calibration (+5.0% protected ROI at +12.0% trigger)
"""

import pytest
import time
from app.services.laya_router_service import laya_router_service
from app.services.laya_btc_specialist_service import laya_btc_specialist
from services.order_projection_service import proj_service


def test_btc_macro_bloodbath_vetoes_altcoin_longs():
    """
    Testa se o Farol Macro do BTC bloqueia expressamente qualquer compra de altcoin
    quando o BTC estiver em queda (< -0.4% ou 24h < -1.0%).
    """
    # Cenário de queda do BTC com dominância alta (exatamente o que ocorreu no trade ZK e ENA)
    res = laya_btc_specialist.classify_altcoin_climate(
        btc_change_24h=-1.2,
        btc_trend_bias=-0.6,
        btc_dominance=59.5,
        dominance_trend="STABLE"
    )
    assert res["climate"] == "ALTCOIN_BLOODBATH"
    assert res["altcoin_long_allowed"] is False
    assert res["altcoin_short_allowed"] is True

    # Avaliação do Alt Pump Ignition sob sangria do BTC
    candidate = {
        "symbol": "ENA-USDT-SWAP",
        "clean_sym": "ENA",
        "score": 85,
        "1c_exp": 78.0,
        "bot_ignition": True
    }
    decor_data = {"correlation": 0.15, "is_decorrelated": True}
    btc_intel = {
        "altcoin_climate": res["climate"],
        "altcoin_long_allowed": res["altcoin_long_allowed"],
        "btc_trend_bias": -0.6,
        "btc_change_24h": -1.2,
        "dominance_trend": "STABLE",
        "btc_dominance": 59.5
    }

    ign_res = laya_router_service.evaluate_alt_pump_ignition(btc_intel, decor_data, candidate)
    assert ign_res["is_ignition"] is False
    assert "VETO_BTC_SANGRIANDO" in ign_res["tag"]


def test_structural_stop_loss_distance_healthy():
    """
    Garante que os setups geram stops com respiro estrutural saudável (2.0% a 3.8%),
    e NUNCA estrangulam o stop em 0.8% a 1.2% do preço.
    """
    current_price = 1.0000
    acc_range = {
        "is_consolidating": True,
        "support_h1": 0.9900,
        "resistance_h1": 1.0500
    }
    
    # 1. DVWAP Reversion LONG
    res_dvwap = laya_router_service.evaluate_dvwap_reversion(
        symbol="DOT-USDT-SWAP",
        current_price=current_price,
        vwap=1.0300,  # Preço esticado -2.9% abaixo da VWAP
        acc_range=acc_range,
        lsr=1.00,
        btc_trend_bias=0.0,
        funding_rate=0.0,
        atr_pct=2.5
    )
    assert res_dvwap["qualifies"] is True
    assert res_dvwap["direction"] == "LONG"
    stop_dist = (current_price - res_dvwap["stop_loss"]) / current_price
    # Stop deve ter respiro estrutural mínimo de 2.0%
    assert 0.020 <= stop_dist <= 0.038

    # 2. Momento Mola LONG
    res_mola = laya_router_service.evaluate_momento_mola(
        symbol="DOT-USDT-SWAP",
        current_price=0.9910,
        acc_range=acc_range,
        bb_width_pct=1.5,
        is_at_support=True,
        lsr=1.00,
        btc_trend_bias=0.0,
        funding_rate=0.0,
        atr_pct=2.5
    )
    assert res_mola["qualifies"] is True
    stop_dist_mola = (0.9910 - res_mola["stop_loss"]) / 0.9910
    assert 0.020 <= stop_dist_mola <= 0.038


def test_symbol_quarantine_resilience():
    """
    Testa se o cooldown por símbolo barra qualquer tentativa de reentrada por 2 horas.
    """
    sym = "ENA"
    laya_router_service.record_stop_loss(sym, direction="LONG", cooldown_seconds=7200)
    assert laya_router_service.is_symbol_in_cooldown("ENA") is True
    assert laya_router_service.is_symbol_in_cooldown("ENAUSDT") is True
    assert laya_router_service.is_symbol_in_cooldown("ENA-USDT-SWAP") is True

    # Símbolo limpo não deve estar em quarentena
    assert laya_router_service.is_symbol_in_cooldown("SOL") is False


def test_breakeven_never_give_back_calibration():
    """
    Verifica se os parâmetros canônicos do Breakeven ativam em +12% de ROI e travam em +5% de ROI.
    """
    from pathlib import Path
    sb_path = Path(__file__).resolve().parent.parent / "services" / "sandbox_service.py"
    content = sb_path.read_text(encoding="utf-8")
    assert "breakeven_trigger = 12.0" in content
    assert "breakeven_target_stop = 5.0" in content


@pytest.mark.asyncio
async def test_lower_tf_exhaustion_method():
    """
    Testa se o método check_lower_tf_exhaustion retorna formato esperado de proteção.
    """
    res = await laya_router_service.check_lower_tf_exhaustion("BTCUSDT", "LONG")
    assert "is_safe" in res
    assert "reason" in res
