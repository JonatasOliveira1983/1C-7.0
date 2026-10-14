# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path
import pytest

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.order_projection_service import order_projection_service, StopLevel


def test_laya_mean_reversion_ladder_routing():
    """Garante que a estratégia LAYA_MEAN_REVERSION recebe a escadinha calibrada para R:R positivo."""
    ladder = order_projection_service.get_stop_ladder(
        roi_percent=0.0,
        is_ranging=True,
        strategy_class="LAYA_MEAN_REVERSION"
    )
    
    assert len(ladder) >= 4
    # Nível 1 dispara em +10.0% ROI para evitar asfixia por spread e travar +2.0%
    lvl1 = ladder[0]
    assert lvl1.trigger_roi == 10.0, f"Trigger esperado 10.0: {lvl1.trigger_roi}"
    assert lvl1.stop_roi >= 2.0, f"Stop de proteção insuficiente: {lvl1.stop_roi}"
    
    # Nível 2 trava lucro substantivo em +18% ROI (stop +8%)
    lvl2 = ladder[1]
    assert lvl2.trigger_roi == 18.0
    assert lvl2.stop_roi >= 8.0


def test_laya_mean_reversion_active_level_at_12pct_roi():
    """Se o trade atingir +12.0% ROI, o stop DEVE subir imediatamente para lucro positivo (Risco Zero)."""
    ladder = order_projection_service.get_stop_ladder(
        roi_percent=12.0,
        is_ranging=True,
        strategy_class="LAYA_MEAN_REVERSION"
    )
    active = order_projection_service.get_active_level(
        roi_percent=12.0,
        ladder=ladder,
        is_ranging=True,
        strategy_class="LAYA_MEAN_REVERSION"
    )
    
    assert active is not None
    assert active.stop_roi >= 2.0, f"Stop para +12% ROI deveria ser >= 2.0%, obtido {active.stop_roi}"


def test_laya_mean_reversion_ladder_in_trending_environment():
    """Mesmo que o ADX geral esteja em tendência, o setup de mean reversion deve usar a escadinha calibrada."""
    ladder = order_projection_service.get_stop_ladder(
        roi_percent=0.0,
        is_ranging=False, # ADX >= 25
        strategy_class="LAYA_MEAN_REVERSION"
    )
    
    lvl1 = ladder[0]
    assert lvl1.trigger_roi == 10.0, "LAYA_MEAN_REVERSION não deve cair na escadinha TRENDING normal (14% trigger)"
