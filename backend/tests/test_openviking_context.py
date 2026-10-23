# -*- coding: utf-8 -*-
"""
Tests for OpenViking Context Database Engine for 1Crypten.
Verifies:
1. Virtual Filesystem Hierarchy (viking://resources, viking://user/memories, viking://agent/skills)
2. Three-Tier Progressive Disclosure (L0: Abstract, L1: Overview, L2: Detail)
3. Self-Evolving Memory & Trade Closure Lesson Generation
4. Hermes Context Synthesis & Invariant Integrity
"""

import os
import sys
import pytest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.openviking_context_service import (
    OpenVikingContextService,
    ContextLevel,
    VikingNode,
)


@pytest.fixture
def viking_service():
    # Inicia serviço apontando para o repositório raiz
    repo_root = BACKEND_DIR.parent
    service = OpenVikingContextService(root_dir=str(repo_root))
    service.sync_all()
    return service


def test_virtual_filesystem_tree(viking_service):
    """Verifica se a árvore virtual viking:// reflete a estrutura canônica."""
    tree = viking_service.tree("viking://")
    assert "resources" in tree
    assert "user" in tree
    assert "agent" in tree

    # Subpastas de user/memories
    user_tree = viking_service.tree("viking://user/memories")
    assert "preferences" in user_tree
    assert "patterns" in user_tree
    assert "cases" in user_tree


def test_progressive_disclosure_levels(viking_service):
    """Verifica se os níveis L0, L1 e L2 retornam granularidade crescente."""
    uri = "viking://user/memories/patterns/anti_faca"
    
    l0 = viking_service.read(uri, level=ContextLevel.ABSTRACT)
    l1 = viking_service.read(uri, level=ContextLevel.OVERVIEW)
    l2 = viking_service.read(uri, level=ContextLevel.DETAIL)

    assert l0 is not None
    assert l1 is not None
    assert l2 is not None

    # L0 deve ser conciso (~100 a 300 chars)
    assert len(l0) < len(l1)
    # L1 deve ter visão operacional completa
    assert len(l1) <= len(l2)
    # Invariante chave presente
    assert "1C-EXP >= 70" in l1 or "1c_exp" in l1.lower()


def test_search_and_retrieval(viking_service):
    """Verifica a busca estruturada por invariantes no sistema de arquivos virtual."""
    results = viking_service.search("Never Give Back", level=ContextLevel.OVERVIEW)
    assert len(results) > 0
    top = results[0]
    assert "never_give_back" in top["uri"].lower() or "invariante" in top["content"].lower() or "trailing" in top["content"].lower()


def test_self_evolving_trade_closure_lesson(viking_service, tmp_path):
    """Verifica se o fechamento de uma ordem gera aprendizado episódico persistente."""
    mock_trade = {
        "id": "trade_test_irys_01",
        "symbol": "IRYS-USDT-SWAP",
        "strategy": "DVWAP_REVERSION",
        "direction": "SHORT",
        "entry_price": 0.052,
        "exit_price": 0.054,
        "pnl_pct": -2.5,
        "exit_reason": "STOP_LOSS",
        "contract_meta": {
            "rationale": "Tentativa de reversao à media em pump acelerado",
            "1c_exp": 85,
        }
    }

    initial_cases = len(viking_service.ls("viking://user/memories/cases"))
    lesson_node = viking_service.record_trade_closure(mock_trade)

    assert lesson_node is not None
    assert "irys" in lesson_node.uri.lower()
    assert len(viking_service.ls("viking://user/memories/cases")) == initial_cases + 1

    # Ao ler o caso recém-gravado, o motivo e aprendizado devem estar presentes
    case_content = viking_service.read(lesson_node.uri, level=ContextLevel.OVERVIEW)
    assert "IRYS-USDT-SWAP" in case_content
    assert "STOP_LOSS" in case_content
    assert "DVWAP_REVERSION" in case_content


def test_hermes_hierarchical_context_synthesis(viking_service):
    """Verifica se o prompt enriquecido para o Hermes contém blocos estruturados."""
    prompt_context = viking_service.get_hierarchical_context_for_prompt(
        query="Como funciona a regra anti faca e o stop loss da laya?",
        max_tokens=1500
    )

    assert "[OPENVIKING // VIKING CONTEXT DATABASE]" in prompt_context
    assert "VIKING PREFERENCES" in prompt_context
    assert "VIKING TRADING PATTERNS" in prompt_context
    # Garante ausência total de emojis na formatação técnica
    assert "🚀" not in prompt_context
    assert "💡" not in prompt_context
