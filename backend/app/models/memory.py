# -*- coding: utf-8 -*-
"""
Modelos agnósticos de persistência de memória para o 1Crypten.
Padrão Mem0: Working Memory, Episodic Memory (Insights de pares/fatos) e Semantic Memory (RAG).
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4
from pydantic import BaseModel, Field, ConfigDict


class MemoryType(str, Enum):
    """Tipos fundamentais de memória agnóstica."""
    WORKING = "working"      # Contexto imediato de sessão ou varredura atual
    EPISODIC = "episodic"    # Fatos de pares, vetos, absorções e comportamentos observados
    SEMANTIC = "semantic"    # Conhecimento indexado, regras macro e playbook


class MemoryBase(BaseModel):
    """Atributos base compartilhados de um registro de memória."""
    model_config = ConfigDict(extra="ignore")

    namespace: str = Field(
        default="crypto_pair",
        description="Identificador de partição / domínio (ex: crypto_pair, macro_oracle, operator_rules)"
    )
    entity_id: str = Field(
        ...,
        min_length=1,
        description="Identificador da entidade associada (ex: SOLUSDT, BTCUSDT, LAYA, OPERATOR)"
    )
    memory_type: MemoryType = Field(
        default=MemoryType.EPISODIC,
        description="Categoria funcional da memória"
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Conteúdo textual do fato ou contexto memorizado"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados estruturados (timeframe, regime, confluencia, fonte)"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Grau de certeza ou peso da memória (0.0 a 1.0)"
    )
    expires_at: Optional[datetime] = Field(
        default=None,
        description="Data opcional de expiração da memória (TTL)"
    )


class MemoryCreate(MemoryBase):
    """DTO para inserção ou registro de nova memória."""
    pass


class MemoryItem(MemoryBase):
    """Registro completo de memória persistida com metadados de ciclo de vida."""
    id: str = Field(
        default_factory=lambda: f"mem-{uuid4()}",
        description="Identificador único universal da memória"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp UTC de criação"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp UTC da última alteração"
    )
    access_count: int = Field(
        default=0,
        ge=0,
        description="Número de vezes que esta memória foi recuperada"
    )
    last_accessed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp UTC do último acesso/recuperação"
    )


class MemorySearchQuery(BaseModel):
    """Parâmetros de consulta e busca em memórias persistidas."""
    model_config = ConfigDict(extra="ignore")

    namespace: str = Field(default="crypto_pair", description="Namespace para isolamento")
    entity_id: Optional[str] = Field(default=None, description="Filtro opcional por entidade (par ou agente)")
    memory_type: Optional[MemoryType] = Field(default=None, description="Filtro opcional por tipo")
    query: Optional[str] = Field(default=None, description="Termo de busca textual ou semântica")
    limit: int = Field(default=10, ge=1, le=100, description="Quantidade máxima de resultados")
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Corte mínimo de confiança")


class MemorySearchResult(BaseModel):
    """Resultado individual de busca contendo item e score de relevância."""
    model_config = ConfigDict(extra="ignore")

    item: MemoryItem
    score: float = Field(..., ge=0.0, le=1.0, description="Pontuação combinada de relevância e confiança")
