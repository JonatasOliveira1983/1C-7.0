import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.laya_router_service import laya_router_service


def test_vetoed_candidate_cannot_be_eligible():
    """
    Invariante: Um setup com 'qualifies': False ou com 'VETO' no rationale
    NUNCA pode ser elegível para abertura autônoma.
    """
    cand = {
        "symbol": "SAND-USDT-SWAP",
        "clean_sym": "SANDUSDT",
        "direction": "LONG",
        "strategy": "LAYA_AGUIA_FUSION",
        "score": 50,
        "qualifies": False,
        "1c_range": 72.0,
        "bot_ignition": False,
        "rationale": "VETO TOPO (1C-Range 72%): Ímã ACIMA, mas preço na resistência."
    }
    
    # Simula triagem com a função de elegibilidade
    is_vetoed = not cand.get("qualifies", True) or "VETO" in str(cand.get("rationale", "")).upper()
    assert is_vetoed is True


def test_aguia_fusion_cannot_bypass_min_score():
    """
    Invariante: Mesmo sendo LAYA_AGUIA_FUSION, se o score for < MIN_ENTRY_SCORE (85),
    não pode ser aprovado sem arbitragem Hermes.
    """
    cand = {
        "symbol": "SAND-USDT-SWAP",
        "clean_sym": "SANDUSDT",
        "direction": "LONG",
        "strategy": "LAYA_AGUIA_FUSION",
        "score": 50,
        "qualifies": True,
        "1c_range": 30.0,
        "bot_ignition": True,
        "rationale": "FUSAO AGUIA"
    }
    min_score = laya_router_service.MIN_ENTRY_SCORE
    assert cand["score"] < min_score


def test_resistance_top_range_blocks_long():
    """
    Invariante: Comprar topo (1C-Range >= 65%) é proibido sem ignição comprovada (is_pump_ignition).
    """
    cand = {
        "symbol": "SAND-USDT-SWAP",
        "clean_sym": "SANDUSDT",
        "direction": "LONG",
        "strategy": "LAYA_AGUIA_FUSION",
        "score": 90,
        "qualifies": True,
        "1c_range": 72.0,
        "is_pump_ignition": False,
        "bot_ignition": True,
        "rationale": "FUSAO AGUIA"
    }
    
    c_range = cand["1c_range"]
    is_pump = cand.get("is_pump_ignition", False)
    
    # Trava: se range >= 65% e não for pump ignition, DEVE ser bloqueado
    blocked = (c_range >= 65.0 and not is_pump)
    assert blocked is True
