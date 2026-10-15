"""
Tests for Laya Sovereign Institutional Engine (Encryptos Whale Framework)
- BTC Specialist & Lead-Lag (Spot x Futures)
- Bitcoin Dominance (BTC.D) Altcoin Climate
- Canonical 10 Titans Whitelist & OKX Dossier
- 2-Hour Quarantine After Stop Loss
- Structural Stop Distance (min 2.8%)
"""
import pytest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch

from app.services.laya_btc_specialist_service import LayaBTCSpecialistService
from app.services.okx_universe_service import okx_universe_service
from app.services.laya_router_service import laya_router_service


@pytest.mark.asyncio
async def test_btc_dominance_and_climate_matrix():
    service = LayaBTCSpecialistService()
    
    # Caso 1: BTC.D alta (62%), BTC caindo (-2.5%) -> ALTCOIN_BLOODBATH
    climate_bloodbath = service.classify_altcoin_climate(btc_dominance=62.0, btc_24h_change_pct=-2.5)
    assert climate_bloodbath["climate"] == "ALTCOIN_BLOODBATH"
    assert climate_bloodbath["altcoin_long_allowed"] is False
    assert climate_bloodbath["altcoin_short_allowed"] is True

    # Caso 2: BTC.D caindo (52%), BTC em alta (+3.0%) -> ALTCOIN_EXPANSION
    climate_expansion = service.classify_altcoin_climate(btc_dominance=52.0, btc_24h_change_pct=3.0)
    assert climate_expansion["climate"] == "ALTCOIN_EXPANSION"
    assert climate_expansion["altcoin_long_allowed"] is True
    assert climate_expansion["altcoin_short_allowed"] is False

    # Caso 3: BTC.D subindo forte (61%), BTC subindo forte (+4.0%) -> BTC_DRAINAGE (Vampiro)
    climate_drainage = service.classify_altcoin_climate(btc_dominance=61.0, btc_24h_change_pct=4.0)
    assert climate_drainage["climate"] == "BTC_DRAINAGE"
    assert climate_drainage["altcoin_long_allowed"] is False


@pytest.mark.asyncio
async def test_titans_30_altcoins_and_dossier():
    # Verifica universo dos Top 30 Altcoins com BTC estritamente excluído para trade
    titans = await okx_universe_service.get_tradable_universe(limit=30, exclude_btc=True)
    assert len(titans) == 30
    symbols = [t["symbol"] for t in titans]
    assert "BTC-USDT-SWAP" not in symbols, "BTC não pode estar na cesta de trades"
    assert "ETH-USDT-SWAP" in symbols
    assert "SOL-USDT-SWAP" in symbols
    assert "NEAR-USDT-SWAP" in symbols
    assert "ZK-USDT-SWAP" in symbols
    assert "XPL-USDT-SWAP" in symbols

    # Dossiê de Altcoin (SOL): 15x de alavancagem
    sol_dossier = await okx_universe_service.get_asset_dossier("SOL-USDT-SWAP")
    assert sol_dossier["symbol"] == "SOL-USDT-SWAP"
    assert sol_dossier["leverage"] == 15
    assert sol_dossier["ctVal"] > 0
    assert sol_dossier["tickSize"] > 0

    # Veto absoluto de abertura de ordens no BTC
    btc_eval = laya_router_service.evaluate_multi_setup_opportunity(
        symbol="BTC-USDT-SWAP",
        current_price=82000.0,
        acc_range={"resistance_h1": 81000.0, "support_h1": 80000.0}
    )
    assert btc_eval["qualifies"] is False
    assert btc_eval["direction"] == "HOLD"
    assert "ORÁCULO MACRO" in btc_eval["rationale"]


def test_quarantine_2h_after_stop_loss():
    test_symbol = "NEAR-USDT-SWAP"
    clean_sym = "NEAR"

    # Antes do stop, não está em quarentena
    laya_router_service._symbol_cooldowns.pop(clean_sym, None)
    assert not laya_router_service.is_symbol_in_cooldown(clean_sym)

    # Registra Stop Loss com quarentena padrão de 7200 segundos (2 horas)
    laya_router_service.record_stop_loss(test_symbol, direction="LONG", cooldown_seconds=7200)

    # Deve estar sob quarentena
    assert laya_router_service.is_symbol_in_cooldown(clean_sym)
    expiry = laya_router_service._symbol_cooldowns.get(clean_sym)
    assert expiry is not None
    assert (expiry - time.time()) > 7100  # Pelo menos ~1h58m restantes


def test_structural_stop_loss_distance_minimum():
    # Avalia que evaluate_h1_breakout impõe pelo menos 2.8% de stop (não 1.2% ou 1.5%)
    acc_range = {
        "is_consolidating": True,
        "resistance_h1": 100.0,
        "support_h1": 95.0,
        "range_pct": 5.0
    }
    # Preço rompeu para 101.0 com volume e fluxo
    res = laya_router_service.evaluate_h1_breakout(
        symbol="SOLUSDT",
        current_price=101.0,
        acc_range=acc_range,
        lsr=1.05,
        oi_delta_pct=1.2,
        btc_trend_bias=0.2,
        funding_rate=0.0001,
        atr_pct=1.0  # ATR baixo propositalmente
    )

    assert res["qualifies"] is True
    assert res["direction"] == "LONG"
    # A distância do stop DEVE ser >= 2.8% (0.028) mesmo com ATR baixo de 1.0%
    assert res["stop_dist"] >= 0.028
    assert res["stop_loss"] <= 101.0 * (1.0 - 0.028)


def test_altcoin_climate_veto_in_multi_setup():
    acc_range = {
        "is_consolidating": True,
        "resistance_h1": 10.0,
        "support_h1": 9.0,
        "range_pct": 10.0
    }
    # Clima ALTCOIN_BLOODBATH: BTC.D alta, altcoin_long_allowed=False
    btc_intel_bloodbath = {
        "btc_dominance": 61.5,
        "altcoin_climate": "ALTCOIN_BLOODBATH",
        "altcoin_long_allowed": False,
        "altcoin_short_allowed": True
    }

    # Tentativa de LONG em rompimento de altcoin durante ALTCOIN_BLOODBATH
    eval_res = laya_router_service.evaluate_multi_setup_opportunity(
        symbol="NEARUSDT",
        current_price=10.2,  # Rompeu máxima H1
        acc_range=acc_range,
        vwap=9.5,
        bb_width_pct=2.5,
        lsr=1.05,
        oi_delta_pct=1.0,
        btc_trend_bias=-0.1,
        funding_rate=0.0001,
        atr_pct=2.0,
        btc_intel=btc_intel_bloodbath
    )

    # Deve ser vetado pelo clima macro do BTC.D!
    assert eval_res["qualifies"] is False
    assert eval_res["direction"] == "HOLD"
    assert "VETO BTC.D CLIMA" in eval_res["rationale"]
