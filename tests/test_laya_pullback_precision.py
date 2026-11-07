import sys, os
sys.path.insert(0, os.path.abspath("backend"))
import pytest
from app.services.laya_router_service import laya_router_service


def _build_test_candles(base_price=3.70, trend="down", count=20):
    """Gera candles simulados de 30M."""
    candles = []
    curr = base_price
    for i in range(count):
        if trend == "down":
            open_p = curr
            close_p = curr - 0.005
            high_p = open_p + 0.002
            low_p = close_p - 0.002
            curr = close_p
        elif trend == "up":
            open_p = curr
            close_p = curr + 0.005
            high_p = close_p + 0.002
            low_p = open_p - 0.002
            curr = close_p
        candles.append({
            "ts": 1700000000 + i * 1800,
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "close": close_p,
            "vol": 1000
        })
    return candles


def test_veto_esticado_fundo_short():
    """
    Garante que se o preco desabou e esta esticado no fundo (>0.6% abaixo da SMA8),
    o setup de SHORT e estritamente vetado (nao vende fundo!).
    """
    candles = _build_test_candles(base_price=3.70, trend="down", count=15)
    current_price = 3.60
    
    res = laya_router_service.calculate_30m_pullback_trigger("NEAR", candles, current_price, "SHORT")
    assert res["has_pullback_setup"] is False
    assert "VETO_ESTICADO_FUNDO" in res["reason"]
    assert res["pullback_type"] == "STRETCHED_OVERSOLD"


def test_gatilho_repique_resistencia_short():
    """
    Garante que quando o preco sobe para retestar a SMA8/SMA21 e deixa pavio superior,
    o gatilho de SHORT e acionado no topo do repique com Stop Loss seguro acima da maxima.
    """
    candles = _build_test_candles(base_price=3.80, trend="down", count=10)
    last_candle = {
        "ts": 1700000000 + 11 * 1800,
        "open": 3.745,
        "high": 3.765,  # retestou na SMA8
        "low": 3.740,
        "close": 3.750, # fechou rejeitando com pavio superior
        "vol": 2500
    }
    candles.append(last_candle)
    
    res = laya_router_service.calculate_30m_pullback_trigger("NEAR", candles, 3.750, "SHORT")
    assert res["has_pullback_setup"] is True
    assert res["pullback_type"] == "RETEST_REJECTION_BEAR"
    assert "stop_loss" in res
    assert res["stop_loss"] > 3.750


def test_veto_esticado_topo_long():
    """
    Garante que se o preco disparou e esta esticado no topo (>0.6% acima da SMA8),
    o setup de LONG e estritamente vetado (nao compra topo!).
    """
    candles = _build_test_candles(base_price=3.50, trend="up", count=15)
    current_price = 3.65
    
    res = laya_router_service.calculate_30m_pullback_trigger("NEAR", candles, current_price, "LONG")
    assert res["has_pullback_setup"] is False
    assert "VETO_ESTICADO_TOPO" in res["reason"]
    assert res["pullback_type"] == "STRETCHED_OVERBOUGHT"


def test_evaluate_30m_tf_structure_veto_vela_verde():
    """
    Garante que se a vela 30M atual estiver em expansao de alta (verde)
    sem rejeicao superior clara, o SHORT e vetado (proibido vender vela verde subindo!).
    """
    raw_candles = [
        ["1700000000", "10.60", "10.75", "10.58", "10.70", "50000"],
        ["1700001800", "10.70", "10.85", "10.68", "10.83", "60000"],
        ["1700003600", "10.83", "10.96", "10.82", "10.95", "90000"]
    ]
    res = laya_router_service.evaluate_lower_tf_structure(raw_candles, "SHORT")
    assert res["is_safe"] is False
    assert ("VETO" in res["reason"])


def test_evaluate_30m_tf_structure_veto_volume_explosivo():
    """
    Garante que se o repique estiver subindo com volume explosivo (compradores agressivos),
    o SHORT e vetado ate o volume secar.
    """
    raw_candles = [
        ["1700000000", "10.60", "10.70", "10.58", "10.65", "20000"],
        ["1700001800", "10.65", "10.75", "10.62", "10.70", "25000"],
        ["1700003600", "10.70", "10.95", "10.69", "10.90", "150000"]
    ]
    res = laya_router_service.evaluate_lower_tf_structure(raw_candles, "SHORT")
    assert res["is_safe"] is False
    assert ("VETO" in res["reason"])


def test_stop_loss_must_be_above_sma21_resistance_short():
    """
    Garante que a resistencia real para calculo de Stop Loss no SHORT
    seja SEMPRE a maior media (max(sma8, sma21) = SMA21), nunca a menor.
    Evita a violinada na qual o stop ficava em 10.935 enquanto a SMA21 estava em 11.058.
    """
    candles = _build_test_candles(base_price=11.20, trend="down", count=25)
    last_candle = {
        "ts": 1700000000 + 26 * 1800,
        "open": 10.93,
        "high": 10.98,
        "low": 10.92,
        "close": 10.95,
        "vol": 1000
    }
    candles.append(last_candle)
    res = laya_router_service.calculate_30m_pullback_trigger("LINK", candles, 10.95, "SHORT")
    if res["has_pullback_setup"]:
        sma21 = res.get("sma21_30m", 0.0)
        assert res["stop_loss"] > sma21, f"Stop Loss ({res['stop_loss']}) deve ser maior que a SMA21 ({sma21})"


def test_classify_macro_market_regime_vetoes_alt_longs_in_bear():
    """
    Garante que o Farol Macro do Bitcoin no 2H bloqueia terminantemente
    qualquer tentativa de LONG em altcoins quando o BTC estiver em BEAR (SMA8 < SMA21).
    """
    btc_sma_bear = {
        "direction": "SHORT",
        "sma8": 75000.0,
        "sma21": 76500.0,
        "diff_pct": -2.0
    }
    macro = laya_router_service.classify_macro_market_regime(btc_sma_bear, btc_dominance=59.0)
    assert macro["allow_alt_longs"] is False
    assert macro["allow_alt_shorts"] is True
