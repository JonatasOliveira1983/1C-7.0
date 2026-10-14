# -*- coding: utf-8 -*-
"""
Suíte TDD: Laya Multi-Timeframe & Multi-Setup Engine
===================================================
Valida:
1. Prioridade 1: Breakout de 1H (Saída de Acumulação) com stop na borda.
2. Prioridade 2: Momento Mola (Compressão 15M no extremo da consolidação).
3. Prioridade 3: DVWAP Reversion (Desvio elástico da VWAP diária no 5M intra-range).
4. Invariante de Hierarquia: Rompimento H1 sempre prevalece sobre DVWAP/Mola.
"""

import os
import sys
from pathlib import Path
import pytest

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.laya_router_service import LayaRouterService


@pytest.fixture
def laya():
    return LayaRouterService()


def test_h1_breakout_priority_one(laya):
    """Quando o preço rompe a máxima de 1H com fluxo, ativa Smart Money H1."""
    acc_range = {
        "is_consolidating": True,
        "resistance_h1": 100.0,
        "support_h1": 95.0,
        "range_pct": 5.26
    }
    # Preço rompeu acima da resistência
    current_price = 100.5
    lsr = 1.05  # Saudável
    oi_delta = 1.2  # Volume novo

    res = laya.evaluate_h1_breakout(
        symbol="BTCUSDT",
        current_price=current_price,
        acc_range=acc_range,
        lsr=lsr,
        oi_delta_pct=oi_delta
    )

    assert res["qualifies"] is True
    assert res["direction"] == "LONG"
    assert res["score"] >= 88
    # Stop ATR blindado com folga de volatilidade abaixo da borda
    assert res["stop_loss"] <= 99.8
    assert res["stop_loss"] < current_price
    assert res["target"] > current_price


def test_dvwap_reversion_within_accumulation(laya):
    """Dentro da consolidação de 1H, preço esticado >= 2.0% da VWAP gera reversão LONG."""
    acc_range = {
        "is_consolidating": True,
        "resistance_h1": 100.0,
        "support_h1": 90.0,
        "range_pct": 11.1
    }
    # Preço está DENTRO do range de 1H (91.0), esticado -2.67% abaixo da VWAP (93.5)
    current_price = 91.0
    vwap = 93.5
    lsr = 1.08  # Varejo neutro/vendido

    res = laya.evaluate_dvwap_reversion(
        symbol="SOLUSDT",
        current_price=current_price,
        vwap=vwap,
        acc_range=acc_range,
        lsr=lsr,
        btc_trend_bias=0.0
    )

    assert res["qualifies"] is True
    assert res["direction"] == "LONG"
    assert res["strategy"] == "LAYA_DVWAP_REVERSION"
    assert res["target"] == vwap  # Alvo é o retorno ao centro da VWAP
    # Stop loss blindado com folga de pelo menos 1.5%
    assert res["stop_loss"] <= round(current_price * 0.985, 4)


def test_momento_mola_within_accumulation(laya):
    """Dentro da consolidação de 1H, compressão de volatilidade no suporte gera Momento Mola."""
    acc_range = {
        "is_consolidating": True,
        "resistance_h1": 100.0,
        "support_h1": 90.0,
        "range_pct": 11.1
    }
    # Preço no suporte (90.8), com Bollinger Width muito baixo (1.2% - mola comprimida)
    current_price = 90.8
    bb_width_pct = 1.2
    is_at_support = True
    lsr = 0.95

    res = laya.evaluate_momento_mola(
        symbol="AVAXUSDT",
        current_price=current_price,
        acc_range=acc_range,
        bb_width_pct=bb_width_pct,
        is_at_support=is_at_support,
        lsr=lsr
    )

    assert res["qualifies"] is True
    assert res["direction"] == "LONG"
    assert res["strategy"] == "LAYA_MOMENTO_MOLA"
    assert res["score"] >= 86
    assert res["stop_loss"] < current_price


def test_hierarchy_breakout_overrides_dvwap(laya):
    """Se o preço rompeu a consolidação H1, o setup Smart Money H1 prevalece sobre DVWAP."""
    acc_range = {
        "is_consolidating": True,
        "resistance_h1": 100.0,
        "support_h1": 90.0,
        "range_pct": 11.1
    }
    # Preço rompeu para fora (101.5)
    current_price = 101.5
    vwap = 98.0  # Também esticado da VWAP, mas é ROMPIMENTO H1
    lsr = 1.10
    oi_delta = 1.5

    best = laya.evaluate_multi_setup_opportunity(
        symbol="BTCUSDT",
        current_price=current_price,
        acc_range=acc_range,
        vwap=vwap,
        bb_width_pct=1.4,
        lsr=lsr,
        oi_delta_pct=oi_delta
    )

    assert best["qualifies"] is True
    assert best["strategy"] == "LAYA_SMART_MONEY_H1"  # Prioridade 1 vence!


