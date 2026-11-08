import sys, os
sys.path.insert(0, os.path.abspath("backend"))
import pytest
from services.order_projection_service import OrderProjectionService
from app.services.laya_router_service import LayaRouterService


def test_breakeven_does_not_trigger_at_25_or_50_roi():
    """
    O Breakeven NÃO pode disparar com +25% ou +50% ROI.
    Só deve ser acionado a partir de +60.0% de ROI.
    """
    proj = OrderProjectionService()
    ladder = proj.get_stop_ladder(0.0, strategy_class="LAYA_PULLBACK_HUNTER_2H_30M")
    
    first_level = ladder[0]
    assert first_level.trigger_roi >= 60.0, f"Gatilho muito baixo: {first_level.trigger_roi}"
    assert 25.0 <= first_level.stop_roi <= 35.0, f"Stop travado fora da faixa de +25% a +35%: {first_level.stop_roi}"


def test_active_level_at_roi_pullback():
    proj = OrderProjectionService()
    # Em +35% de ROI (como bateu WLD e LINK), NÃO pode haver stop em breakeven
    lvl_35 = proj.get_active_level(35.0, strategy_class="LAYA_PULLBACK_HUNTER_2H_30M")
    assert lvl_35 is None, "A 35% de ROI a ordem deve continuar correndo livre sem stop antecipado"

    # Em +65% de ROI, deve estar no Breakeven travando no mínimo +25% a +35% de ROI
    lvl_65 = proj.get_active_level(65.0, strategy_class="LAYA_PULLBACK_HUNTER_2H_30M")
    assert lvl_65 is not None
    assert lvl_65.stop_roi >= 25.0


def test_zero_tolerance_altcoin_long_when_btc_not_bull():
    """
    Tolerância Zero para Compras de Altcoin sem Bitcoin em BULL.
    """
    router = LayaRouterService()
    dummy_15m = [
        {"ts": 1700000000 + i * 900, "open": 10.0, "high": 10.1, "low": 9.9, "close": 10.0, "vol": 1000}
        for i in range(25)
    ]
    
    # 1. Quando BTC é BEAR ou CHOP (bias <= 0), o 15M DEVE vetar LONG
    res = router.evaluate_intermediate_reversal_15m(
        symbol="ARB-USDT-SWAP",
        current_price=10.0,
        candles_15m=dummy_15m,
        c_range=20.0, # Em suporte
        btc_trend_bias=-0.2 # Não é BULL
    )
    if res.get("direction") == "LONG":
        assert not res.get("qualifies"), "LONG autorizado indevidamente pelo 15M com BTC sem alta confirmada!"
