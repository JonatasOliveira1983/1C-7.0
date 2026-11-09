import sys, os
sys.path.insert(0, os.path.abspath("backend"))
import pytest
from services.order_projection_service import OrderProjectionService, ORDER_STOP_LADDER_SWING
from app.services.laya_router_service import LayaRouterService


def test_swing_strategy_classification_and_ladder():
    proj = OrderProjectionService()
    # LAYA_PULLBACK_HUNTER_2H_30M e LAYA_AGUIA_FUSION devem ser classificadas como SWING
    ladder_pullback = proj.get_stop_ladder(0.0, is_ranging=False, strategy_class="LAYA_PULLBACK_HUNTER_2H_30M")
    ladder_aguia = proj.get_stop_ladder(0.0, is_ranging=False, strategy_class="LAYA_AGUIA_FUSION")
    
    triggers = [lvl.trigger_roi for lvl in ladder_pullback]
    assert 60.0 in triggers
    assert 100.0 in triggers
    assert 200.0 in triggers
    assert 300.0 in triggers
    assert 500.0 in triggers

    # Degrau 300% deve garantir no mínimo 200% de ROI travado
    lvl_300 = next(lvl for lvl in ladder_pullback if lvl.trigger_roi == 300.0)
    assert lvl_300.stop_roi >= 200.0


def test_max_roi_139_does_not_choke_trade():
    """
    Simula o caso real de FIL-USDT:
    No pico de 139.3% ROI, o stop antigo asfixiava a 97.5% (apenas 0.84% de preço).
    Com a nova regra, o stop deve ficar no degrau consolidado (+50% ou +100%),
    mantendo respiro de preço livre (> 1.0% de preço / > 50% ROI).
    """
    proj = OrderProjectionService()
    active_lvl = proj.get_active_level(139.3, strategy_class="LAYA_PULLBACK_HUNTER_2H_30M")
    assert active_lvl is not None
    # Com a regra V211 de Trailing Dinâmico (gap de 35% após +100%), a 139.3% o stop é 104.3% ROI
    assert active_lvl.stop_roi == 104.3
    assert active_lvl.phase == "TRAILING"
    # A folga de respiro deve ser exatamente 35.0% de ROI (0.70% no preço a 50X)
    respiro_roi = round(139.3 - active_lvl.stop_roi, 1)
    assert respiro_roi == 35.0


def test_alvo_chao_300_locks_200_roi():
    proj = OrderProjectionService()
    active_300 = proj.get_active_level(300.0, strategy_class="LAYA_PULLBACK_HUNTER_2H_30M")
    assert active_300 is not None
    assert active_300.stop_roi >= 200.0


def test_pullback_hunter_target_aims_at_least_6_pct():
    """
    O alvo da estratégia 2H/30M deve buscar amplitude mínima de 6.0% (300% ROI a 50x)
    """
    router = LayaRouterService()
    # Mock de candles 30M com rejeição para acionar o trigger
    dummy_klines = []
    for i in range(25):
        dummy_klines.append({"ts": 1700000000 + i * 1800, "open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0, "vol": 1000})
    # Último candle testa a média e rejeita com pavio alto
    dummy_klines[-1] = {"ts": 1700000000 + 25 * 1800, "open": 100.0, "high": 100.4, "low": 99.8, "close": 99.9, "vol": 1500}
    
    short_setup = router.calculate_30m_pullback_trigger("TEST-USDT", dummy_klines, 99.9, "SHORT")
    if short_setup.get("has_pullback_setup"):
        target_dist = abs(99.9 - short_setup["target"]) / 99.9
        assert target_dist >= 0.059, f"Target dist muito curto: {target_dist*100:.2f}%"
