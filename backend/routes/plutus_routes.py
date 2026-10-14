# -*- coding: utf-8 -*-
"""
1CRYPTEN 7.0 — ROTAS FASTAPI DO AGENTE PLUTUS (VIVER DE RENDA / ARCA)
Expõe endpoints REST para simulação de renda, universo de ativos e diagnóstico do Hermes.
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from services.plutus_agent import plutus_agent, ARCA_UNIVERSE, ARCA_PROFILES

router = APIRouter(prefix="/api/v1/plutus", tags=["PLUTUS - Viver de Renda"])


class IncomeSimulationRequest(BaseModel):
    target_monthly_income_brl: float = Field(default=50000.0, description="Renda líquida mensal desejada em R$")
    profile_key: str = Field(default="ARCA_EQUILIBRADA", description="Perfil ARCA: CONSERVADOR, ARCA_EQUILIBRADA ou ACELERADOR_PROVENTOS")
    current_patrimony_brl: float = Field(default=0.0, description="Patrimônio já acumulado para cálculo de gap")


@router.post("/simulate")
async def simulate_income_route(payload: IncomeSimulationRequest):
    """
    Calcula a matemática financeira reversa para viver de renda.
    Retorna patrimônio necessário, divisão por pilares e lista de compras cota a cota.
    """
    try:
        await plutus_agent.update_live_quotes_if_needed()
        result = plutus_agent.simulate_income(
            target_monthly_income_brl=payload.target_monthly_income_brl,
            profile_key=payload.profile_key,
            current_patrimony_brl=payload.current_patrimony_brl
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao simular carteira Plutus: {str(e)}")


@router.get("/universe")
async def get_arca_universe():
    """Retorna o universo curado de ativos da ARCA (FIIs, Ações, Caixa, Internacional)."""
    return {
        "status": "success",
        "profiles": ARCA_PROFILES,
        "universe": ARCA_UNIVERSE
    }


@router.post("/hermes-diagnosis")
async def get_hermes_diagnosis(payload: IncomeSimulationRequest):
    """Hermes Intelligence emite o parecer executivo e confluência de risco sobre a carteira."""
    try:
        sim = plutus_agent.simulate_income(
            target_monthly_income_brl=payload.target_monthly_income_brl,
            profile_key=payload.profile_key,
            current_patrimony_brl=payload.current_patrimony_brl
        )
        diagnosis = plutus_agent.generate_hermes_diagnosis(sim)
        return diagnosis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar diagnóstico do Hermes: {str(e)}")
