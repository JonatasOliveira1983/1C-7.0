import sys, os
sys.path.insert(0, os.path.abspath("backend"))
import pytest
from services.order_projection_service import OrderProjectionService


def test_swing_dynamic_trailing_gap_50_above_100():
    """
    Alternativa A: Gap Elástico de Respiro Técnico (50.0% de ROI / 1.0% de Preço a 50X)
    - < 60% ROI: Respiro técnico estrutural 2H.
    - >= 60% ROI: Breakeven Soberano (+30.0% ROI líquido / +$300).
    - >= 100% ROI: Trailing Dinâmico com gap de 50% de ROI (1.0% de preço a 50X).
      * Atingiu +100% ROI -> Trava +50% (+$500 garantidos).
      * Atingiu +150% ROI -> Trava +100% (+$1.000 garantidos no cofre, 1.0% de respiro).
      * Atingiu +200% ROI -> Trava +150% (+$1.500 garantidos).
    - >= 300% ROI: Alvo Chão garantindo no mínimo 200% ROI (+$2.000) e surfe macro 4H.
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

    # 3. A 100%: Trailing Dinâmico aciona e trava 50% ROI (100 - 50)
    lvl_100 = proj.get_active_level(100.0, strategy_class=strat)
    assert lvl_100 is not None
    assert lvl_100.stop_roi == 50.0
    assert lvl_100.phase == "TRAILING"

    # 4. A 150%: Trava 100% ROI líquido (+$1.000 garantidos com 1.0% de respiro para buscar 300%)
    lvl_150 = proj.get_active_level(150.0, strategy_class=strat)
    assert lvl_150 is not None
    assert lvl_150.stop_roi == 100.0
    assert lvl_150.phase == "TRAILING"
    respiro_150 = round(150.0 - lvl_150.stop_roi, 1)
    assert respiro_150 == 50.0  # 1.0% de preço a 50X

    # 5. A 200%: Trava 150% ROI líquido (+$1.500 garantidos)
    lvl_200 = proj.get_active_level(200.0, strategy_class=strat)
    assert lvl_200 is not None
    assert lvl_200.stop_roi == 150.0
    assert lvl_200.phase == "TRAILING"

    # 6. A 300% (Alvo Chão): Garante pelo menos 200% ROI
    lvl_300 = proj.get_active_level(300.0, strategy_class=strat)
    assert lvl_300 is not None
    assert lvl_300.stop_roi >= 200.0
