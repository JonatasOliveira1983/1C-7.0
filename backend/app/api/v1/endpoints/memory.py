# -*- coding: utf-8 -*-
"""
Endpoints de Memória Agêntica Episódica e Deduplicada (Padrão Mem0 para 1Crypten).
Permite auditoria em tempo real do conhecimento acumulado da Laya sobre os pares de trading.
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException
from app.models.memory import (
    MemoryCreate,
    MemoryItem,
    MemorySearchQuery,
    MemorySearchResult,
    MemoryType,
)
from app.services.memory_service import memory_service

router = APIRouter()


@router.get("/stats", summary="Estatísticas do Banco de Memória")
async def get_memory_stats() -> Dict[str, Any]:
    """Retorna contadores de memórias ativas por namespace e caminho do SQLite."""
    return memory_service.get_stats()


@router.get("/pair/{pair}", summary="Consulta Conhecimento de um Par Específico")
async def get_pair_memory(
    pair: str,
    limit: int = Query(default=5, ge=1, le=50),
) -> Dict[str, Any]:
    """
    Retorna os insights episódicos memorizados sobre um par e a síntese
    estruturada injetada na consciência da Laya Soberana.
    """
    insights = memory_service.get_pair_insights(pair=pair, limit=limit)
    synthesized = memory_service.synthesize_pair_memory(pair=pair, limit=limit)
    return {
        "pair": pair.upper(),
        "total_insights": len(insights),
        "synthesized_context": synthesized,
        "insights": [
            {
                "id": r.item.id,
                "content": r.item.content,
                "confidence": r.item.confidence,
                "memory_type": r.item.memory_type.value,
                "score": r.score,
                "metadata": r.item.metadata,
                "updated_at": r.item.updated_at.isoformat(),
            }
            for r in insights
        ],
    }


@router.get("/search", summary="Busca Textual em Memórias")
async def search_memories(
    q: Optional[str] = Query(default=None, description="Termo de busca textual"),
    namespace: str = Query(default="crypto_pair", description="Namespace"),
    entity_id: Optional[str] = Query(default=None, description="Filtro de entidade/par"),
    min_confidence: float = Query(default=0.0, ge=0.0, le=1.0),
    limit: int = Query(default=10, ge=1, le=100),
) -> List[Dict[str, Any]]:
    """Busca memórias aplicando ranking de relevância por tokens e peso de confiança."""
    query = MemorySearchQuery(
        namespace=namespace,
        entity_id=entity_id.upper() if entity_id else None,
        query=q,
        min_confidence=min_confidence,
        limit=limit,
    )
    results = memory_service.search_memories(query)
    return [
        {
            "id": r.item.id,
            "entity_id": r.item.entity_id,
            "namespace": r.item.namespace,
            "content": r.item.content,
            "confidence": r.item.confidence,
            "score": r.score,
            "metadata": r.item.metadata,
            "updated_at": r.item.updated_at.isoformat(),
        }
        for r in results
    ]


@router.post("/add", summary="Registrar Nova Memória Manual ou Tática")
async def add_memory(dto: MemoryCreate) -> Dict[str, Any]:
    """Registra uma memória com deduplicação automática e incremento de confiança."""
    item = memory_service.add_memory(dto)
    return {
        "status": "success",
        "id": item.id,
        "entity_id": item.entity_id,
        "confidence": item.confidence,
        "content": item.content,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }
