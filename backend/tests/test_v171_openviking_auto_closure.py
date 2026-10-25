# -*- coding: utf-8 -*-
"""
1CRYPTEN 7.0 — Test V171: OpenViking Episodic Auto-Closure on Trailing & Stop Loss
Verifies that automated trade closures in sandbox_service trigger episodic memory
in OpenViking and persist to the Obsidian Vault.
"""
import pytest
import time
from unittest.mock import MagicMock, patch
from services.openviking_context_service import openviking_context_service, ContextLevel


@pytest.mark.asyncio
async def test_openviking_record_trade_closure_synthetic():
    """Valida gravação e progressive disclosure de fechamento de trade."""
    trade_payload = {
        "id": "test_v171_super_runner_01",
        "symbol": "SOL-USDT-SWAP",
        "strategy": "LAYA_DVWAP_REVERSION",
        "direction": "SHORT",
        "entry_price": 180.0,
        "exit_price": 140.0,
        "pnl_pct": 333.33,
        "exit_reason": "CLOSED_TRAILING",
        "contract_meta": {"rationale": "Desvio extremo de VWAP com rejeição em resistência H1"}
    }

    node = openviking_context_service.record_trade_closure(trade_payload)

    # 1. Deve criar o nó com a URI correta
    assert node.uri == "viking://user/memories/cases/case_sol_test_v171_super_runner_01"
    assert "SOL" in node.title
    assert "LUCRO" in node.title
    assert "+333.33%" in node.title

    # 2. Progressive Disclosure L0, L1, L2
    l0 = node.get_content(ContextLevel.ABSTRACT)
    l1 = node.get_content(ContextLevel.OVERVIEW)
    l2 = node.get_content(ContextLevel.DETAIL)

    assert "LUCRO de +333.33%" in l0
    assert "Invariante Never Give Back" in l1
    assert "Desvio extremo de VWAP" in l1
    assert len(l2) >= len(l1)

    # 3. Deve ser recuperável no nó do serviço
    retrieved = openviking_context_service.read(node.uri, level=ContextLevel.ABSTRACT)
    assert retrieved == l0


@pytest.mark.asyncio
async def test_openviking_record_trade_closure_loss():
    """Valida gravação de caso de loss com Escudo Anti-Faca."""
    loss_payload = {
        "id": "test_v171_loss_02",
        "symbol": "TIA-USDT-SWAP",
        "strategy": "ALT_PUMP_IGNITION",
        "direction": "LONG",
        "entry_price": 9.5,
        "exit_price": 9.2,
        "pnl_pct": -18.0,
        "exit_reason": "CLOSED_SL",
        "contract_meta": {"rationale": "Tentativa de rompimento violada"}
    }

    node = openviking_context_service.record_trade_closure(loss_payload)
    assert "PREJUÍZO" in node.title
    assert "-18.00%" in node.title
    assert "Escudo Anti-Faca" in node.get_content(ContextLevel.OVERVIEW)
