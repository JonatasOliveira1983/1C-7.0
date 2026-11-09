import sys, os
sys.path.insert(0, os.path.abspath("backend"))
import pytest
from services.order_projection_service import OrderProjectionService


def test_swing_dynamic_trailing_gap_35_above_100():
    """
    Abordagem 2: Trailing Dinâmico Conectado ao Pico para Swing 2H / 30M.
    - < 60% ROI: Respiro técnico estrutural.
    - >= 60% ROI: Breakeven Soberano (+30.0% ROI).
    - >= 100% ROI: Trailing Dinâmico com gap de 35% de ROI (0.70% de preço a 50X).
    - >= 300% ROI: Alvo Chão garantindo no mínimo 200% ROI e surfe macro.
    """
    proj = OrderProjectionService()
    strat = "LAYA_PULLBACK_HUNTER_2H_30M"

    # 1. Antes de 60%: livre
    lvl_50 = proj.get_active_level(50.0, strategy_class=strat)
    assert lvl_50 is None

    # 2. A 60%: Breakeven Soberano trava 30% ROI líquido
    lvl_60 = proj.get_active_level(60.0, strategy_class=strat)
    assert lvl_60 is not None
    assert lvl_60.stop_roi == 30.0

    # 3. A 100%: Trailing Dinâmico aciona e trava 65% ROI (100 - 35)
    lvl_100 = proj.get_active_level(100.0, strategy_class=strat)
    assert lvl_100 is not None
    assert lvl_100.stop_roi == 65.0
    assert lvl_100.phase == "TRAILING"

    # 4. Caso real de LINK no pico de 151.9%: trava 116.9% ROI (em vez de sair a 50%)
    lvl_link = proj.get_active_level(151.9, strategy_class=strat)
    assert lvl_link is not None
    assert lvl_link.stop_roi == 116.9
    assert lvl_link.phase == "TRAILING"

    # 5. Caso real de UNI no pico de 161.4%: trava 126.4% ROI (em vez de 50%)
    lvl_uni = proj.get_active_level(161.4, strategy_class=strat)
    assert lvl_uni is not None
    assert lvl_uni.stop_roi == 126.4
    assert lvl_uni.phase == "TRAILING"

    # 6. A 300% (Alvo Chão): Garante pelo menos 200% ROI
    lvl_300 = proj.get_active_level(300.0, strategy_class=strat)
    assert lvl_300 is not None
    assert lvl_300.stop_roi >= 200.0
