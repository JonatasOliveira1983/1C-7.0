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
    # SMA8 estara em torno de 3.65 - 3.68
    # Preco atual desabou para 3.60 (esticado bem abaixo da media)
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
    # 10 candles de baixa, seguidos de um repique ate a SMA8 com rejeicao
    candles = _build_test_candles(base_price=3.80, trend="down", count=10)
    # Fecha o ultimo candle retestando a media com pavio superior
    last_candle = {
        "ts": 1700000000 + 11 * 1800,
        "open": 3.745,
        "high": 3.765,  # retestou na SMA8
        "low": 3.740,
        "close": 3.750, # fechou rejeitando com pavio superior
        "vol": 2500
    }
    candles.append(last_candle)
    
    # Preco atual em 3.750 (na zona da SMA8, rejeitando)
    res = laya_router_service.calculate_30m_pullback_trigger("NEAR", candles, 3.750, "SHORT")
    assert res["has_pullback_setup"] is True
    assert res["pullback_type"] == "RETEST_REJECTION_BEAR"
    assert "stop_loss" in res
    assert res["stop_loss"] > 3.750  # Stop Loss acima do repique


def test_veto_esticado_topo_long():
    """
    Garante que se o preco disparou e esta esticado no topo (>0.6% acima da SMA8),
    o setup de LONG e estritamente vetado (nao compra topo!).
    """
    candles = _build_test_candles(base_price=3.50, trend="up", count=15)
    # Preco disparou muito acima da media
    current_price = 3.65
    
    res = laya_router_service.calculate_30m_pullback_trigger("NEAR", candles, current_price, "LONG")
    assert res["has_pullback_setup"] is False
    assert "VETO_ESTICADO_TOPO" in res["reason"]
    assert res["pullback_type"] == "STRETCHED_OVERBOUGHT"
