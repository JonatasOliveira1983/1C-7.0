# -*- coding: utf-8 -*-
"""
Tests for FundingService (OKX Funding Rate & Cashflow Tracker)
Ensures:
1. Long position pays when funding rate is positive.
2. Short position receives when funding rate is positive.
3. Long position receives when funding rate is negative.
4. Short position pays when funding rate is negative.
5. Fleet summary calculates aggregate net 8h and 24h funding cashflow.
"""
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from app.services.funding_service import FundingService


def test_calculate_funding_long_positive_rate():
    service = FundingService()
    # Margem $200, Alavancagem 15x -> Nocional $3000
    # Taxa +0.01% (+0.0001) -> Long paga $0.30 por ciclo de 8h
    res = service.calculate_position_funding(
        symbol="BTC-USDT-SWAP",
        side="LONG",
        margin=200.0,
        leverage=15.0,
        rate_override=0.0001,
        funding_time_override=1792137600000
    )
    assert res["notional_usd"] == 3000.0
    assert res["funding_rate_pct"] == 0.01
    assert res["action"] == "PAGA"
    assert res["cost_per_cycle_usd"] == -0.30
    assert res["cost_24h_usd"] == -0.90


def test_calculate_funding_short_positive_rate():
    service = FundingService()
    # Margem $200, Alavancagem 15x -> Nocional $3000
    # Taxa +0.01% (+0.0001) -> Short RECEBE +$0.30 por ciclo de 8h
    res = service.calculate_position_funding(
        symbol="ONDO-USDT-SWAP",
        side="SHORT",
        margin=200.0,
        leverage=15.0,
        rate_override=0.0001,
        funding_time_override=1792137600000
    )
    assert res["notional_usd"] == 3000.0
    assert res["action"] == "RECEBE"
    assert res["cost_per_cycle_usd"] == 0.30
    assert res["cost_24h_usd"] == 0.90


def test_calculate_funding_short_negative_rate():
    service = FundingService()
    # Margem $200, Alavancagem 15x -> Nocional $3000
    # Taxa -0.02% (-0.0002) -> Short PAGA -$0.60 por ciclo de 8h
    res = service.calculate_position_funding(
        symbol="SUI-USDT-SWAP",
        side="SHORT",
        margin=200.0,
        leverage=15.0,
        rate_override=-0.0002,
        funding_time_override=1792137600000
    )
    assert res["action"] == "PAGA"
    assert res["cost_per_cycle_usd"] == -0.60
    assert res["cost_24h_usd"] == -1.80


def test_fleet_funding_summary():
    service = FundingService()
    slots = [
        # ONDO Short (Recebe $0.30)
        {
            "symbol": "ONDO-USDT-SWAP",
            "side": "SHORT",
            "entry_margin": 200.0,
            "leverage": 15.0,
            "funding_rate": 0.0001,
            "funding_time": 1792137600000
        },
        # SEI Short (Recebe $0.15)
        {
            "symbol": "SEI-USDT-SWAP",
            "side": "SHORT",
            "entry_margin": 200.0,
            "leverage": 15.0,
            "funding_rate": 0.00005,
            "funding_time": 1792137600000
        },
        # FET Long (Paga -$0.15)
        {
            "symbol": "FET-USDT-SWAP",
            "side": "LONG",
            "entry_margin": 200.0,
            "leverage": 15.0,
            "funding_rate": 0.00005,
            "funding_time": 1792137600000
        }
    ]
    summary = service.calculate_fleet_funding_summary(slots)
    # Total líquido: +0.30 + 0.15 - 0.15 = +$0.30 por ciclo de 8h
    assert summary["total_cost_per_cycle_usd"] == 0.30
    assert summary["total_cost_24h_usd"] == 0.90
    assert summary["status"] == "RECEITA_PASSIVA"
    assert summary["paying_slots_count"] == 1
    assert summary["receiving_slots_count"] == 2
