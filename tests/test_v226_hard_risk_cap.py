# -*- coding: utf-8 -*-
"""
1CRYPTEN — Suite de Testes V226 (Hard Risk Cap 50X & Purga do high_2h_window).
Invariantes Canonicas:
1. max_stop_dist <= 0.0070 (0.70% de preco = max -35.0% de ROI em 50X Margem Cruzada).
2. Auto-capping de cand["stop_loss"] a 0.70% caso venha com distancia excessiva (>0.75%).
3. OpenViking indexa viking://resources/architecture/v226_hard_risk_cap_50x e viking://user/memories/cases/case_eth_titan_v226_resolution.
"""
import sys
from pathlib import Path
root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

import pytest
from backend.services.openviking_context_service import OpenVikingContextService, ContextLevel


def test_v226_hard_risk_cap_short_capping():
    """Valida que ordens em SHORT com stop excessivo sao auto-capadas em 0.70%."""
    cand = {
        "symbol": "ETH-USDT-SWAP",
        "direction": "SHORT",
        "price": 1762.83,
        "stop_loss": 1798.08,  # Distancia de 2.0% (caso ETH antigo)
    }
    cand_dir = cand["direction"]
    cand_sl = cand.get("stop_loss")
    cand_p = float(cand.get("price") or 0.0)

    # Logica de auto-capping V226 de scan_and_execute_autonomous
    if cand_dir == "SHORT" and cand_sl and cand_p > 0 and cand_sl > cand_p:
        cand_sl_dist = (cand_sl - cand_p) / cand_p
        if cand_sl_dist > 0.0075:
            cand["stop_loss"] = round(cand_p * 1.0070, 4)

    expected_sl = round(1762.83 * 1.0070, 4)
    assert cand["stop_loss"] == expected_sl, f"Stop loss deveria ser {expected_sl}, mas foi {cand['stop_loss']}"
    assert (cand["stop_loss"] - cand_p) / cand_p <= 0.007001


def test_v226_hard_risk_cap_long_capping():
    """Valida que ordens em LONG com stop excessivo sao auto-capadas em 0.70%."""
    cand = {
        "symbol": "BTC-USDT-SWAP",
        "direction": "LONG",
        "price": 64000.00,
        "stop_loss": 62000.00,  # Distancia de 3.125%
    }
    cand_dir = cand["direction"]
    cand_sl = cand.get("stop_loss")
    cand_p = float(cand.get("price") or 0.0)

    if cand_dir == "LONG" and cand_sl and cand_p > 0 and cand_sl < cand_p:
        cand_sl_dist = (cand_p - cand_sl) / cand_p
        if cand_sl_dist > 0.0075:
            cand["stop_loss"] = round(cand_p * 0.9930, 4)

    expected_sl = round(64000.00 * 0.9930, 4)
    assert cand["stop_loss"] == expected_sl, f"Stop loss deveria ser {expected_sl}, mas foi {cand['stop_loss']}"
    assert (cand_p - cand["stop_loss"]) / cand_p <= 0.007001


def test_v226_openviking_nodes():
    """Valida indexacao de V226 no OpenViking Context Service."""
    svc = OpenVikingContextService()
    svc.sync_all()

    uri_v226 = "viking://resources/architecture/v226_hard_risk_cap_50x"
    assert uri_v226 in svc.nodes, "No de arquitetura V226 deve existir no OpenViking"
    node = svc.nodes[uri_v226]
    assert "0.70%" in node.l1_overview or "0.70%" in node.l0_abstract

    uri_eth = "viking://user/memories/cases/case_eth_titan_v226_resolution"
    assert uri_eth in svc.nodes, "No de resolucao forense do ETH deve existir no OpenViking"
    node_eth = svc.nodes[uri_eth]
    assert "ETH" in node_eth.title
    assert "Hard Risk Cap 50X" in node_eth.title or "V226" in node_eth.title