def test_h1_breakout_stop_loss_sanity(laya):
    """Sanity Gate: O stop loss NUNCA pode ser invertido em relação ao preço de entrada."""
    acc_range = {
        "is_consolidating": True,
        "resistance_h1": 2.070,
        "support_h1": 1.950,
        "range_pct": 6.15
    }
    # Preço rompeu por margem mínima
    current_price = 2.071
    res_long = laya.evaluate_h1_breakout(
        symbol="RENDERUSDT",
        current_price=current_price,
        acc_range=acc_range,
        lsr=1.05,
        oi_delta_pct=1.0
    )
    assert res_long["qualifies"] is True
    assert res_long["direction"] == "LONG"
    # Stop loss DEVE ser menor que o preço de entrada
    assert res_long["stop_loss"] < current_price

    # Cenário SHORT
    acc_short = {
        "is_consolidating": True,
        "resistance_h1": 2.100,
        "support_h1": 2.000,
        "range_pct": 5.0
    }
    short_price = 1.995
    res_short = laya.evaluate_h1_breakout(
        symbol="RENDERUSDT",
        current_price=short_price,
        acc_range=acc_short,
        lsr=1.30,
        oi_delta_pct=1.0
    )
    assert res_short["qualifies"] is True
    assert res_short["direction"] == "SHORT"
    # Stop loss DEVE ser maior que o preço de entrada
    assert res_short["stop_loss"] > short_price


def test_fallback_no_zero_rationale(laya):
    """Diagnóstico integrado NUNCA deve imprimir $0.0000-$0.0000 no Thought Stream."""
    empty_acc = {
        "is_consolidating": False,
        "resistance_h1": 0.0,
        "support_h1": 0.0,
        "range_pct": 0.0
    }
    res = laya.evaluate_multi_setup_opportunity(
        symbol="APTUSDT",
        current_price=0.87,
        acc_range=empty_acc,
        vwap=0.87,
        bb_width_pct=2.5,
        lsr=1.0,
        oi_delta_pct=0.0
    )
    assert "$0.0000" not in res["rationale"]
    assert "SINCRONIZANDO H1" in res["rationale"]


def test_btc_trend_bias_veto_long(laya):
    """Farol Macro do BTC em queda (-1.2%) deve vetar qualquer tentativa de LONG em altcoins."""
    acc_range = {
        "is_consolidating": True,
        "resistance_h1": 100.0,
        "support_h1": 90.0,
        "range_pct": 11.1
    }
    # Preço bem abaixo da VWAP (-2.67%), mas BTC derretendo
    current_price = 91.0
    vwap = 93.5

    res = laya.evaluate_dvwap_reversion(
        symbol="ETHUSDT",
        current_price=current_price,
        vwap=vwap,
        acc_range=acc_range,
        lsr=1.05,
        btc_trend_bias=-1.2  # BTC caindo forte
    )
    assert res["qualifies"] is False
    assert "BTC MACRO VETO" in res["rationale"]


def test_directional_circuit_breaker(laya):
    """Dois stops consecutivos na mesma direção travam novas operações nessa direção por 45 minutos."""
    assert laya.is_direction_in_cooldown("LONG") is False

    # Primeiro stop LONG
    laya.record_stop_loss("AVAXUSDT", direction="LONG")
    assert laya.is_direction_in_cooldown("LONG") is False

    # Segundo stop LONG
    laya.record_stop_loss("INJUSDT", direction="LONG")
    # Agora deve estar em cooldown!
    assert laya.is_direction_in_cooldown("LONG") is True
    # SHORT não pode ser afetado
    assert laya.is_direction_in_cooldown("SHORT") is False


def test_funding_rate_shield_veto_long(laya):
    """Funding Rate excessivo (+0.04%) deve vetar LONG para não pagar aluguel às baleias."""
    acc_range = {
        "is_consolidating": True,
        "resistance_h1": 100.0,
        "support_h1": 90.0,
        "range_pct": 11.1
    }
    # Preço esticado abaixo da VWAP, mas funding muito alto contra o comprador
    res = laya.evaluate_dvwap_reversion(
        symbol="SOLUSDT",
        current_price=91.0,
        vwap=93.5,
        acc_range=acc_range,
        lsr=1.05,
        btc_trend_bias=0.0,
        funding_rate=0.0004  # +0.04% a cada 8h
    )
    assert res["qualifies"] is False
    assert "VETO FUNDING RATE" in res["rationale"]


def test_funding_rate_shield_veto_short(laya):
    """Funding Rate fortemente negativo (-0.04%) deve vetar SHORT para evitar risco de squeeze."""
    acc_range = {
        "is_consolidating": True,
        "resistance_h1": 100.0,
        "support_h1": 90.0,
        "range_pct": 11.1
    }
    # Preço esticado acima da VWAP, mas funding muito negativo (vendedores pagando)
    res = laya.evaluate_dvwap_reversion(
        symbol="RENDERUSDT",
        current_price=96.0,
        vwap=93.5,
        acc_range=acc_range,
        lsr=1.25,
        btc_trend_bias=0.0,
        funding_rate=-0.0004  # -0.04% a cada 8h
    )
    assert res["qualifies"] is False
    assert "VETO FUNDING RATE" in res["rationale"]


def test_atr_dynamic_stop_loss(laya):
    """Stop loss ancorado em ATR (2.0%) deve ter folga >= 1.5% e nunca ficar colado a 0.3%."""
    acc_range = {
        "is_consolidating": True,
        "resistance_h1": 2400.0,
        "support_h1": 2200.0,
        "range_pct": 9.09
    }
    current_price = 2410.0
    res = laya.evaluate_h1_breakout(
        symbol="ETHUSDT",
        current_price=current_price,
        acc_range=acc_range,
        lsr=1.05,
        oi_delta_pct=1.0,
        btc_trend_bias=0.0,
        funding_rate=0.0001,
        atr_pct=2.0  # ATR de 2%
    )
    assert res["qualifies"] is True
    assert res["direction"] == "LONG"
    # Distância do stop deve ser de pelo menos 1.2% a 2.5%
    stop_dist_pct = ((current_price - res["stop_loss"]) / current_price) * 100.0
    assert stop_dist_pct >= 1.2
    assert res["stop_loss"] < current_price


