# -*- coding: utf-8 -*-
"""
1CRYPTEN 7.0 — Unified RAG Service Gateway (Base Tecnológica SSOT)
Forwards all requests to backend.services.rag_service, unifying:
- MASTER_ARCHITECTURE.md (Invariants & canonical design)
- vault_galaxy/ (Obsidian Vault: journal, trades, strategies)
- .agents/rules/ & AGENTS.md (Superpowers methodology)
- docs/ (Audits, blueprints, technical specs)
- backend/data/knowledge/
"""
from services.rag_service import rag_service, RAGService, KnowledgeChunk

__all__ = ["rag_service", "RAGService", "KnowledgeChunk"]
