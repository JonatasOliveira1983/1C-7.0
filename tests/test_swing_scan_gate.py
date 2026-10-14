import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, os.path.abspath("backend"))

@pytest.mark.asyncio
async def test_swing_service_blocks_new_trades_when_disabled():
    """
    Invariante: Quando SWING_SCAN_ENABLED é False, nenhuma ordem Swing pode ser aberta.
    """
    from services.sandbox_swing_service import SandboxSwingService
    from config import settings
    
    svc = SandboxSwingService()
    
    with patch.object(settings, "SWING_SCAN_ENABLED", False, create=True):
        fake_signal = {
            "symbol": "BTCUSDT",
            "side": "Buy",
            "strategy": "VELOCITY FLOW",
            "price": 60000.0,
            "id": "test_swing_block"
        }
        res = await svc._try_open_swing_trade(fake_signal)
        assert res is None, "Abertura de trade swing deve retornar None quando SWING_SCAN_ENABLED=False"

@pytest.mark.asyncio
async def test_swing_run_scan_cycle_skips_when_disabled():
    """
    Invariante: O ciclo de scan do Swing deve retornar imediatamente sem varrer o mercado quando desativado.
    """
    from services.sandbox_swing_service import SandboxSwingService
    from config import settings
    
    svc = SandboxSwingService()
    
    with patch.object(settings, "SWING_SCAN_ENABLED", False, create=True):
        with patch("services.database_service.database_service.get_swing_trades", new_callable=AsyncMock) as mock_get:
            await svc._run_scan_cycle()
            mock_get.assert_not_called()
