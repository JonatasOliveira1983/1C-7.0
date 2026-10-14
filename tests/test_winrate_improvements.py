import os
import sys

sys.path.insert(0, os.path.abspath("backend"))

import pytest
import time
from unittest.mock import MagicMock, AsyncMock, patch

from services.order_projection_service import (
    OrderProjectionService,
    StopLevel,
    ORDER_STOP_LADDER_LAYA_REVERSION
)


def test_order_stop_ladder_laya_reversion_structure():
    """Valida que a escadinha da Laya tem o Early Shield em 4.0% e Breakeven em 6.0%."""
    levels = {lvl.name: lvl for lvl in ORDER_STOP_LADDER_LAYA_REVERSION}
    
    assert "EARLY_SHIELD_LAYA" in levels, "EARLY_SHIELD_LAYA deve existir na escadinha"
    early_shield = levels["EARLY_SHIELD_LAYA"]
    assert early_shield.trigger_roi == 4.0
    assert early_shield.stop_roi == -2.0
    
    assert "GARANTIA_TAXAS_LAYA" in levels, "GARANTIA_TAXAS_LAYA deve existir"
    garantia = levels["GARANTIA_TAXAS_LAYA"]
    assert garantia.trigger_roi == 6.0
    assert garantia.stop_roi == 1.5


def test_never_give_back_monotonicity_laya():
    """Invariante Never Give Back: os degraus de stop da Laya devem ser estritamente crescentes."""
    triggers = [lvl.trigger_roi for lvl in ORDER_STOP_LADDER_LAYA_REVERSION]
    stops = [lvl.stop_roi for lvl in ORDER_STOP_LADDER_LAYA_REVERSION]
    
    for i in range(1, len(triggers)):
        assert triggers[i] > triggers[i-1], f"Trigger {i} deve ser maior que {i-1}"
        assert stops[i] > stops[i-1], f"Stop {i} deve ser estritamente maior que {i-1}"


@pytest.mark.asyncio
async def test_laya_router_threshold_84_and_mid_channel_rejection():
    """Valida que a régua de entrada mínima da Laya é >= 84 e que o centro do canal não qualifica."""
    from app.services.laya_router_service import LayaRouterService

    service = LayaRouterService()
    
    # 1. Régua mínima de entrada deve ser >= 84
    assert service.MIN_ENTRY_SCORE >= 84, f"MIN_ENTRY_SCORE deve ser no mínimo 84, obtido {service.MIN_ENTRY_SCORE}"

    # 2. Avaliação de entrada no meio do canal (diff_pct = 0.05% - dentro de [-0.35%, +0.35%])
    res_center = service.evaluate_channel_position(diff_pct=0.05, lsr=1.2, flow_regime="NEUTRAL")
    assert res_center["qualifies"] is False, "Centro de canal não deve qualificar para entrada"
    assert res_center["score"] < 84, "Score no centro do canal deve ser menor que 84"

    # 3. Avaliação no suporte com desconto real (diff_pct = -0.45%)
    res_support = service.evaluate_channel_position(diff_pct=-0.45, lsr=1.1, flow_regime="LONG_LIQUIDATION_BOTTOM")
    assert res_support["qualifies"] is True, "Suporte com desconto deve qualificar"
    assert res_support["direction"] == "LONG"
    assert res_support["score"] >= 84, "Score no suporte deve ser >= 84"

    # 4. Avaliação na resistência com exaustão real (diff_pct = +0.50%)
    res_resist = service.evaluate_channel_position(diff_pct=0.50, lsr=1.45, flow_regime="SHORT_LIQUIDATION_TOP")
    assert res_resist["qualifies"] is True, "Resistência com exaustão deve qualificar"
    assert res_resist["direction"] == "SHORT"
    assert res_resist["score"] >= 84, "Score na resistência deve ser >= 84"


@pytest.mark.asyncio
async def test_laya_symbol_cooldown_after_stop_loss():
    """Valida que símbolos em cooldown após stop loss são bloqueados de abrir novos trades."""
    from app.services.laya_router_service import LayaRouterService

    service = LayaRouterService()
    now = time.time()
    
    # Registrar stop loss para ARB
    service.record_stop_loss("ARB", cooldown_seconds=2700)
    
    assert service.is_symbol_in_cooldown("ARB") is True, "ARB deve estar em cooldown após SL"
    assert service.is_symbol_in_cooldown("SOL") is False, "SOL não deve estar em cooldown"

    # Se passarem 2701 segundos
    with patch("time.time", return_value=now + 2705):
        assert service.is_symbol_in_cooldown("ARB") is False, "ARB deve sair do cooldown após 2700s"
