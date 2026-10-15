# -*- coding: utf-8 -*-
"""
Tests for MemoryService & SQLiteMemoryStore (Mem0 Pattern for 1Crypten)
Covers:
1. Creation of episodic memory for crypto pairs
2. Automatic deduplication & confidence increment
3. Search by token and relevance scoring
4. Pair context synthesis for Laya Sovereign Brain
5. Persistence across store reload
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.models.memory import MemoryCreate, MemoryType, MemorySearchQuery
from app.services.memory_store import SQLiteMemoryStore
from app.services.memory_service import MemoryService


@pytest.fixture
def temp_db_store():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    store = SQLiteMemoryStore(db_path=db_path)
    yield store
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass


def test_add_and_retrieve_memory(temp_db_store):
    service = MemoryService(store=temp_db_store)
    dto = MemoryCreate(
        namespace="crypto_pair",
        entity_id="SOLUSDT",
        memory_type=MemoryType.EPISODIC,
        content="Resistência forte em 154.50 com absorção institucional de venda",
        confidence=0.8,
        metadata={"timeframe": "15m", "regime": "BEARISH_ABSORPTION"}
    )
    created = service.add_memory(dto)
    assert created.id.startswith("mem-")
    assert created.entity_id == "SOLUSDT"
    assert created.confidence == 0.8
    assert created.metadata["timeframe"] == "15m"

    retrieved = temp_db_store.get(created.id)
    assert retrieved is not None
    assert retrieved.content == dto.content
    assert retrieved.access_count == 1


def test_memory_deduplication_and_confidence_boost(temp_db_store):
    service = MemoryService(store=temp_db_store)
    dto1 = MemoryCreate(
        namespace="crypto_pair",
        entity_id="SUIUSDT",
        memory_type=MemoryType.EPISODIC,
        content="Funding rate negativo extremo com long squeeze em andamento",
        confidence=0.7,
        metadata={"count": 1}
    )
    m1 = service.add_memory(dto1)
    assert m1.confidence == 0.7

    # Inserção idêntica de conteúdo normalizado (mesmo par e namespace)
    dto2 = MemoryCreate(
        namespace="crypto_pair",
        entity_id="SUIUSDT",
        memory_type=MemoryType.EPISODIC,
        content="Funding rate negativo extremo com long squeeze em andamento",
        confidence=0.7,
        metadata={"count": 2, "source": "Rubik"}
    )
    m2 = service.add_memory(dto2)

    # Não deve ter criado nova entrada, mas sim atualizado a existente com boost de confiança (+0.1)
    assert m2.id == m1.id
    assert m2.confidence == 0.8
    assert m2.metadata["count"] == 2
    assert m2.metadata["source"] == "Rubik"

    # Confirma que só há 1 registro no banco
    all_sui = temp_db_store.search(namespace="crypto_pair", entity_id="SUIUSDT")
    assert len(all_sui) == 1


def test_search_memories_with_token_relevance(temp_db_store):
    service = MemoryService(store=temp_db_store)
    service.record_pair_insight("BTCUSDT", "Farol Macro Bitcoin em expansão de volatilidade ADX 35", confidence=0.9)
    service.record_pair_insight("BTCUSDT", "Funding rate neutro em 0.010%", confidence=0.7)
    service.record_pair_insight("ETHUSDT", "Ethereum rompendo resistência dos 2650 com alto volume", confidence=0.85)

    query = MemorySearchQuery(
        namespace="crypto_pair",
        entity_id="BTCUSDT",
        query="volatilidade",
        limit=5
    )
    results = service.search_memories(query)
    assert len(results) >= 1
    assert "volatilidade" in results[0].item.content.lower()
    assert results[0].score >= 0.8


def test_synthesize_pair_memory_for_laya(temp_db_store):
    service = MemoryService(store=temp_db_store)
    service.record_pair_insight("XPLUSDT", "Gatilho de Momentum Mola confirmado com confluência Kronos 82%", confidence=0.9)
    service.record_pair_insight("XPLUSDT", "LSR favorável 0.85 indicando desespero de sardinhas vendidas", confidence=0.85)

    context = service.synthesize_pair_memory("XPLUSDT", limit=2)
    assert "[MEMÓRIAS OPERACIONAIS REGISTRADAS: XPLUSDT]" in context
    assert "Momentum Mola" in context
    assert "LSR favorável" in context


def test_store_persistence(temp_db_store):
    service = MemoryService(store=temp_db_store)
    service.record_pair_insight("AVAXUSDT", "Whale orderbook wall detectada em 28.00", confidence=0.8)

    # Recarrega nova instância apontando para o mesmo banco SQLite
    reloaded_store = SQLiteMemoryStore(db_path=temp_db_store.db_path)
    memories = reloaded_store.search(namespace="crypto_pair", entity_id="AVAXUSDT")
    assert len(memories) == 1
    assert "Whale orderbook wall" in memories[0].content
