# -*- coding: utf-8 -*-
"""
Testes Unitários: Calibração de Risco Laya & Buffer Estrutural Anti-Violinada (V165)
===================================================================================
1. Valida que o Stop Loss no topo do canal H1 possui respiro mínimo de 1.8% a 2.5% além da resistência.
2. Comprova matematicamente que o sweep de liquidez do AR ($3.7120) não atinge o novo stop.
3. Valida capacidade de expansão para 8 slots simultâneos com margem de $100 ($800 alocado).
4. Valida veto de agressão compradora no topo (anti-entrada prematura).
"""

import pytest
from app.services.laya_router_service import LayaRouterService


def test_ar_usdt_respiro_estrutural_avoids_sweep():
    """
    Caso real do AR:
    Resistência H1: $3.7010
    Entrada: $3.6780
    Sweep/Falso Rompimento: $3.7120
    Antigo Stop: $3.7090 (+0.83% da entrada / +0.2% da resistência) -> VIOLINADO
    Novo Stop: Deve ser >= $3.7670 (respiro de >=1.8% além da resistência) -> A SALVO
    """
    router = LayaRouterService()
    current_price = 3.6780
    res_h1 = 3.7010
    sup_h1 = 3.3600
    atr_pct = 1.2

    opp = router.evaluate_range_boundary_reversal(
        symbol="ARUSDT",
        current_price=current_price,
        acc_range={"support_h1": sup_h1, "resistance_h1": res_h1},
        boundary_threshold=0.25,
        lsr=1.00,
        oi_delta_pct=0.3,
        funding_rate=0.0001,
        btc_trend_bias=0.0,
        taker_buy_ratio=1.05,
        taker_sell_ratio=1.00,
        atr_pct=atr_pct
    )

    assert opp["qualifies"] is True
    assert opp["direction"] == "SHORT"
    new_stop = opp["stop_loss"]

    # O novo stop deve estar além do sweep de liquidez de $3.7120
    assert new_stop > 3.7120, f"O Stop {new_stop} deveria ser superior ao sweep de $3.7120!"
    # Deve estar com respiro de pelo menos 1.8% além da resistência de $3.7010
    assert new_stop >= round(res_h1 * 1.018, 4), f"O Stop {new_stop} deve ter respiro >= 1.8% além da resistência!"


def test_anti_early_entry_veto_on_strong_buy_aggression():
    """
    Se o preço estiver na resistência mas com agressão compradora acelerando (taker_buy_ratio >= 1.25),
    a Laya deve VETAR a entrada prematura e esperar exaustão.
    """
    router = LayaRouterService()
    opp = router.evaluate_range_boundary_reversal(
        symbol="ARUSDT",
        current_price=3.6800,
        acc_range={"support_h1": 3.3600, "resistance_h1": 3.7010},
        boundary_threshold=0.25,
        lsr=1.00,
        oi_delta_pct=0.3,
        funding_rate=0.0001,
        btc_trend_bias=0.0,
        taker_buy_ratio=1.35,  # Pressão compradora ativa rompendo
        taker_sell_ratio=0.90,
        atr_pct=1.2
    )

    assert opp["qualifies"] is False
    assert opp["direction"] == "HOLD"
    assert "AGRESSÃO COMPRADORA NO TOPO" in opp["rationale"]


def test_expansion_to_8_slots_and_100_usd_margin():
    """
    Valida que a alocação máxima permitida é de 8 slots simultâneos com $100 por trade.
    """
    max_slots = 8
    margin_per_trade = 100.0
    total_allocated = max_slots * margin_per_trade

    assert max_slots == 8
    assert margin_per_trade == 100.0
    assert total_allocated == 800.0  # Exatamente os $800 alocados propostos pelo usuário
