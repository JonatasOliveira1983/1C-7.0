# -*- coding: utf-8 -*-
"""
Serviço de Inteligência de Memória Agêntica (Padrão Mem0 para 1Crypten).
Responsável por deduplicação de fatos, pontuação de confiança contextual
e síntese de memórias de pares de criptoativos para a Laya Soberana e Hermes.
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from app.models.memory import (
    MemoryCreate,
    MemoryItem,
    MemorySearchQuery,
    MemorySearchResult,
    MemoryType,
)
from app.services.memory_store import SQLiteMemoryStore, memory_store as default_memory_store


class MemoryService:
    """Orquestrador de memória persistente para Laya com deduplicação e busca contextual."""

    def __init__(self, store: Optional[SQLiteMemoryStore] = None):
        self.store = store or default_memory_store

    def add_memory(self, dto: MemoryCreate) -> MemoryItem:
        """
        Adiciona uma memória com deduplicação automática:
        Se já existir uma memória com o mesmo namespace, entity_id e conteúdo normalizado,
        reforça a confiança da existente (+0.1 até 1.0), mescla metadados e atualiza updated_at.
        """
        normalized_content = dto.content.strip().lower()
        candidates = self.store.search(
            namespace=dto.namespace,
            entity_id=dto.entity_id,
            limit=50,
        )

        for candidate in candidates:
            if candidate.content.strip().lower() == normalized_content:
                # Deduplicação: reforçar confiança e fundir metadados
                candidate.confidence = round(min(1.0, candidate.confidence + 0.1), 3)
                if dto.metadata:
                    candidate.metadata.update(dto.metadata)
                candidate.updated_at = datetime.now(timezone.utc)
                return self.store.update(candidate)

        # Se não existe correspondência exata, persiste nova memória
        return self.store.put(dto)

    def search_memories(self, query: MemorySearchQuery) -> List[MemorySearchResult]:
        """
        Busca memórias aplicando filtros e calculando pontuação de relevância.
        """
        items = self.store.search(
            namespace=query.namespace,
            entity_id=query.entity_id,
            memory_type=query.memory_type,
            query=query.query,
            limit=query.limit * 2 if query.query else query.limit,
            min_confidence=query.min_confidence,
        )

        results: List[MemorySearchResult] = []
        q_tokens = [t.lower() for t in query.query.split()] if query.query else []

        for item in items:
            score = item.confidence
            if q_tokens:
                text_lower = item.content.lower()
                matches = sum(1 for token in q_tokens if token in text_lower)
                token_ratio = matches / len(q_tokens)
                score = round(score * (0.5 + 0.5 * token_ratio), 3)

            results.append(MemorySearchResult(item=item, score=score))

        # Ordena pelo score decrescente
        results.sort(key=lambda r: r.score, reverse=True)
        return results[: query.limit]

    def synthesize_context(
        self,
        namespace: str,
        entity_id: str,
        limit: int = 5,
    ) -> str:
        """
        Sintetiza as memórias mais relevantes em um bloco estruturado para injeção.
        """
        items = self.store.search(
            namespace=namespace,
            entity_id=entity_id,
            limit=limit,
        )
        if not items:
            return ""

        lines = [
            f"--- [MEMÓRIAS OPERACIONAIS REGISTRADAS: {entity_id}] ---",
        ]
        for it in items:
            lines.append(
                f"- [{it.memory_type.value.upper()}] (conf: {it.confidence:.2f}) {it.content}"
            )
        lines.append("---")
        return "\n".join(lines)

    # =========================================================================
    # Helpers Especializados para a Laya Soberana e Trading Desk
    # =========================================================================

    def record_pair_insight(
        self,
        pair: str,
        content: str,
        confidence: float = 0.8,
        metadata: Optional[Dict[str, Any]] = None,
        memory_type: MemoryType = MemoryType.EPISODIC,
    ) -> MemoryItem:
        """Registra uma observação ou padrão de comportamento sobre um par de trading."""
        pair_norm = pair.replace("-USDT-SWAP", "").replace("USDT", "") + "USDT"
        dto = MemoryCreate(
            namespace="crypto_pair",
            entity_id=pair_norm.upper(),
            memory_type=memory_type,
            content=content.strip(),
            confidence=confidence,
            metadata=metadata or {},
        )
        return self.add_memory(dto)

    def record_macro_fact(
        self,
        content: str,
        confidence: float = 0.9,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryItem:
        """Registra um insight macro sobre o Bitcoin ou clima geral do mercado."""
        dto = MemoryCreate(
            namespace="macro_oracle",
            entity_id="BTC",
            memory_type=MemoryType.EPISODIC,
            content=content.strip(),
            confidence=confidence,
            metadata=metadata or {},
        )
        return self.add_memory(dto)

    def get_pair_insights(self, pair: str, limit: int = 5) -> List[MemorySearchResult]:
        """Recupera os insights mais recentes sobre um par."""
        pair_norm = pair.replace("-USDT-SWAP", "").replace("USDT", "") + "USDT"
        query = MemorySearchQuery(
            namespace="crypto_pair",
            entity_id=pair_norm.upper(),
            limit=limit,
        )
        return self.search_memories(query)

    def synthesize_pair_memory(self, pair: str, limit: int = 3) -> str:
        """Gera síntese rápida em texto das memórias do par para Laya."""
        pair_norm = pair.replace("-USDT-SWAP", "").replace("USDT", "") + "USDT"
        return self.synthesize_context(namespace="crypto_pair", entity_id=pair_norm.upper(), limit=limit)

    def get_stats(self) -> Dict[str, Any]:
        """Estatísticas globais de memórias ativas."""
        total = self.store.count()
        crypto_pairs = self.store.count(namespace="crypto_pair")
        macro = self.store.count(namespace="macro_oracle")
        return {
            "total_memories": total,
            "crypto_pairs_memories": crypto_pairs,
            "macro_memories": macro,
            "db_path": self.store.db_path,
        }


memory_service = MemoryService()
