"""
TDD Tests for Hermes Omniscience:
Validates that Hermes and OpenViking possess full context of:
1. Plutus Agent (viking://agent/plutus & live dashboard state)
2. Telemetry System (viking://system/telemetry & live latency/slippage state)
3. Laya 360 (viking://agent/laya360 & Top 30 Titans candidate pulse)
4. Blueprints Documentation (viking://resources/blueprints/*)
"""

import pytest


def test_openviking_indexes_plutus_and_telemetry():
    """Validates that OpenViking contains nodes for Plutus and Telemetry."""
    from services.openviking_context_service import openviking_context_service, ContextLevel

    node_plutus = openviking_context_service.get_node("viking://agent/plutus")
    assert node_plutus is not None, "Node viking://agent/plutus must exist in OpenViking"
    assert "ARCA" in node_plutus.get_content(ContextLevel.OVERVIEW).upper()

    node_telem = openviking_context_service.get_node("viking://system/telemetry")
    assert node_telem is not None, "Node viking://system/telemetry must exist in OpenViking"
    assert "SLIPPAGE" in node_telem.get_content(ContextLevel.OVERVIEW).upper()


def test_openviking_indexes_blueprints():
    """Validates that OpenViking indexes files from docs/blueprint/."""
    from services.openviking_context_service import openviking_context_service, ContextLevel

    node_bp = openviking_context_service.get_node("viking://resources/blueprints/07_plano_agente_plutus_arca")
    assert node_bp is not None, "Node for blueprint 07 must exist in OpenViking"
    assert "ARCA" in node_bp.get_content(ContextLevel.ABSTRACT).upper()


def test_hermes_runtime_context_contains_plutus_and_telemetry():
    """Validates that _build_runtime_context injects live Plutus and Telemetry state."""
    from app.services.hermes_service import _build_runtime_context

    # Query with a Plutus-related prompt
    ctx_system, _ = _build_runtime_context("Como esta a alocacao do Plutus e o metodo ARCA?")
    assert "PLUTUS" in ctx_system.upper(), "Runtime context must contain Plutus section"
    assert "ARCA" in ctx_system.upper(), "Runtime context must detail ARCA method"
    assert "TELEMETRIA" in ctx_system.upper(), "Runtime context must contain Telemetry section"
    assert "LATENCIA" in ctx_system.upper() or "SLIPPAGE" in ctx_system.upper(), "Runtime context must detail Telemetry metrics"
