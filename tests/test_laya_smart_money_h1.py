"""
TDD Tests for Laya Smart Money H1 Breakout Engine (Encryptos Methodology).
- Range detection in 1H timeframe (Accumulation / Consolidation).
- Breakout entry confirmation via LSR x Open Interest Delta.
- Asymmetric Stop Loss positioned precisely at the exit boundary to neutralize fakeouts.
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.laya_router_service import LayaRouterService

@pytest.fixture
def laya_service():
    service = LayaRouterService()
    return service

def test_h1_accumulation_detection():
    service = LayaRouterService()
    # 15 velas de 1h simulando consolidação entre 100.0 e 105.0
    candles_h1 = [
        {"high": 104.5, "low": 100.2, "open": 101.0, "close": 103.0},
        {"high": 105.0, "low": 101.0, "open": 103.0, "close": 102.5},
        {"high": 104.8, "low": 100.5, "open": 102.5, "close": 104.0},
        {"high": 103.9, "low": 100.0, "open": 104.0, "close": 101.5},
        {"high": 105.0, "low": 100.8, "open": 101.5, "close": 104.8},
    ]
    acc = service.calculate_h1_accumulation_range(candles_h1)
    assert acc["is_consolidating"] is True
    assert acc["resistance_h1"] == 105.0
    assert acc["support_h1"] == 100.0

def test_h1_accumulation_breakout_long_with_favorable_oi_and_lsr():
    service = LayaRouterService()
    candles_h1 = [
        {"high": 105.0, "low": 100.0, "open": 102.0, "close": 104.0}
    ]
    acc = {"is_consolidating": True, "resistance_h1": 105.0, "support_h1": 100.0}
    
    # Preço atual rompeu a resistência H1 com força (105.30)
    current_price = 105.30
    lsr = 1.10         # Sardinhas neutras/baixas (institucional comprando)
    oi_delta_pct = 0.8 # OI subindo forte (+0.8%)
    
    eval_res = service.evaluate_h1_breakout(
        symbol="SOLUSDT",
        current_price=current_price,
        acc_range=acc,
        lsr=lsr,
        oi_delta_pct=oi_delta_pct
    )
    
    assert eval_res["qualifies"] is True
    assert eval_res["direction"] == "LONG"
    assert eval_res["score"] >= 90
    # Stop loss posicionado na borda de saída (105.0) para proteger contra falso rompimento
    assert eval_res["stop_loss"] <= 105.05
    assert eval_res["stop_loss"] >= 104.70

def test_h1_accumulation_breakdown_short_with_favorable_oi_and_lsr():
    service = LayaRouterService()
    acc = {"is_consolidating": True, "resistance_h1": 105.0, "support_h1": 100.0}
    
    # Preço atual perdeu o suporte H1 com força (99.60)
    current_price = 99.60
    lsr = 1.35         # Sardinhas compradas tentando segurar faca caindo (combustível para short)
    oi_delta_pct = 0.6 # OI subindo (+0.6% de novas posições vendidas)
    
    eval_res = service.evaluate_h1_breakout(
        symbol="SOLUSDT",
        current_price=current_price,
        acc_range=acc,
        lsr=lsr,
        oi_delta_pct=oi_delta_pct
    )
    
    assert eval_res["qualifies"] is True
    assert eval_res["direction"] == "SHORT"
    assert eval_res["score"] >= 90
    # Stop loss posicionado na borda de saída (100.0)
    assert eval_res["stop_loss"] >= 99.90
    assert eval_res["stop_loss"] <= 100.30

def test_h1_fakeout_veto_due_to_retail_euphoria():
    service = LayaRouterService()
    acc = {"is_consolidating": True, "resistance_h1": 105.0, "support_h1": 100.0}
    
    # Preço rompeu (105.40), mas LSR está eufórico (1.55 = armadilha de compra das baleias)
    current_price = 105.40
    lsr = 1.55
    oi_delta_pct = 0.5
    
    eval_res = service.evaluate_h1_breakout(
        symbol="SOLUSDT",
        current_price=current_price,
        acc_range=acc,
        lsr=lsr,
        oi_delta_pct=oi_delta_pct
    )
    
    assert eval_res["qualifies"] is False
    assert "BULL_TRAP" in eval_res["rationale"] or "VETO" in eval_res["rationale"]

def test_inside_accumulation_range_holds_without_trading():
    service = LayaRouterService()
    acc = {"is_consolidating": True, "resistance_h1": 105.0, "support_h1": 100.0}
    
    # Preço no miolo da consolidação (102.50)
    current_price = 102.50
    lsr = 1.10
    oi_delta_pct = 0.2
    
    eval_res = service.evaluate_h1_breakout(
        symbol="SOLUSDT",
        current_price=current_price,
        acc_range=acc,
        lsr=lsr,
        oi_delta_pct=oi_delta_pct
    )
    
    assert eval_res["qualifies"] is False
    assert eval_res["direction"] == "HOLD"

def test_h1_accumulation_detection_from_okx_raw_candles():
    service = LayaRouterService()
    # OKX retorna listas: [ts, o, h, l, c, vol, volCcy]
    raw_okx_candles = [
        ["1710000000", "101.0", "104.5", "100.2", "103.0", "1000", "100000"],
        ["1710003600", "103.0", "105.0", "101.0", "102.5", "1200", "120000"],
        ["1710007200", "102.5", "104.8", "100.5", "104.0", "900", "90000"],
        ["1710010800", "104.0", "103.9", "100.0", "101.5", "850", "85000"],
        ["1710014400", "101.5", "105.0", "100.8", "104.8", "1100", "110000"],
    ]
    acc = service.calculate_h1_accumulation_range(raw_okx_candles)
    assert acc["is_consolidating"] is True
    assert acc["resistance_h1"] == 105.0
    assert acc["support_h1"] == 100.0

