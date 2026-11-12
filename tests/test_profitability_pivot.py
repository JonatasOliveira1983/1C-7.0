# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path
import pytest

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.order_projection_service import (
    order_projection_service,
    ORDER_STOP_LADDER_LAYA_REVERSION,
    ORDER_STOP_LADDER_SWING,
    ORDER_STOP_LADDER_SCALPING
)


def test_v146_laya_reversion_rr_asymmetry():
    """Valida que a escadinha da Laya possui R:R >= 2:1 positivo e protege contra asfixia precoce."""
    lvl1 = ORDER_STOP_LADDER_LAYA_REVERSION[0]
    lvl2 = ORDER_STOP_LADDER_LAYA_REVERSION[1]
    
    # Nível 1 não deve disparar em menos de 25% em 50x (evita asfixia de spread)
    assert lvl1.trigger_roi >= 25.0, f"Trigger muito baixo: {lvl1.trigger_roi}"
    assert lvl1.stop_roi >= 5.0, f"Stop de taxas insuficiente: {lvl1.stop_roi}"
    
    # Nível 2 deve travar lucro real de pelo menos 25%
    assert lvl2.stop_roi >= 25.0, f"Lucro do Nível 2 deveria ser >= 25.0%, obtido {lvl2.stop_roi}"
    
    # Alvo final deve permitir pelo menos +60% ROI
    alvo_final = ORDER_STOP_LADDER_LAYA_REVERSION[-1]
    assert alvo_final.trigger_roi >= 60.0
    assert alvo_final.stop_roi >= 45.0


def test_v146_swing_ladder_prevents_full_giveback():
    """Valida que ordens de swing com +35% ROI (Degrau 1 Taxas OKX V212) NUNCA voltam para o zero."""
    active_at_35 = order_projection_service.get_active_level(
        roi_percent=35.0,
        ladder=ORDER_STOP_LADDER_SWING,
        is_ranging=False,
        strategy_class="SWING"
    )
    
    assert active_at_35 is not None
    # Deve travar pelo menos 7% no bolso se atingiu 35% (degrau 1 protetivo de taxas)
    assert active_at_35.stop_roi >= 7.0, f"Deveria travar >= 7% de ROI, obtido {active_at_35.stop_roi}"


def test_v146_never_give_back_invariant():
    """Invariante Never Give Back: os stops dos níveis só sobem, nunca recuam."""
    for name, ladder in [
        ("LAYA_REVERSION", ORDER_STOP_LADDER_LAYA_REVERSION),
        ("SWING", ORDER_STOP_LADDER_SWING),
        ("SCALPING", ORDER_STOP_LADDER_SCALPING)
    ]:
        for i in range(1, len(ladder)):
            prev = ladder[i-1]
            curr = ladder[i]
            assert curr.trigger_roi > prev.trigger_roi, f"[{name}] Trigger não é estritamente crescente"
            assert curr.stop_roi > prev.stop_roi, f"[{name}] Stop não é estritamente crescente (Never Give Back violado)"


@pytest.mark.asyncio
async def test_v146_sandbox_stop_capping():
    """Valida que o sandbox_service capa os stops estruturais no teto institucional (-18.0% ROI em 15x)."""
    from services.sandbox_service import sandbox_service
    from unittest.mock import AsyncMock, patch
    
    # Mock de stop estrutural muito largo (-15% de ROI)
    # Com 15x, preço de entrada 100.0, stop 99.0 = -15% de ROI
    with patch.object(sandbox_service, '_get_30m_structural_stop', new=AsyncMock(return_value=99.0)):
        stop_data = await sandbox_service._calculate_adaptive_stop(
            symbol="BTC-USDT-SWAP",
            entry_price=100.0,
            side="BUY",
            contract_meta={"leverage": 15.0, "tickSize": 0.01},
            is_ranging=True
        )
        
        assert "stop_roi" in stop_data
        # O stop ROI aprovado deve respeitar o teto limite de -18.0%
        assert stop_data["stop_roi"] >= -18.0, f"Stop violou o teto de -18.0%: {stop_data['stop_roi']}"
        assert stop_data["stop_roi"] == pytest.approx(-15.0, abs=0.5), f"Stop esperado em torno de -15.0%: {stop_data['stop_roi']}"
