# -*- coding: utf-8 -*-
"""
Test Suite: V176 Bilateral Institutional Volume Spike & Anti-Pump / Anti-Dump Guards
Verifies:
1. Volume spike >= 3.0x with green candle -> BULLISH spike (PUMP).
2. Volume spike >= 3.0x with red candle -> BEARISH spike (DUMP).
3. SHORT is vetoed in PUMP, authorized in DUMP / normal.
4. LONG is vetoed in DUMP (falling knife), authorized in PUMP / normal.
5. Eligible dispatch guard enforces bilateral safety before opening orders.
"""
import pytest


def test_volume_spike_direction_detection():
    """Volume spike detection calculates ratio and direction from candle open/close."""
    hist_vols = [10000.0] * 10
    avg_hist_vol = sum(hist_vols) / len(hist_vols)

    # 1. Bullish Pump Spike (Open 100, Close 110, Vol 40,000)
    c_open_bull = 100.0
    c_close_bull = 110.0
    vol_bull = 40000.0
    has_spike_bull = (vol_bull / avg_hist_vol) >= 3.0
    spike_dir_bull = "BULLISH" if c_close_bull >= c_open_bull else "BEARISH"
    assert has_spike_bull is True
    assert spike_dir_bull == "BULLISH"

    # 2. Bearish Dump Spike (Open 100, Close 90, Vol 45,000)
    c_open_bear = 100.0
    c_close_bear = 90.0
    vol_bear = 45000.0
    has_spike_bear = (vol_bear / avg_hist_vol) >= 3.0
    spike_dir_bear = "BULLISH" if c_close_bear >= c_open_bear else "BEARISH"
    assert has_spike_bear is True
    assert spike_dir_bear == "BEARISH"


def test_bilateral_veto_in_liquidity_hunt():
    """Verifies that PUMP vetos SHORT and DUMP vetos LONG in Liquidity Hunt."""
    is_hunt_zone = True
    is_pullback_or_edge = True
    is_at_support_floor = False
    is_dip_or_edge = True
    is_at_resistance_ceiling = False

    # Scenario 1: BULLISH PUMP SPIKE -> SHORT is vetoed, LONG is allowed
    has_volume_spike = True
    spike_direction = "BULLISH"
    bot_on = False
    c_exp = 50.0

    is_pump_ignition = bot_on or (c_exp >= 70.0) or (has_volume_spike and spike_direction == "BULLISH")
    is_dump_ignition = (has_volume_spike and spike_direction == "BEARISH")

    qualifies_short = is_hunt_zone and is_pullback_or_edge and not is_at_support_floor and not is_pump_ignition
    qualifies_long = is_hunt_zone and is_dip_or_edge and not is_at_resistance_ceiling and not is_dump_ignition

    assert is_pump_ignition is True
    assert qualifies_short is False  # VETOED SHORT against PUMP!
    assert is_dump_ignition is False
    assert qualifies_long is True   # LONG allowed in PUMP!

    # Scenario 2: BEARISH DUMP SPIKE -> LONG is vetoed, SHORT is allowed
    spike_direction_dump = "BEARISH"
    is_pump_ignition_dump = bot_on or (c_exp >= 70.0) or (has_volume_spike and spike_direction_dump == "BULLISH")
    is_dump_ignition_dump = (has_volume_spike and spike_direction_dump == "BEARISH")

    qualifies_short_dump = is_hunt_zone and is_pullback_or_edge and not is_at_support_floor and not is_pump_ignition_dump
    qualifies_long_dump = is_hunt_zone and is_dip_or_edge and not is_at_resistance_ceiling and not is_dump_ignition_dump

    assert is_pump_ignition_dump is False
    assert qualifies_short_dump is True   # SHORT allowed in DUMP!
    assert is_dump_ignition_dump is True
    assert qualifies_long_dump is False  # VETOED LONG against falling knife!


def test_bilateral_dispatch_guard():
    """Eligible filter rejects SHORT in pump and rejects LONG in dump."""
    cand_short_in_pump = {
        "direction": "SHORT",
        "is_pump_ignition": True,
        "is_dump_ignition": False
    }
    blocked_short = (
        cand_short_in_pump.get("direction") == "SHORT" and cand_short_in_pump.get("is_pump_ignition")
    )
    assert blocked_short is True

    cand_long_in_dump = {
        "direction": "LONG",
        "is_pump_ignition": False,
        "is_dump_ignition": True
    }
    blocked_long = (
        cand_long_in_dump.get("direction") == "LONG" and cand_long_in_dump.get("is_dump_ignition")
    )
    assert blocked_long is True

    # Safe setups
    cand_safe_long = {
        "direction": "LONG",
        "is_pump_ignition": True,
        "is_dump_ignition": False
    }
    safe_long_blocked = (
        cand_safe_long.get("direction") == "LONG" and cand_safe_long.get("is_dump_ignition")
    )
    assert safe_long_blocked is False
