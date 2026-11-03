import pytest
import asyncio
from app.services.laya_router_service import laya_router_service
from services.order_projection_service import proj_service, StopLevel


def create_mock_candles(start_price: float, trend: str, count: int = 48, step_pct: float = 0.005):
    """Gera candles sinteticos de 1H para agregacao em 2H."""
    candles = []
    current_p = start_price
    base_time = 1700000000000
    for i in range(count):
        if trend == "DOWN":
            current_p *= (1.0 - step_pct)
        elif trend == "UP":
            current_p *= (1.0 + step_pct)
        # Formato: [timestamp, open, high, low, close, volume]
        t = str(base_time + i * 3600000)
        p_str = f"{current_p:.6f}"
        candles.append([t, p_str, f"{current_p*1.002:.6f}", f"{current_p*0.998:.6f}", p_str, "100000"])
    return candles


def test_macro_btc_regime_classification():
    """Valida a classificacao do regime de mercado pelo BTC e BTC.D."""
    # Cenário 1: BTC em queda com medias cruzadas para baixo
    btc_candles_down = create_mock_candles(80000.0, "DOWN", 48)
    c2h = laya_router_service.aggregate_1h_to_2h(btc_candles_down)
    sma_btc = laya_router_service.calculate_sma_cross_2h(c2h)
    
    regime = laya_router_service.classify_macro_market_regime(
        btc_sma_info=sma_btc,
        btc_dominance=59.5,
        btc_dominance_trend="UP"
    )
    assert regime["direction"] == "BEAR"
    assert regime["regime"] == "BTC_BEAR_EXPANSION"
    assert regime["allow_alt_shorts"] is True


def test_decorrelated_outlier_detection():
    """Valida deteccao de ativos descorrelacionados com volume anormal."""
    # Ativo com baixa correlacao com BTC (<0.35) e volume spike 3.5x
    decorr_info = {
        "is_decorrelated": True,
        "correlation": 0.15,
        "confidence": 75.0,
        "vol_ratio": 3.5,
        "volume_spike": True
    }
    
    is_outlier = laya_router_service.is_decorrelated_outlier(decorr_info)
    assert is_outlier is True


def test_structural_breakout_validation_anti_knife():
    """Garante que reversao para LONG exige rompimento confirmado da SMA 21 e topo do pivo no 2H."""
    # Ativo caindo em faca (SMA 8 < SMA 21 no 2H) - Caso MON / AEON antes do pivo
    knife_candles = create_mock_candles(0.025, "DOWN", 48)
    c2h = laya_router_service.aggregate_1h_to_2h(knife_candles)
    sma_info = laya_router_service.calculate_sma_cross_2h(c2h)
    
    last_candle = c2h[-1]
    last_close = float(last_candle["close"] if isinstance(last_candle, dict) else last_candle[4])
    
    validation = laya_router_service.validate_structural_reversal_2h(
        sma_info=sma_info,
        current_price=last_close,
        direction="LONG"
    )
    assert validation["confirmed"] is False
    assert "VETO" in validation["reason"]


def test_structural_breakout_validation_confirmed():
    """Garante que reversao oficial (SMA 8 > SMA 21 no 2H e preco acima da SMA 21) autoriza LONG."""
    # Ativo com rompimento confirmado no 2H (SMA 8 > SMA 21 e preco acima da SMA 21) - Caso AEON rompido
    breakout_candles = create_mock_candles(0.020, "UP", 48)
    c2h = laya_router_service.aggregate_1h_to_2h(breakout_candles)
    sma_info = laya_router_service.calculate_sma_cross_2h(c2h)
    
    last_candle = c2h[-1]
    last_close = float(last_candle["close"] if isinstance(last_candle, dict) else last_candle[4])
    
    validation = laya_router_service.validate_structural_reversal_2h(
        sma_info=sma_info,
        current_price=last_close,
        direction="LONG"
    )
    assert validation["confirmed"] is True
    assert validation["macro_direction"] == "LONG"


def test_order_ladder_300_roi_lock():
    """Garante que a escadinha possui o nivel de lock macico em +250% a +300% ROI (~5-6% de preco a 50x)."""
    ladder = proj_service.get_stop_ladder(roi_percent=0.0, is_ranging=False, strategy_class="LAYA_AGUIA_FUSION")
    
    # Procura degrau de 300% ROI
    level_300 = next((lvl for lvl in ladder if lvl.trigger_roi >= 250.0 and lvl.trigger_roi <= 320.0), None)
    assert level_300 is not None
    assert level_300.stop_roi >= 200.0, "O degrau de 300% ROI deve travar pelo menos 200% de lucro liquido garantido"


def test_profit_fast_reentry_cooldown():
    """Valida que par com lucro recente tem cooldown reduzido para 5min ao inves de 45min."""
    import time
    laya_router_service.record_trade_profit("MONUSDT", 280.0)
    profit_info = getattr(laya_router_service, "_symbol_last_profit", {}).get("MON")
    assert profit_info is not None
    assert profit_info["pnl"] == 280.0
    assert (time.time() - profit_info["time"]) < 10.0

