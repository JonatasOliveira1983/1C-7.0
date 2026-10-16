import pytest
from app.services.laya_router_service import laya_router_service
from services.sandbox_service import sandbox_service
from services.order_projection_service import proj_service

def test_h1_breakout_short_distant_support_capped():
    """
    Testa o cenário SEI: rompimento de baixa com suporte anterior muito distante.
    O stop loss jamais deve ficar no suporte antigo (ex: 0.0706), e sim limitado
    estritamente a no máximo 1.2% de distância do preço de entrada (-18% ROI em 15x).
    """
    current_price = 0.06149
    acc_range = {
        "is_consolidating": True,
        "support_h1": 0.0702,  # Suporte anterior 14.8% acima do preço atual!
        "resistance_h1": 0.0750
    }
    atr_pct = 2.5
    lsr = 1.40
    oi_delta_pct = 1.0
    funding_rate = 0.0001
    btc_trend_bias = -0.2

    res = laya_router_service.evaluate_h1_breakout(
        symbol="SEI-USDT-SWAP",
        current_price=current_price,
        acc_range=acc_range,
        lsr=lsr,
        oi_delta_pct=oi_delta_pct,
        btc_trend_bias=btc_trend_bias,
        funding_rate=funding_rate,
        atr_pct=atr_pct
    )

    assert res["qualifies"] is True
    assert res["direction"] == "SHORT"
    stop_loss = res["stop_loss"]
    assert stop_loss > current_price
    
    # Distância percentual do stop não pode ultrapassar 1.2%
    stop_dist = (stop_loss - current_price) / current_price
    assert stop_dist <= 0.0125
    
    # Em 15x de alavancagem, o stop ROI não pode ser pior do que -18.75%
    roi = proj_service.calculate_roi(current_price, stop_loss, "SHORT", 15.0)
    assert roi >= -18.75
    assert roi <= -10.0


def test_h1_breakout_long_distant_resistance_capped():
    """
    Testa rompimento de alta com resistência muito distante.
    O stop loss deve ser cravado com teto de 1.2% no preço.
    """
    current_price = 100.0
    acc_range = {
        "is_consolidating": True,
        "support_h1": 75.0,
        "resistance_h1": 80.0  # Resistência antiga 20% abaixo!
    }
    atr_pct = 2.5
    lsr = 0.90
    oi_delta_pct = 1.2
    funding_rate = 0.0001
    btc_trend_bias = 0.1

    res = laya_router_service.evaluate_h1_breakout(
        symbol="ETH-USDT-SWAP",
        current_price=current_price,
        acc_range=acc_range,
        lsr=lsr,
        oi_delta_pct=oi_delta_pct,
        btc_trend_bias=btc_trend_bias,
        funding_rate=funding_rate,
        atr_pct=atr_pct
    )

    assert res["qualifies"] is True
    assert res["direction"] == "LONG"
    stop_loss = res["stop_loss"]
    assert stop_loss < current_price

    stop_dist = (current_price - stop_loss) / current_price
    assert stop_dist <= 0.0125

    roi = proj_service.calculate_roi(current_price, stop_loss, "LONG", 15.0)
    assert roi >= -18.75
    assert roi <= -10.0


def test_dvwap_reversion_stop_capping():
    """
    Testa reversão à VWAP com stop limitado a 1.2% de preço.
    """
    current_price = 50.0
    vwap = 48.0
    acc_range = {
        "is_consolidating": True,
        "support_h1": 45.0,
        "resistance_h1": 58.0  # Resistência distante
    }
    atr_pct = 1.5
    lsr = 1.30
    funding_rate = 0.0001
    btc_trend_bias = -0.1

    res = laya_router_service.evaluate_dvwap_reversion(
        symbol="SOL-USDT-SWAP",
        current_price=current_price,
        vwap=vwap,
        acc_range=acc_range,
        lsr=lsr,
        btc_trend_bias=btc_trend_bias,
        funding_rate=funding_rate,
        atr_pct=atr_pct
    )

    assert res["qualifies"] is True
    assert res["direction"] == "SHORT"
    stop_dist = (res["stop_loss"] - current_price) / current_price
    assert stop_dist <= 0.0125


@pytest.mark.asyncio
async def test_sandbox_adaptive_stop_limits():
    """
    Verifica se o cálculo de stop adaptativo do sandbox respeita o limite de -18% ROI.
    """
    meta = {"leverage": 15.0, "tickSize": 0.0001}
    # Forçar fallback fixo
    res = await sandbox_service._calculate_adaptive_stop(
        symbol="TEST-USDT-SWAP",
        entry_price=10.0,
        side="LONG",
        contract_meta=meta,
        is_ranging=False
    )

    # Fallback deve ser exatamente -15.0% ROI (1.0% de preço)
    assert -18.5 <= res["stop_roi"] <= -14.5
    assert res["stop_price"] < 10.0
