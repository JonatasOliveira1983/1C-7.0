"""
Testes TDD V191 - Protocolo Sniper de Suporte/Resistência Macro, S/R Flip e Stop Estrutural
Valida que LAYA_AGUIA_FUSION proíbe compras no topo do canal / vácuo e exige repique no suporte.
"""
import pytest
from app.services.laya_router_service import laya_router_service

def _generate_synthetic_candles_1h(base_price=0.18, count=24, trend="BULL"):
    candles = []
    current = base_price
    for i in range(count):
        if trend == "BULL":
            open_p = current
            close_p = open_p * 1.003
            high_p = close_p * 1.002
            low_p = open_p * 0.998
            current = close_p
        else:
            open_p = current
            close_p = open_p * 0.997
            high_p = open_p * 1.002
            low_p = close_p * 0.998
            current = close_p
        candles.append([1700000000 + i * 3600, open_p, high_p, low_p, close_p, 100000.0])
    return candles

def _generate_synthetic_candles_15m(support=0.1790, current=0.1802, count=30):
    candles = []
    p = support
    for i in range(count - 1):
        candles.append([1700000000 + i * 900, p, p * 1.002, p * 0.998, p * 1.001, 50000.0])
        p *= 1.0005
    # Última vela testa o suporte com repique
    candles.append([1700000000 + (count - 1) * 900, support * 1.001, current * 1.002, support * 0.999, current, 80000.0])
    return candles

def test_veto_topo_estirado_vacuo_sem_reteste():
    """Garante que compra no topo do canal (c_range >= 55%) sem reteste de suporte é VETADA."""
    candles_1h = _generate_synthetic_candles_1h(base_price=0.170, count=24, trend="BULL")
    current_price = 0.1830  # Esticado perto do topo
    acc_range = {
        "is_consolidating": True,
        "support_h1": 0.1780,
        "resistance_h1": 0.1840,
        "range_pct": 3.37
    }
    # c_range = (0.1830 - 0.1780) / (0.1840 - 0.1780) = 83.3% (Topo do canal!)
    
    res = laya_router_service.evaluate_aguia_encryptos_fusion(
        symbol="ENA-USDT-SWAP",
        current_price=current_price,
        candles_1h=candles_1h,
        bot_ignition=True,
        c_exp=75.0,
        btc_trend_bias=0.1,
        acc_range=acc_range,
        c_range=83.3
    )
    
    assert res["qualifies"] is False, "Não deveria qualificar compra em 83.3% do canal (topo esticado)"
    assert "TOPO" in res.get("reason", "").upper() or "VÁCUO" in res.get("reason", "").upper() or "VACUO" in res.get("reason", "").upper()

def test_aprovacao_repique_no_suporte_com_stop_estrutural():
    """Garante que compra no repique de suporte (c_range <= 40%) é APROVADA com stop estrutural abaixo do suporte."""
    candles_1h = _generate_synthetic_candles_1h(base_price=0.172, count=24, trend="BULL")
    support_h1 = 0.1795
    resistance_h1 = 0.1945
    current_price = 0.1805  # Próximo ao suporte (c_range = ~6.6%)
    
    acc_range = {
        "is_consolidating": True,
        "support_h1": support_h1,
        "resistance_h1": resistance_h1,
        "range_pct": 8.35
    }
    c_range_val = ((current_price - support_h1) / (resistance_h1 - support_h1)) * 100.0
    candles_15m = _generate_synthetic_candles_15m(support=support_h1, current=current_price)
    
    res = laya_router_service.evaluate_aguia_encryptos_fusion(
        symbol="ENA-USDT-SWAP",
        current_price=current_price,
        candles_1h=candles_1h,
        bot_ignition=True,
        c_exp=75.0,
        btc_trend_bias=0.1,
        acc_range=acc_range,
        c_range=c_range_val,
        candles_15m=candles_15m
    )
    
    assert res["qualifies"] is True, f"Deveria qualificar compra no suporte: {res.get('reason')}"
    assert res["strategy"] == "LAYA_AGUIA_FUSION"
    assert res["direction"] == "LONG"
    # Stop loss estrutural deve estar ancorado logo abaixo do suporte H1
    assert res["stop_loss"] < support_h1, f"Stop loss ({res['stop_loss']}) deve ficar abaixo do suporte H1 ({support_h1})"
    # Distância do stop loss deve ser curta e estrutural (menor que 1.5%)
    assert res["stop_dist"] <= 0.015
    # Alvo deve mirar a resistência macro
    assert res["target"] > current_price
    assert res["target"] <= resistance_h1 * 1.01

def test_aprovacao_reteste_15m_media():
    """Garante que preço fazendo reteste colado na SMA 8 de 15M (distância <= 0.6%) qualifica."""
    candles_1h = _generate_synthetic_candles_1h(base_price=0.175, count=24, trend="BULL")
    support_h1 = 0.1700
    resistance_h1 = 0.1900
    current_price = 0.1802  # Meio do canal (c_range = 51%)
    acc_range = {
        "is_consolidating": True,
        "support_h1": support_h1,
        "resistance_h1": resistance_h1,
        "range_pct": 11.7
    }
    # Velas 15M com SMA 8 muito próxima de 0.1802
    candles_15m = []
    for i in range(25):
        candles_15m.append([1700000000 + i * 900, 0.1800, 0.1805, 0.1798, 0.1802, 50000.0])
        
    res = laya_router_service.evaluate_aguia_encryptos_fusion(
        symbol="ENA-USDT-SWAP",
        current_price=current_price,
        candles_1h=candles_1h,
        bot_ignition=True,
        c_exp=75.0,
        btc_trend_bias=0.1,
        acc_range=acc_range,
        c_range=51.0,
        candles_15m=candles_15m
    )
    assert res["qualifies"] is True, f"Deveria qualificar reteste na média 15M: {res.get('reason')}"
    assert res["strategy"] == "LAYA_AGUIA_FUSION"

def test_veto_fundo_estirado_vacuo_short():
    """Garante que venda no fundo do canal (c_range <= 45%) sem reteste de resistência é VETADA."""
    candles_1h = _generate_synthetic_candles_1h(base_price=0.180, count=24, trend="BEAR")
    current_price = 0.1710  # Fundo do canal
    acc_range = {
        "is_consolidating": True,
        "support_h1": 0.1700,
        "resistance_h1": 0.1850,
        "range_pct": 8.8
    }
    # c_range = (0.1710 - 0.1700) / (0.1850 - 0.1700) = 6.6% (Fundo do canal!)
    
    res = laya_router_service.evaluate_aguia_encryptos_fusion(
        symbol="ENA-USDT-SWAP",
        current_price=current_price,
        candles_1h=candles_1h,
        bot_ignition=True,
        c_exp=75.0,
        btc_trend_bias=-0.1,
        acc_range=acc_range,
        c_range=6.6
    )
    assert res["qualifies"] is False, "Não deveria vender no fundo de 6.6% do canal"
    assert "FUNDO" in res.get("reason", "").upper()

