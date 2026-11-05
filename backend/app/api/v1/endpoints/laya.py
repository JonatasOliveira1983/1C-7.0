# -*- coding: utf-8 -*-
"""
API Endpoints para Catálogo e Gestão de Estratégias Quantitativas da Laya Soberana.
Padrão 1Crypten: Zero Emojis, Alavancagem Fixa 50X, Invariante Never Give Back.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from database.migrations.create_laya_strategies_table import (
    list_active_strategies,
    get_strategy_by_id,
    seed_canonical_strategies,
)

router = APIRouter()

class StrategyParam(BaseModel):
    key: str
    value: str
    type: str
    description: Optional[str] = None

class StrategyResponse(BaseModel):
    id: str
    name: str
    category: str
    regime: str
    mathematical_basis: str
    academic_source: Optional[str] = None
    default_leverage: float
    min_adx: float
    max_adx: float
    active: int
    params: Dict[str, str]

@router.get("/strategies", response_model=List[Dict[str, Any]])
def get_laya_strategies(category: Optional[str] = None, regime: Optional[str] = None):
    """
    Retorna o catálogo de estratégias quantitativas ativas da Laya Soberana,
    embasadas por literatura acadêmica e calibradas para 50X Isolada.
    """
    try:
        strategies = list_active_strategies()
        if category:
            strategies = [s for s in strategies if s["category"].upper() == category.upper()]
        if regime:
            strategies = [s for s in strategies if s["regime"].upper() == regime.upper()]
        return strategies
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar estratégias da Laya: {str(e)}")

@router.get("/strategies/{strategy_id}", response_model=Dict[str, Any])
def get_laya_strategy_detail(strategy_id: str):
    """Retorna detalhes completos e parâmetros matemáticos de uma estratégia específica."""
    strategy = get_strategy_by_id(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Estratégia '{strategy_id}' não encontrada no catálogo.")
    return strategy

@router.post("/strategies/seed")
def seed_strategies():
    """Restaura e sincroniza o catálogo mestre de estratégias canônicas no SQLite."""
    try:
        seed_canonical_strategies()
        return {"status": "ok", "message": "Catálogo de estratégias canônicas sincronizado com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao sincronizar catálogo: {str(e)}")
