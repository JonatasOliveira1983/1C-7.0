import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.laya_router_service import laya_router_service


def test_evaluate_intermediate_reversal_15m_long_success():
    """
    Valida que quando um ativo atinge o suporte do canal (1C-Range <= 35%)
    e o timeframe de 15M faz a rejeição com volume e cruzamento de SMA 8 > SMA 21,
    o módulo LAYA_INTERMEDIATE_REVERSAL_15M qualifica com sucesso para LONG.
    """
    # Simula 25 candles de 15M: queda até candle 20, varredura no candle 21 e reversão com volume nos candles 22-24
    candles_15m = []
    base_price = 0.0700
    for i in range(20):
        # Queda gradual
        p = base_price - (i * 0.0005)
        candles_15m.append([
            str(i * 900000), str(p), str(p + 0.0002), str(p - 0.0003), str(p - 0.0001), "1000"
        ])
    
    # Candle 20: Fundo varrido com sombra inferior longa (sweep em 0.0594)
    candles_15m.append([
        "18900000", "0.0605", "0.0610", "0.0594", "0.0608", "5000"
    ])
    # Candle 21: Impulso com volume alto (rejeição confirmada)
    candles_15m.append([
        "19800000", "0.0608", "0.0620", "0.0606", "0.0618", "8000"
    ])
    # Candle 22: Rompimento do pivô de 15m (SMA 8 cruza SMA 21)
    candles_15m.append([
        "20700000", "0.0618", "0.0630", "0.0616", "0.0628", "9500"
    ])
    # Candle 23: Confirmação de alta
    candles_15m.append([
        "21600000", "0.0628", "0.0638", "0.0626", "0.0635", "7000"
    ])

    current_price = 0.0635
    eval_res = laya_router_service.evaluate_intermediate_reversal_15m(
        symbol="ZAMAUSDT",
        current_price=current_price,
        candles_15m=candles_15m,
        c_range=25.0, # Suporte extremo de canal
        lsr=1.05,
        btc_trend_bias=0.1
    )

    assert eval_res["qualifies"] is True
    assert eval_res["direction"] == "LONG"
    assert eval_res["strategy"] == "LAYA_INTERMEDIATE_REVERSAL_15M"
    assert eval_res["score"] >= 90
    assert eval_res["stop_loss"] < current_price
    assert eval_res["stop_loss"] <= 0.0595 # Stop ancorado no sweep
    assert eval_res["target"] > current_price
    assert eval_res["leverage_cap"] <= 25.0
    assert "REVERSAO INTERMEDIARIA 15M" in eval_res["rationale"]


def test_evaluate_intermediate_reversal_15m_blocks_middle_of_channel():
    """
    Garante que se o ativo não estiver em suporte/resistência (miolo do canal 50%),
    o módulo não autoriza a reversão antecipada para preservar o Win Rate.
    """
    candles_15m = [[str(i * 900000), "0.065", "0.066", "0.064", "0.065", "1000"] for i in range(25)]
    
    eval_res = laya_router_service.evaluate_intermediate_reversal_15m(
        symbol="ZAMAUSDT",
        current_price=0.065,
        candles_15m=candles_15m,
        c_range=50.0, # Miolo neutro
        lsr=1.0,
        btc_trend_bias=0.0
    )

    assert eval_res["qualifies"] is False
    assert "MIOLO" in eval_res.get("reason", "")


