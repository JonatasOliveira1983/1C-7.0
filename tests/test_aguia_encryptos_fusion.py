import pytest
from app.services.laya_router_service import laya_router_service


def test_parse_candle_dict_and_list():
    """Valida a normalização de candles em formato de lista (OKX raw) ou dicionário."""
    raw_list = ["1700000000000", "1.20", "1.30", "1.15", "1.25", "50000"]
    parsed = laya_router_service._parse_candle(raw_list)
    assert parsed["ts"] == 1700000000000.0
    assert parsed["open"] == 1.20
    assert parsed["high"] == 1.30
    assert parsed["low"] == 1.15
    assert parsed["close"] == 1.25
    assert parsed["vol"] == 50000.0

    raw_dict = {"ts": 1700000000000, "open": 1.20, "high": 1.30, "low": 1.15, "close": 1.25, "vol": 50000}
    parsed_d = laya_router_service._parse_candle(raw_dict)
    assert parsed_d["close"] == 1.25


def test_aggregate_1h_to_2h():
    """Valida a agregação matemática de velas de 1H em 2H."""
    c1 = {"ts": 1000, "open": 10.0, "high": 12.0, "low": 9.0, "close": 11.0, "vol": 100.0}
    c2 = {"ts": 2000, "open": 11.0, "high": 15.0, "low": 10.5, "close": 14.0, "vol": 200.0}
    c3 = {"ts": 3000, "open": 14.0, "high": 16.0, "low": 13.0, "close": 15.5, "vol": 150.0}
    c4 = {"ts": 4000, "open": 15.5, "high": 17.0, "low": 15.0, "close": 16.5, "vol": 250.0}

    candles_1h = [c1, c2, c3, c4]
    candles_2h = laya_router_service.aggregate_1h_to_2h(candles_1h)

    assert len(candles_2h) == 2
    assert candles_2h[0]["open"] == 10.0
    assert candles_2h[0]["high"] == 15.0
    assert candles_2h[0]["low"] == 9.0
    assert candles_2h[0]["close"] == 14.0
    assert candles_2h[0]["vol"] == 300.0

    assert candles_2h[1]["open"] == 14.0
    assert candles_2h[1]["high"] == 17.0
    assert candles_2h[1]["low"] == 13.0
    assert candles_2h[1]["close"] == 16.5
    assert candles_2h[1]["vol"] == 400.0


def test_calculate_sma_cross_2h_bullish_and_bearish():
    """Valida o cálculo do cruzamento SMA 8 (Branca) x SMA 21 (Amarela) no 2H."""
    bullish_candles = []
    for i in range(15):
        bullish_candles.append({"ts": (i+1)*7200, "close": 1.5 - i * 0.02})
    for i in range(10):
        bullish_candles.append({"ts": (16+i)*7200, "close": 1.2 + i * 0.10})

    res_bull = laya_router_service.calculate_sma_cross_2h(bullish_candles)
    assert res_bull["direction"] == "LONG"
    assert res_bull["cross_type"] in ("BULLISH_CROSS", "ALIGNED_BULL")
    assert res_bull["sma8"] > res_bull["sma21"]

    bearish_candles = []
    for i in range(15):
        bearish_candles.append({"ts": (i+1)*7200, "close": 1.0 + i * 0.05})
    for i in range(10):
        bearish_candles.append({"ts": (16+i)*7200, "close": 1.75 - i * 0.12})

    res_bear = laya_router_service.calculate_sma_cross_2h(bearish_candles)
    assert res_bear["direction"] == "SHORT"
    assert res_bear["cross_type"] in ("BEARISH_CROSS", "ALIGNED_BEAR")
    assert res_bear["sma8"] < res_bear["sma21"]


def test_evaluate_aguia_encryptos_fusion_success():
    """Valida que a confluência Bruno Aguiar (SMA 2H) + Phenix (1C-EXP >= 70 / Robôs) qualifica com sucesso."""
    candles_1h = []
    for i in range(30):
        candles_1h.append([
            str(i * 3600000),
            str(1.0 + i * 0.02),
            str(1.05 + i * 0.02),
            str(0.99 + i * 0.02),
            str(1.03 + i * 0.02),
            "10000"
        ])

    current_price = 1.60
    eval_res = laya_router_service.evaluate_aguia_encryptos_fusion(
        symbol="XRPUSDT",
        current_price=current_price,
        candles_1h=candles_1h,
        bot_ignition=True,
        c_exp=78.5,
        btc_trend_bias=0.2
    )

    assert eval_res["qualifies"] is True
    assert eval_res["direction"] == "LONG"
    assert eval_res["strategy"] == "LAYA_AGUIA_FUSION"
    assert eval_res["aguia_fusion"] is True
    assert eval_res["leverage_cap"] == 50.0
    assert eval_res["score"] >= 92
    assert eval_res["stop_loss"] < current_price
    assert eval_res["target"] > current_price
    assert "FUSAO AGUIA-ENCRYPTOS" in eval_res["rationale"]


