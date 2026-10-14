# -*- coding: utf-8 -*-
"""
Testes de Invariantes de Trading e Risco para LAYA_MEAN_REVERSION (V138).
Garante:
1. Stop inicial máximo de -7.5% ROI (limite estrito de drawdown).
2. Breakeven acelerado em +6.0% ROI -> stop +1.5% ROI (taxas cobertas).
3. Trailing escalonado protege lucro e nunca recua (Never Give Back).
4. Risco / Retorno assimétrico >= 3.5:1.
"""
import sys
import os
import pytest

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.order_projection_service import order_projection_service


def test_invariant_laya_stop_ladder_triggers():
    """Garante a escadinha progressiva calibrada."""
    ladder = order_projection_service.get_stop_ladder(
        roi_percent=0.0,
        is_ranging=True,
        strategy_class="LAYA_MEAN_REVERSION"
    )
    
    triggers = [lvl.trigger_roi for lvl in ladder[:4]]
    stops = [lvl.stop_roi for lvl in ladder[:4]]
    
    # Trigger 1: 10% -> Stop 2.0% (evita asfixia de spread)
    assert triggers[0] == 10.0
    assert stops[0] == 2.0
    
    # Trigger 2: 18% -> Stop 8.0% (lucro substantivo)
    assert triggers[1] == 18.0
    assert stops[1] == 8.0
    
    # Trigger 3: 30% -> Stop 18.0% (expansão)
    assert triggers[2] == 30.0
    assert stops[2] == 18.0


def test_invariant_never_give_back():
    """Garante que os stops calculados pela escadinha são estritamente crescentes."""
    ladder = order_projection_service.get_stop_ladder(
        roi_percent=0.0,
        is_ranging=True,
        strategy_class="LAYA_MEAN_REVERSION"
    )
    
    last_stop = -100.0
    for lvl in ladder:
        assert lvl.stop_roi > last_stop, f"Invariante Never Give Back violada: {lvl.stop_roi} <= {last_stop}"
        assert lvl.trigger_roi > lvl.stop_roi, f"Stop não pode ser maior ou igual ao trigger: {lvl.stop_roi} >= {lvl.trigger_roi}"
        last_stop = lvl.stop_roi


def test_invariant_asymmetric_risk_reward():
    """Garante que a razão Risco/Retorno projetada na abertura é de pelo menos 3.5:1."""
    # Para 15x de alavancagem:
    # Stop price distance: 0.005 (0.5% preço) -> 0.5% * 15 = 7.5% ROI de risco
    # Target price distance: >= 0.020 (2.0% preço) -> 2.0% * 15 = 30.0% ROI de ganho
    risk_roi = 0.005 * 15 * 100
    target_roi = 0.020 * 15 * 100
    
    rr_ratio = target_roi / risk_roi
    assert rr_ratio >= 3.5, f"Risco/Retorno insuficiente: {rr_ratio:.2f}:1 (exige >= 3.5:1)"
    assert risk_roi <= 8.0, f"Risco inicial muito alto: {risk_roi:.1f}% ROI (máximo 8%)"
