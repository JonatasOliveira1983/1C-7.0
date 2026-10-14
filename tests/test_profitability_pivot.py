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
    
    # Nível 1 não deve disparar em menos de 10% (evita asfixia de spread)
    assert lvl1.trigger_roi >= 10.0, f"Trigger muito baixo: {lvl1.trigger_roi}"
    assert lvl1.stop_roi >= 2.0, f"Stop de taxas insuficiente: {lvl1.stop_roi}"
    
    # Nível 2 deve travar lucro real de pelo menos 8%
    assert lvl2.stop_roi >= 8.0, f"Lucro do Nível 2 deveria ser >= 8.0%, obtido {lvl2.stop_roi}"
    
    # Alvo final deve permitir pelo menos +60% ROI
    alvo_final = ORDER_STOP_LADDER_LAYA_REVERSION[-1]
    assert alvo_final.trigger_roi >= 60.0
    assert alvo_final.stop_roi >= 45.0


def test_v146_swing_ladder_prevents_full_giveback():
    """Valida que ordens de swing com +30% ROI NUNCA voltam para o zero."""
    active_at_30 = order_projection_service.get_active_level(
        roi_percent=30.0,
        ladder=ORDER_STOP_LADDER_SWING,
        is_ranging=False,
        strategy_class="SWING"
    )
    
    assert active_at_30 is not None
    # Deve travar pelo menos 12% no bolso se atingiu 30%
    assert active_at_30.stop_roi >= 12.0, f"Deveria travar >= 12% de ROI, obtido {active_at_30.stop_roi}"


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
    """Valida que o sandbox_service capa os stops estritamente em no máximo -7.0% ROI."""
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
        # O stop ROI NUNCA pode ser mais negativo do que -3.5% (novo teto rígido de drawdown)
        assert stop_data["stop_roi"] >= -3.5, f"Stop violou o teto rígido de -3.5%: {stop_data['stop_roi']}"
        assert stop_data["stop_roi"] == pytest.approx(-3.5, abs=0.5), f"Stop esperado em torno de -3.5%: {stop_data['stop_roi']}"