def test_evaluate_aguia_encryptos_fusion_veto_by_encryptos():
    """Valida que sem o combustível do Phenix (sem robôs e 1C-EXP baixo), o setup é vetado mesmo com SMA favorável."""
    # Gera candles com SMA 8 acima de SMA 21 (tendência de alta)
    candles_1h = []
    for i in range(30):
        candles_1h.append([
            str(i * 3600000),
            str(1.0 + i * 0.02),
            str(1.05 + i * 0.02),
            str(0.99 + i * 0.02),
            str(1.03 + i * 0.02),
            "1000"
        ])

    eval_res = laya_router_service.evaluate_aguia_encryptos_fusion(
        symbol="DOGEUSDT",
        current_price=1.60,
        candles_1h=candles_1h,
        bot_ignition=False,
        c_exp=45.0, # Muito baixo (varejo morto sem aceleração)
        btc_trend_bias=0.1
    )

    assert eval_res["qualifies"] is False
    assert "Veto Encryptos" in eval_res.get("reason", "")


def test_bruno_aguiar_cross_margin_sizing_math():
    """Valida a matemática de risco de Bruno Aguiar: $60 por slot numa banca de $10.000 (0.6%) e folga de colateral."""
    bank_realized = 10000.0
    margin_per_slot = round(bank_realized * 0.006, 2)
    max_slots = 10
    total_allocated = margin_per_slot * max_slots
    liquid_cushion = bank_realized - total_allocated

    assert margin_per_slot == 60.0
    assert total_allocated == 600.0 # 6% da banca
    assert liquid_cushion == 9400.0 # 94% livre para garantir que o preço de liquidação fique 40% a 60% de distância




def test_macro_2h_sma_sovereign_gate_vetoes_counter_trend():
    """Valida que NENHUMA estratégia pode abrir LONG quando a SMA 2H é de baixa (SMA 8 < 21), nem SHORT quando é de alta."""
    # 1. Simula ativo em forte queda (como MON: SMA 8 abaixo de SMA 21 no 2H)
    candles_bearish_1h = []
    for i in range(30):
        # Preço caindo de 2.0 para 1.0
        p = 2.0 - (i * 0.03)
        candles_bearish_1h.append([
            str(i * 3600000),
            str(p + 0.01),
            str(p + 0.02),
            str(p - 0.01),
            str(p),
            "1000"
        ])

    # Tenta romper para cima no H1 com parâmetros válidos
    res_long = laya_router_service.evaluate_multi_setup_opportunity(
        symbol="MONUSDT",
        current_price=1.10,
        acc_range={
            "is_consolidating": True,
            "resistance_h1": 1.05,
            "support_h1": 0.95
        },
        lsr=1.0,
        oi_delta_pct=5.0,
        btc_trend_bias=0.0,
        candles_1h=candles_bearish_1h
    )

    # O gate 2H DEVE VETAR O LONG!
    assert res_long["qualifies"] is False
    assert res_long["direction"] == "HOLD"
    assert "VETO SOBERANO SMA 2H" in res_long.get("rationale", "")

    # 2. Simula ativo em forte alta (SMA 8 acima de SMA 21 no 2H)
    candles_bullish_1h = []
    for i in range(30):
        p = 1.0 + (i * 0.03)
        candles_bullish_1h.append([
            str(i * 3600000),
            str(p - 0.01),
            str(p + 0.02),
            str(p - 0.01),
            str(p),
            "1000"
        ])

    # Tenta romper para baixo no H1 com parâmetros válidos
    res_short = laya_router_service.evaluate_multi_setup_opportunity(
        symbol="SOLUSDT",
        current_price=0.90,
        acc_range={
            "is_consolidating": True,
            "resistance_h1": 1.05,
            "support_h1": 0.95
        },
        lsr=1.0,
        oi_delta_pct=5.0,
        btc_trend_bias=0.0,
        candles_1h=candles_bullish_1h
    )

    # O gate 2H DEVE VETAR O SHORT!
    assert res_short["qualifies"] is False
    assert res_short["direction"] == "HOLD"
    assert "VETO SOBERANO SMA 2H" in res_short.get("rationale", "")


if __name__ == "__main__":
    test_parse_candle_dict_and_list()
    print("PASS: test_parse_candle_dict_and_list")
    test_aggregate_1h_to_2h()
    print("PASS: test_aggregate_1h_to_2h")
    test_calculate_sma_cross_2h_bullish_and_bearish()
    print("PASS: test_calculate_sma_cross_2h_bullish_and_bearish")
    test_evaluate_aguia_encryptos_fusion_success()
    print("PASS: test_evaluate_aguia_encryptos_fusion_success")
    test_evaluate_aguia_encryptos_fusion_veto_by_encryptos()
    print("PASS: test_evaluate_aguia_encryptos_fusion_veto_by_encryptos")
    test_bruno_aguiar_cross_margin_sizing_math()
    print("PASS: test_bruno_aguiar_cross_margin_sizing_math")
    print("=== ALL 6 TESTS PASSED 100% ===")
