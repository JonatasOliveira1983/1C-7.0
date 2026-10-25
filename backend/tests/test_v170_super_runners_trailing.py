import pytest
import math
from services.order_projection_service import OrderProjectionService, ORDER_STOP_LADDER_LAYA_REVERSION

def test_laya_reversion_ladder_has_super_runners_tiers():
    """Valida que a escadinha da Laya inclui degraus institucionais até 1200%+."""
    triggers = [lvl.trigger_roi for lvl in ORDER_STOP_LADDER_LAYA_REVERSION]
    assert 300.0 in triggers   # ROCKET
    assert 500.0 in triggers   # CROWN
    assert 1000.0 in triggers  # HYPER
    assert 1200.0 in triggers  # APEX

def test_laya_super_trend_level_selection():
    """Valida que um trade da Laya com 295% ou 500% de ROI escala os degraus da Escadinha."""
    proj = OrderProjectionService()
    
    # Com 295% de ROI (como na ordem do par ORDER), deve selecionar pelo menos WAVE (200% -> stop 150%)
    lvl_295 = proj.get_active_level(295.0, strategy_class="LAYA_DVWAP_REVERSION")
    assert lvl_295 is not None
    assert lvl_295.stop_roi >= 150.0
    
    # Com 350% de ROI, deve selecionar ROCKET (300% -> stop 220%)
    lvl_350 = proj.get_active_level(350.0, strategy_class="LAYA_DVWAP_REVERSION")
    assert lvl_350 is not None
    assert lvl_350.name == "ROCKET"
    assert lvl_350.stop_roi == 220.0

    # Com 1050% de ROI, deve selecionar HYPER (1000% -> stop 800%)
    lvl_1050 = proj.get_active_level(1050.0, strategy_class="LAYA_DVWAP_REVERSION")
    assert lvl_1050 is not None
    assert lvl_1050.name == "HYPER"
    assert lvl_1050.stop_roi == 800.0
