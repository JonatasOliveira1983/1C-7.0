# -*- coding: utf-8 -*-
"""
Tests to guarantee get_slots() preserves live current_price and PnL percentage.
Prevents regression where current_price was forced to entry_price and pnl_percent to 0.0%.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from routes.trading import _map_sandbox_trade_to_slot, get_slots


def test_map_sandbox_trade_preserves_current_price_and_pnl():
    trade_mock = {
        "id": "test_trade_123",
        "symbol": "SEI-USDT-SWAP",
        "direction": "SHORT",
        "entry_price": 0.06192,
        "current_price": 0.06314,
        "stop_loss": 0.06370,
        "target": 0.05800,
        "current_roi": -29.55,
        "pnl_pct": -29.55,
        "status": "ACTIVE",
        "strategy": "LAYA_RANGE_REVERSAL",
        "leverage": 15,
        "entry_margin": 200.0,
        "opened_at": None,
    }

    slot = _map_sandbox_trade_to_slot(trade_mock, "SCALPING")
    assert slot["entry_price"] == 0.06192
    assert slot["current_price"] == 0.06314, "current_price não pode ser sobrescrito pelo entry_price!"
    assert slot["pnl_percent"] == -29.55, "pnl_percent não pode ser zerado para 0.0%!"
    assert slot["side"] == "Sell"
    assert slot["slot_type"] == "SCALPING"
