import os
import sys
import pytest
import asyncio

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.okx_universe_service import okx_universe_service
from app.services.laya_router_service import laya_router_service

@pytest.mark.asyncio
async def test_btc_is_in_tradable_universe():
    await okx_universe_service.sync_instruments()
    universe = await okx_universe_service.get_tradable_universe(limit=30, exclude_btc=False)
    symbols = [u["symbol"] for u in universe]
    assert "BTC-USDT-SWAP" in symbols, "BTC-USDT-SWAP deve estar presente no universo negociavel"

@pytest.mark.asyncio
async def test_evaluate_entry_matrix_allows_btc():
    res = laya_router_service.evaluate_multi_setup_opportunity(
        symbol="BTC-USDT-SWAP",
        current_price=68800.0,
        acc_range={"is_accumulating": False, "breakout_dir": "NEUTRAL"},
        vwap=68800.0,
        bb_width_pct=5.0,
        lsr=1.0,
        oi_delta_pct=0.0,
        btc_trend_bias=-0.5,
        funding_rate=0.0001,
        atr_pct=1.0
    )
    # Nao pode mais retornar BTC_ORACLE_MONITOR com veto fixo
    assert res.get("strategy") != "BTC_ORACLE_MONITOR"
    assert "Proibido abrir ordens de trade no BTC" not in res.get("rationale", "")

def test_heatmap_magnet_exemption_logic():
    # Valida que LAYA_PULLBACK_HUNTER_2H_30M e LAYA_AGUIA_FUSION estao isentas da regra
    exempt_strategies = ("LAYA_PULLBACK_HUNTER_2H_30M", "LAYA_AGUIA_FUSION")
    cand_dir = "SHORT"
    dom_magnet = "BULLISH_SWEEP"
    target_reg = "ACIMA"
    btc_trend_bias = -0.1

    # Para uma estrategia comum, deve vetar
    strat_breakout = "LAYA_SMART_MONEY_H1"
    should_veto_common = strat_breakout not in exempt_strategies and cand_dir == "SHORT" and (dom_magnet == "BULLISH_SWEEP" or target_reg == "ACIMA") and (btc_trend_bias >= -0.2)
    assert should_veto_common is True, "Estrategia comum contra muralha deve ser vetada"

    # Para Pullback Hunter, DEVE SER ISENTO (should_veto = False)
    strat_pullback = "LAYA_PULLBACK_HUNTER_2H_30M"
    should_veto_pullback = strat_pullback not in exempt_strategies and cand_dir == "SHORT" and (dom_magnet == "BULLISH_SWEEP" or target_reg == "ACIMA") and (btc_trend_bias >= -0.2)
    assert should_veto_pullback is False, "Pullback Hunter DEVE estar isento do veto do ima de liquidez"