def test_evaluate_intermediate_reversal_15m_short_success():
    """
    Valida reversao short no topo do canal (c_range >= 65%) com sweep de liquidez e rejeicao no 15M.
    """
    candles_15m = []
    base_price = 0.0600
    for i in range(20):
        p = base_price + (i * 0.0005)
        candles_15m.append([
            str(i * 900000), str(p), str(p + 0.0003), str(p - 0.0002), str(p + 0.0001), "1000"
        ])
    
    # Candle 20: Topo varrido com sombra superior longa (sweep em 0.0715)
    candles_15m.append([
        "18900000", "0.0700", "0.0715", "0.0698", "0.0701", "6000"
    ])
    # Candle 21: Queda com volume alto (rejeicao confirmada)
    candles_15m.append([
        "19800000", "0.0701", "0.0702", "0.0688", "0.0690", "8500"
    ])
    # Candle 22: Rompimento de baixa no 15M
    candles_15m.append([
        "20700000", "0.0690", "0.0692", "0.0678", "0.0680", "9000"
    ])
    # Candle 23: Continuacao de queda
    candles_15m.append([
        "21600000", "0.0680", "0.0682", "0.0672", "0.0674", "7500"
    ])

    current_price = 0.0674
    eval_res = laya_router_service.evaluate_intermediate_reversal_15m(
        symbol="ZAMAUSDT",
        current_price=current_price,
        candles_15m=candles_15m,
        c_range=75.0, # Resistencia extrema de canal
        lsr=1.0,
        btc_trend_bias=-0.1
    )

    assert eval_res["qualifies"] is True
    assert eval_res["direction"] == "SHORT"
    assert eval_res["strategy"] == "LAYA_INTERMEDIATE_REVERSAL_15M"
    assert eval_res["score"] >= 90
    assert eval_res["stop_loss"] > current_price
    assert eval_res["stop_loss"] >= 0.0714
    assert eval_res["target"] < current_price
    assert eval_res["leverage_cap"] <= 25.0


def test_multi_setup_opportunity_allows_15m_reversal_despite_2h_macro_trend():
    """
    Valida que evaluate_multi_setup_opportunity autoriza a entrada de LAYA_INTERMEDIATE_REVERSAL_15M
    mesmo quando a tendencia macro do 2H ainda nao virou (SMA 8 < SMA 21 no 2H),
    evitando a perda de movimentos explosivos como o de +8% do ZAMA.
    """
    # 2H Macro em queda evidente (SMA 8 < SMA 21 no 2H)
    candles_1h = []
    for i in range(24):
        # Queda ao longo de 24 horas
        open_p = 0.0800 - (i * 0.0008)
        close_p = open_p - 0.0007
        high_p = open_p + 0.0002
        low_p = close_p - 0.0002
        candles_1h.append([
            str(i * 3600000), str(open_p), str(high_p), str(low_p), str(close_p), "50000"
        ])
    
    # 15M com reversao confirmada no fundo
    candles_15m = []
    base_price = 0.0700
    for i in range(20):
        p = base_price - (i * 0.0005)
        candles_15m.append([
            str(i * 900000), str(p), str(p + 0.0002), str(p - 0.0003), str(p - 0.0001), "1000"
        ])
    candles_15m.append(["18900000", "0.0605", "0.0610", "0.0594", "0.0608", "5000"])
    candles_15m.append(["19800000", "0.0608", "0.0620", "0.0606", "0.0618", "8000"])
    candles_15m.append(["20700000", "0.0618", "0.0630", "0.0616", "0.0628", "9500"])
    candles_15m.append(["21600000", "0.0628", "0.0638", "0.0626", "0.0635", "7000"])

    current_price = 0.0635
    acc_range = {
        "support_h1": 0.0590,
        "resistance_h1": 0.0720,
        "is_consolidating": True,
        "range_pct": 22.0
    }

    res = laya_router_service.evaluate_multi_setup_opportunity(
        symbol="ZAMAUSDT",
        current_price=current_price,
        acc_range=acc_range,
        candles_1h=candles_1h,
        candles_15m=candles_15m,
        c_exp=45.0,
        bot_ignition=False,
        btc_trend_bias=0.0,
        lsr=1.05
    )

    assert res["qualifies"] is True
    assert res["direction"] == "LONG"
    assert res["strategy"] == "LAYA_INTERMEDIATE_REVERSAL_15M"
    assert res["stop_loss"] <= 0.0595

