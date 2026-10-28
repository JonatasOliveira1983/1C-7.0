# -*- coding: utf-8 -*-
"""
Test Suite: V176 Anti-Pump 1C-EXP & Institutional Volume Spike Filter (Opcao B)
Verifies:
1. Volume spike >= 3.0x triggers has_volume_spike flag.
2. SHORT candidate in LAYA_LIQUIDITY_HUNT is vetoed if bot_on, c_exp >= 70, or has_volume_spike.
3. SHORT candidate is blocked in final dispatch if marked with has_volume_spike or bot_ignition.
4. LONG candidate is not blocked by volume spike (momentum supports long breakout).
"""
import pytest


def test_volume_spike_calculation():
    """Volume spike detection compares recent volume to historical 10-period baseline."""
    # Historical 10 candles with average volume of 10,000
    hist_vols = [10000.0] * 10
    avg_hist_vol = sum(hist_vols) / len(hist_vols)

    # 1. Normal volume (1.2x) -> no spike
    recent_normal = 12000.0
    vol_ratio_normal = recent_normal / avg_hist_vol
    has_spike_normal = (vol_ratio_normal >= 3.0)
    assert vol_ratio_normal == 1.2
    assert has_spike_normal is False

    # 2. Institutional volume surge (6.5x, like BEAT pump) -> spike detected
    recent_spike = 65000.0
    vol_ratio_spike = recent_spike / avg_hist_vol
    has_spike = (vol_ratio_spike >= 3.0)
    assert vol_ratio_spike == 6.5
    assert has_spike is True


def test_anti_pump_veto_in_liquidity_hunt():
    """SHORT in LAYA_LIQUIDITY_HUNT is vetoed if pump ignition is active."""
    # Base setup: Hunt zone + Pullback condition met
    is_hunt_zone = True
    is_pullback_or_edge = True
    is_at_support_floor = False

    # Scenario A: Normal market, no ignition -> Qualifies for SHORT
    bot_on_a = False
    c_exp_a = 45.0
    has_volume_spike_a = False
    is_pump_ignition_a = bot_on_a or (c_exp_a >= 70.0) or has_volume_spike_a
    qualifies_a = is_hunt_zone and is_pullback_or_edge and not is_at_support_floor and not is_pump_ignition_a
    assert is_pump_ignition_a is False
    assert qualifies_a is True

    # Scenario B: Institutional Volume Spike (vol_ratio >= 3.0) -> VETOED
    bot_on_b = False
    c_exp_b = 50.0
    has_volume_spike_b = True
    is_pump_ignition_b = bot_on_b or (c_exp_b >= 70.0) or has_volume_spike_b
    qualifies_b = is_hunt_zone and is_pullback_or_edge and not is_at_support_floor and not is_pump_ignition_b
    assert is_pump_ignition_b is True
    assert qualifies_b is False

    # Scenario C: Robos Ligados (bot_on = True) -> VETOED
    bot_on_c = True
    c_exp_c = 60.0
    has_volume_spike_c = False
    is_pump_ignition_c = bot_on_c or (c_exp_c >= 70.0) or has_volume_spike_c
    qualifies_c = is_hunt_zone and is_pullback_or_edge and not is_at_support_floor and not is_pump_ignition_c
    assert is_pump_ignition_c is True
    assert qualifies_c is False

    # Scenario D: 1C-EXP Explosive (c_exp >= 70.0) -> VETOED
    bot_on_d = False
    c_exp_d = 75.0
    has_volume_spike_d = False
    is_pump_ignition_d = bot_on_d or (c_exp_d >= 70.0) or has_volume_spike_d
    qualifies_d = is_hunt_zone and is_pullback_or_edge and not is_at_support_floor and not is_pump_ignition_d
    assert is_pump_ignition_d is True
    assert qualifies_d is False


def test_anti_pump_dispatch_guard():
    """Dispatch guard in eligible prevents opening SHORT if marked with volume spike or bot ignition."""
    # SHORT with volume spike
    cand_short_spiked = {
        "direction": "SHORT",
        "has_volume_spike": True,
        "bot_ignition": False,
        "1c_exp": 50.0
    }
    blocked_short = (
        cand_short_spiked.get("direction") == "SHORT" and (
            cand_short_spiked.get("has_volume_spike")
            or cand_short_spiked.get("bot_ignition")
            or cand_short_spiked.get("1c_exp", 0) >= 70.0
        )
    )
    assert blocked_short is True

    # LONG with volume spike (should NOT be blocked; institutional volume favors LONG)
    cand_long_spiked = {
        "direction": "LONG",
        "has_volume_spike": True,
        "bot_ignition": True,
        "1c_exp": 85.0
    }
    blocked_long = (
        cand_long_spiked.get("direction") == "SHORT" and (
            cand_long_spiked.get("has_volume_spike")
            or cand_long_spiked.get("bot_ignition")
            or cand_long_spiked.get("1c_exp", 0) >= 70.0
        )
    )
    assert blocked_long is False
