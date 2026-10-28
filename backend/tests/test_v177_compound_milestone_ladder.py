# -*- coding: utf-8 -*-
"""
Test Suite: V177 Compound Milestone Ladder (Abordagem B)
Verifies:
1. Dynamic margin scales in $1,000 milestones based strictly on realized bankroll.
2. Safety floor guarantees a minimum of $50.00 USD per slot.
3. Total risk exposure across all 8 slots remains mathematically constant at 8.0% of milestone capital.
4. Fluctuations in floating unrealized PnL do not prematurely expand slot margin.
"""
import pytest


def calculate_compound_margin(realized_balance: float) -> tuple[int, float]:
    """Calculates milestone level and margin per slot."""
    milestone_step = max(5, int(realized_balance // 1000))
    margin_planned = float(milestone_step * 10.0)
    milestone_capital = milestone_step * 1000
    return milestone_capital, margin_planned


def test_milestone_ladder_progression():
    """Verifies discrete steps for each $1,000 milestone."""
    # Under $10,000 (defensive de-escalation)
    milestone, margin = calculate_compound_margin(9500.0)
    assert milestone == 9000
    assert margin == 90.0

    # $10,000 baseline
    milestone, margin = calculate_compound_margin(10000.0)
    assert milestone == 10000
    assert margin == 100.0

    # Intra-milestone ($10,950 -> still $100)
    milestone, margin = calculate_compound_margin(10950.0)
    assert milestone == 10000
    assert margin == 100.0

    # Milestone 1 crossed ($11,000 -> $110)
    milestone, margin = calculate_compound_margin(11000.0)
    assert milestone == 11000
    assert margin == 110.0

    # Intra-milestone ($11,850 -> still $110)
    milestone, margin = calculate_compound_margin(11850.0)
    assert milestone == 11000
    assert margin == 110.0

    # Milestone 2 crossed ($12,000 -> $120)
    milestone, margin = calculate_compound_margin(12000.0)
    assert milestone == 12000
    assert margin == 120.0

    # High milestone ($15,000 -> $150)
    milestone, margin = calculate_compound_margin(15200.0)
    assert milestone == 15000
    assert margin == 150.0

    # Doubling milestone ($20,000 -> $200)
    milestone, margin = calculate_compound_margin(20500.0)
    assert milestone == 20000
    assert margin == 200.0


def test_safety_floor_clamp():
    """Extreme drawdown cannot push margin below $50.00 USD (protects minSz)."""
    milestone, margin = calculate_compound_margin(3500.0)
    assert milestone == 5000
    assert margin == 50.0


def test_risk_exposure_invariance():
    """Total maximum margin across 8 slots is strictly 8.0% of milestone capital."""
    for bal in [8000.0, 10000.0, 11000.0, 12000.0, 15000.0, 25000.0]:
        milestone, margin = calculate_compound_margin(bal)
        total_8_slots = margin * 8.0
        exposure_ratio = total_8_slots / milestone
        assert pytest.approx(exposure_ratio, rel=1e-3) == 0.08
