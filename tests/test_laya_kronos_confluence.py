# -*- coding: utf-8 -*-
"""
Testes TDD para a Matriz de Confluência Laya + Kronos.
Cobre:
1. Veto de Armadilha de Varejo (Retail Trap / Veto Buy).
2. Confluência Sniper Long (Varredura de stops + Inflexão de alta Kronos).
3. Confluência Sniper Short (Exaustão de compra + Quebra de suporte Kronos).
4. Proteção por Dispersão Caótica de Trajetórias (Redução de alavancagem para 20x).
5. Conflito Temporal (Divergência entre fluxo e previsão geométrica).
"""
import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

# Assegura que o backend esteja no sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.laya_kronos_confluence_service import (
    LayaKronosConfluenceService,
    laya_kronos_confluence_service
)


def test_confluence_veto_retail_fomo_long():
    """Varejo eufórico (LSR >= 1.35) deve vetar compra mesmo se Kronos apontar UP."""
    flow = {
        "lsr": 1.45,
        "oi_delta_pct": 1.2,
        "flow_regime": "RETAIL_FOMO_INJECTION",
        "whale_signal": "VETO_BUY",
        "veto_reason": "Varejo em euforia extrema"
    }
    kronos = {
        "conviction": 85.0,
        "prediction_direction": "UP",
        "predicted_change_pct": 1.5,
        "paths_dispersion": 0.012
    }
    
    result = laya_kronos_confluence_service.evaluate_confluence(flow, kronos, side="BUY")
    assert result["is_vetoed"] is True
    assert result["confluence_type"] == "RETAIL_TRAP_VETO"
    assert result["score_boost"] < 0
    assert result["leverage_cap"] <= 10.0


def test_confluence_sniper_long_liquidation_bottom():
    """Varredura de stops concluída (fundo) + Kronos UP deve gerar confluência máxima de compra."""
    flow = {
        "lsr": 0.95,
        "oi_delta_pct": -0.8,
        "flow_regime": "LONG_LIQUIDATION_BOTTOM",
        "whale_signal": "SNIPER_BUY_REVERSAL"
    }
    kronos = {
        "conviction": 80.0,
        "prediction_direction": "UP",
        "predicted_change_pct": 2.1,
        "paths_dispersion": 0.015
    }
    
    result = laya_kronos_confluence_service.evaluate_confluence(flow, kronos, side="BUY")
    assert result["is_vetoed"] is False
    assert result["confluence_type"] == "INSTITUTIONAL_SNIPER_LONG"
    assert result["score_boost"] >= 10
    assert result["leverage_cap"] == 50.0


def test_confluence_sniper_short_squeeze_exhaustion():
    """Exaustão de compra + Kronos DOWN deve gerar confluência máxima de venda (SHORT)."""
    flow = {
        "lsr": 1.38,
        "oi_delta_pct": -0.5,
        "flow_regime": "SHORT_SQUEEZE_EXHAUSTION",
        "whale_signal": "PREPARE_SHORT_REVERSAL"
    }
    kronos = {
        "conviction": 75.0,
        "prediction_direction": "DOWN",
        "predicted_change_pct": -1.8,
        "paths_dispersion": 0.018
    }
    
    result = laya_kronos_confluence_service.evaluate_confluence(flow, kronos, side="SELL")
    assert result["is_vetoed"] is False
    assert result["confluence_type"] == "INSTITUTIONAL_SNIPER_SHORT"
    assert result["score_boost"] >= 10


def test_confluence_high_dispersion_caps_leverage():
    """Alta dispersão de trajetórias do Kronos deve reduzir alavancagem para no máximo 20x."""
    flow = {
        "lsr": 1.05,
        "oi_delta_pct": 0.1,
        "flow_regime": "CONSOLIDATION_ABSORPTION",
        "whale_signal": "HOLD"
    }
    kronos = {
        "conviction": 55.0,
        "prediction_direction": "UP",
        "predicted_change_pct": 0.4,
        "paths_dispersion": 0.042  # Dispersão muito alta
    }
    
    result = laya_kronos_confluence_service.evaluate_confluence(flow, kronos, side="BUY")
    assert result["leverage_cap"] <= 20.0
    assert result["confluence_type"] == "HIGH_DISPERSION_UNCERTAINTY"


def test_confluence_directional_conflict():
    """Sinal de compra quando Kronos prevê queda forte deve penalizar o score."""
    flow = {
        "lsr": 1.05,
        "oi_delta_pct": 0.1,
        "flow_regime": "NEUTRAL",
        "whale_signal": "HOLD"
    }
    kronos = {
        "conviction": 78.0,
        "prediction_direction": "DOWN",
        "predicted_change_pct": -2.5,
        "paths_dispersion": 0.015
    }
    
    result = laya_kronos_confluence_service.evaluate_confluence(flow, kronos, side="BUY")
    assert result["confluence_type"] == "TEMPORAL_DIVERGENCE"
    assert result["score_boost"] < 0


@pytest.mark.asyncio
async def test_endpoint_laya_kronos_confluence():
    """Testa a rota GET /api/v1/laya/kronos-confluence com mock de dados."""
    from app.api.v1.endpoints.hermes import laya_kronos_confluence_endpoint
    
    # Mock do flow e kronos
    with patch("app.services.laya_flow_service.laya_flow_service.get_flow_radar", new_callable=AsyncMock) as mock_flow, \
         patch("services.kronos_scorer.kronos_scorer.score_signal", new_callable=AsyncMock) as mock_kronos:
        
        mock_flow.return_value = {
            "lsr": 0.92,
            "oi_delta_pct": -0.6,
            "flow_regime": "LONG_LIQUIDATION_BOTTOM",
            "whale_signal": "SNIPER_BUY_REVERSAL"
        }
        mock_kronos.return_value = {
            "conviction": 84.0,
            "prediction_direction": "UP",
            "predicted_change_pct": 2.4,
            "paths_dispersion": 0.012
        }
        
        response = await laya_kronos_confluence_endpoint(symbol="SOLUSDT", side="BUY")
        
        assert response["symbol"] == "SOLUSDT"
        assert response["side"] == "BUY"
        assert "flow" in response
        assert "kronos" in response
        assert "confluence" in response
        assert response["confluence"]["confluence_type"] == "INSTITUTIONAL_SNIPER_LONG"
        assert response["confluence"]["score_boost"] == 15
        assert response["confluence"]["is_vetoed"] is False

