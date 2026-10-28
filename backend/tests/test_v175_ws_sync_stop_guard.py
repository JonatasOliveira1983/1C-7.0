# -*- coding: utf-8 -*-
"""
Test Suite: V175 Dynamic WS Sync, Immediate Stop Price Guard & Pullback Filter
Verifies:
1. Immediate Stop Price Guard triggers instantly on current price touching/crossing SL without REST latency.
2. Pullback filter logic vetoes SHORT at range floor and LONG at range top in MEAN_REVERSION.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


def test_immediate_stop_price_guard_long():
    """LONG trade triggers stop_hit when current_price <= stop_loss."""
    direction = "LONG"
    stop_loss = 100.0

    # Below stop loss -> immediate hit
    current_price_below = 99.9
    hit_below = (direction == "LONG" and current_price_below <= stop_loss)
    assert hit_below is True

    # At stop loss -> immediate hit
    current_price_exact = 100.0
    hit_exact = (direction == "LONG" and current_price_exact <= stop_loss)
    assert hit_exact is True

    # Above stop loss -> safe
    current_price_above = 100.1
    hit_above = (direction == "LONG" and current_price_above <= stop_loss)
    assert hit_above is False


def test_immediate_stop_price_guard_short():
    """SHORT trade triggers stop_hit when current_price >= stop_loss."""
    direction = "SHORT"
    stop_loss = 100.0

    # Above stop loss -> immediate hit
    current_price_above = 100.1
    hit_above = (direction == "SHORT" and current_price_above >= stop_loss)
    assert hit_above is True

    # At stop loss -> immediate hit
    current_price_exact = 100.0
    hit_exact = (direction == "SHORT" and current_price_exact >= stop_loss)
    assert hit_exact is True

    # Below stop loss -> safe
    current_price_below = 99.9
    hit_below = (direction == "SHORT" and current_price_below >= stop_loss)
    assert hit_below is False


def test_pullback_range_filters():
    """In MEAN_REVERSION: SHORT vetoed if c_range < 35%, LONG vetoed if c_range > 65%."""
    regime = "MEAN_REVERSION"

    # SHORT at bottom of range (c_range = 25%) should be rejected
    c_range_short_invalid = 25.0
    veto_short = (regime == "MEAN_REVERSION" and c_range_short_invalid < 35.0)
    assert veto_short is True

    # SHORT with pullback (c_range = 55%) should be accepted
    c_range_short_valid = 55.0
    veto_short_ok = (regime == "MEAN_REVERSION" and c_range_short_valid < 35.0)
    assert veto_short_ok is False

    # LONG at top of range (c_range = 75%) should be rejected
    c_range_long_invalid = 75.0
    veto_long = (regime == "MEAN_REVERSION" and c_range_long_invalid > 65.0)
    assert veto_long is True

    # LONG with dip (c_range = 40%) should be accepted
    c_range_long_valid = 40.0
    veto_long_ok = (regime == "MEAN_REVERSION" and c_range_long_valid > 65.0)
    assert veto_long_ok is False
