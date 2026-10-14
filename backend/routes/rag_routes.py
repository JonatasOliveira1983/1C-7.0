# -*- coding: utf-8 -*-
"""
1CRYPTEN 7.0 — RAG Knowledge & Intelligence Routes
Endpoints for semantic search across MASTER_ARCHITECTURE.md, vault_galaxy, and rules.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from services.rag_service import rag_service

router = APIRouter(prefix="/api/v1/hermes/rag", tags=["RAG & Intelligence"])


@router.get("/search")
async def rag_search(
    q: str = Query(..., description="Query de busca semantica no cofre"),
    top_k: int = Query(4, ge=1, le=20),
    category: Optional[str] = Query(None, description="Filtro de categoria (ARCHITECTURE, GALAXY_TRADES, RULES, etc)")
):
    try:
        results = rag_service.search(query=q, top_k=top_k, category=category)
        return {
            "status": "success",
            "query": q,
            "total_matches": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na busca RAG: {str(e)}")


@router.post("/reindex")
async def rag_reindex():
    try:
        import asyncio
        loop = asyncio.get_running_loop()
        stats = await loop.run_in_executor(None, rag_service.index_all)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao reindexar RAG: {str(e)}")


@router.get("/status")
async def rag_status():
    if not rag_service.is_indexed:
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, rag_service.index_all)
        except Exception:
            pass

    return {
        "status": "online",
        "is_indexed": rag_service.is_indexed,
        "total_chunks": rag_service.total_docs,
        "last_indexed_at": rag_service.last_indexed_at,
        "indexed_sources": [
            "MASTER_ARCHITECTURE.md",
            "vault_galaxy/ (journal, trades, strategies)",
            "AGENTS.md",
            ".agents/rules/",
            "docs/ (audits, blueprints, technical specs)"
        ]
    }
