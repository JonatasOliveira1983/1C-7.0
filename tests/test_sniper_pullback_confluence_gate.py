import sys, os
sys.path.insert(0, os.path.abspath("backend"))
import pytest
from app.services.laya_router_service import LayaRouterService


def test_sniper_vetoes_entry_in_the_vacuum_below_sma8():
    """
    Caso LINK ($10.4810): Preço no vácuo abaixo da SMA 8 ($10.58).
    A Camada 1 deve vetar sumariamente a entrada porque o preço não alcançou a Linha Branca.
    """
    router = LayaRouterService()
    # Mock de klines onde SMA8 está em ~10.58 e o preço atual está em 10.4810 (quase 1% abaixo da média)
    klines_30m = [
        {"open": 10.60, "high": 10.62, "low": 10.55, "close": 10.58},
        {"open": 10.58, "high": 10.60, "low": 10.54, "close": 10.57},
        {"open": 10.57, "high": 10.59, "low": 10.50, "close": 10.55},
        {"open": 10.55, "high": 10.58, "low": 10.45, "close": 10.50},
        {"open": 10.50, "high": 10.52, "low": 10.20, "close": 10.25}, # Dump
        {"open": 10.25, "high": 10.48, "low": 10.22, "close": 10.48}, # Repique no meio do caminho
    ]
    res = router.calculate_30m_pullback_trigger(
        symbol="LINK",
        klines_30m=klines_30m,
        current_price=10.4810,
        macro_direction="SHORT",
        lsr=1.10,
        btc_dominance=58.5,
        btc_trend_bias=-0.5
    )
    assert res["has_pullback_setup"] is False
    assert "VETO_AGUARDANDO_TOQUE_SMA8" in res["reason"] or "VETO" in res["reason"]


def test_sniper_vetoes_entry_against_strong_bullish_expansion_candle():
    """
    Não vender contra vela verde de corpo longo sem pavio superior relevante.
    """
    router = LayaRouterService()
    # Preço tocou a SMA8 (10.58) mas em candle de alta pura sem rejeição (fechando na máxima)
    klines_30m = [
        {"open": 10.60, "high": 10.62, "low": 10.55, "close": 10.58},
        {"open": 10.58, "high": 10.60, "low": 10.54, "close": 10.57},
        {"open": 10.57, "high": 10.59, "low": 10.50, "close": 10.55},
        {"open": 10.55, "high": 10.58, "low": 10.45, "close": 10.50},
        {"open": 10.50, "high": 10.52, "low": 10.20, "close": 10.25},
        {"open": 10.25, "high": 10.58, "low": 10.25, "close": 10.579}, # Vela verde esticada fechando na máxima
    ]
    res = router.calculate_30m_pullback_trigger(
        symbol="LINK",
        klines_30m=klines_30m,
        current_price=10.58,
        macro_direction="SHORT",
        lsr=1.10,
        btc_dominance=58.5,
        btc_trend_bias=-0.5
    )
    assert res["has_pullback_setup"] is False
    assert "VETO_CANDLE_FORCA_COMPRADORA" in res["reason"] or "VETO" in res["reason"]


def test_sniper_fires_when_touched_sma8_with_rejection_wick_and_confluences():
    """
    Preço tocou a SMA 8 (10.58), deixou pavio superior de rejeição >= 25%,
    e o Stop Loss foi ancorado com folga acima da SMA 21 (10.70).
    """
    router = LayaRouterService()
    # Closes médios de SMA8 ~ 10.58, SMA21 ~ 10.70
    klines_30m = [
        {"open": 10.72, "high": 10.75, "low": 10.70, "close": 10.71},
        {"open": 10.71, "high": 10.73, "low": 10.68, "close": 10.69},
        {"open": 10.69, "high": 10.70, "low": 10.65, "close": 10.66},
        {"open": 10.66, "high": 10.68, "low": 10.60, "close": 10.62},
        {"open": 10.62, "high": 10.64, "low": 10.52, "close": 10.54},
        {"open": 10.54, "high": 10.56, "low": 10.40, "close": 10.45},
        {"open": 10.45, "high": 10.48, "low": 10.35, "close": 10.38},
        # Vela atual: Repicou até 10.60 (tocou SMA8), sofreu forte rejeição e recuou para 10.54 com pavio de 40%
        {"open": 10.48, "high": 10.60, "low": 10.46, "close": 10.52},
    ]
    res = router.calculate_30m_pullback_trigger(
        symbol="LINK",
        klines_30m=klines_30m,
        current_price=10.54,
        macro_direction="SHORT",
        lsr=1.15,
        btc_dominance=58.5,
        btc_trend_bias=-0.5,
        bot_ignition=True
    )
    assert res["has_pullback_setup"] is True
    assert res["stop_loss"] > 10.60, "Stop Loss deve ficar acima da máxima do repique e da SMA21"
    assert "SNIPER" in res["reason"] or "REJEICAO" in res["reason"]


def test_sniper_anchors_stop_above_2h_sma21_when_provided():
    """
    [UNIFIED A + B]: Quando sma8_2h e sma21_2h são fornecidas (ex: BCH com sma21_2h = 247.64),
    o Stop Loss estrutural deve ficar estritamente ACIMA da SMA 21 do 2H (ex: > 248.00),
    respeitando a blindagem macro do 2H.
    """
    router = LayaRouterService()
    klines_30m = [
        {"open": 245.0, "high": 245.5, "low": 243.0, "close": 244.0},
        {"open": 244.0, "high": 244.5, "low": 242.0, "close": 243.0},
        {"open": 243.0, "high": 243.5, "low": 241.0, "close": 241.5},
        {"open": 241.5, "high": 242.0, "low": 240.5, "close": 241.0},
        {"open": 241.0, "high": 242.0, "low": 240.0, "close": 241.2},
        {"open": 241.2, "high": 243.0, "low": 241.0, "close": 242.8},
        {"open": 242.8, "high": 243.5, "low": 242.0, "close": 243.0}, # Tocou na SMA8 do 2H (243.32) com pavio
    ]
    res = router.calculate_30m_pullback_trigger(
        symbol="BCH",
        klines_30m=klines_30m,
        current_price=243.0,
        macro_direction="SHORT",
        lsr=3.10,
        btc_dominance=60.0,
        btc_trend_bias=-0.3,
        bot_ignition=True,
        sma8_2h=243.32,
        sma21_2h=247.64
    )
    assert res["has_pullback_setup"] is True
    assert res["stop_loss"] >= 247.64, "Stop Loss DEVE ficar acima da SMA 21 do 2H (247.64)"
    assert res["stop_loss"] > 248.00, "Stop Loss deve ter folga institucional acima da SMA 21 do 2H"

