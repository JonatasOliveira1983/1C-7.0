# tests/test_v224_telemetry_liquidation_enrichment.py
# Valida o enriquecimento do summary da telemetria com pools de liquidação e order flow

import os
import sys

# Garante inclusão de backend no path
sys.path.insert(0, os.path.abspath("backend"))

from app.services.telemetry_service import telemetry_service


def test_telemetry_summary_contains_liquidation_and_order_flow():
    summary = telemetry_service.get_summary()
    assert summary is not None
    assert summary["status"] == "ONLINE"
    
    # Valida campos de enriquecimento da V224
    assert "liquidation_intel" in summary, "liquidation_intel deve estar presente no summary"
    liq = summary["liquidation_intel"]
    assert "top_pools" in liq
    assert isinstance(liq["top_pools"], list)
    assert "order_flow" in liq
    assert "btc_lsr" in liq["order_flow"]
    assert "taker_flow" in liq["order_flow"]
    
    # Valida presença dos top candidates enriquecidos
    assert "top_candidates" in summary
    assert "scan_cycle" in summary
    assert summary["version"].startswith("V2")
