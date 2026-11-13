# -*- coding: utf-8 -*-
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.laya_router_service import laya_router_service


def test_evaluate_intermediate_reversal_15m_is_permanently_extirpated():
    """
    [V215-EXTIRPACAO-15M-SUBORDINACAO-2H]
    Valida que o modulo LAYA_INTERMEDIATE_REVERSAL_15M foi permanentemente extirpado
    e retorna sumariamente qualifies=False para proteger 100% das operacoes
    sob a subordinacao macro hierarquica de 2H (SMA 8 x SMA 21) + 30M Pullback Hunter.
    """
    candles_15m = [[str(i * 900000), "0.060", "0.065", "0.059", "0.064", "5000"] for i in range(25)]
    res = laya_router_service.evaluate_intermediate_reversal_15m(
        symbol="ZAMAUSDT",
        current_price=0.064,
        candles_15m=candles_15m,
        c_range=20.0
    )
    assert res["qualifies"] is False
    assert res["direction"] == "HOLD"
    assert res["reason"] == "EXTIRPADO_SUBORDINACAO_2H_OBRIGATORIA"


def test_multi_setup_opportunity_blocks_15m_counter_trend():
    """
    Garante que operacoes em contratendencia macro de 2H sao sumariamente VETADAS
    pela subordinacao hierarquica, sem qualquer bypass legado de 15M.
    """
    candles_1h = []
    for i in range(24):
        open_p = 0.0800 - (i * 0.0008)
        close_p = open_p - 0.0007
        high_p = open_p + 0.0002
        low_p = close_p - 0.0002
        candles_1h.append([
            str(i * 3600000), str(open_p), str(high_p), str(low_p), str(close_p), "50000"
        ])

    candles_15m = [[str(i * 900000), "0.060", "0.065", "0.059", "0.064", "5000"] for i in range(25)]

    acc_range = {
        "support_h1": 0.0590,
        "resistance_h1": 0.0720,
        "is_consolidating": True,
        "range_pct": 22.0
    }

    res = laya_router_service.evaluate_multi_setup_opportunity(
        symbol="ZAMAUSDT",
        current_price=0.0635,
        acc_range=acc_range,
        candles_1h=candles_1h,
        candles_15m=candles_15m,
        c_exp=45.0,
        bot_ignition=False,
        btc_trend_bias=0.0,
        lsr=1.05
    )

    # Nao pode mais entrar em LONG contra a tendencia macro de queda do 2H
    if res.get("qualifies"):
        assert res.get("direction") != "LONG"
    else:
        assert res.get("qualifies") is False
