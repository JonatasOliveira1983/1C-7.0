import pytest
import asyncio
import time
from services.sandbox_service import SandboxService
from services.database_service import DatabaseService, SandboxTrade

@pytest.mark.asyncio
async def test_sandbox_recalculate_realized_balance_handles_string_and_dict():
    """Valida que o recalculo do saldo realizado do Sandbox lida perfeitamente com JSON string e dict."""
    srv = SandboxService()
    
    # Mock de trades fechados com contract_meta em string e dict
    class MockTrade:
        def __init__(self, status, pnl_pct, contract_meta, leverage=15.0):
            self.status = status
            self.pnl_pct = pnl_pct
            self.contract_meta = contract_meta
            self.leverage = leverage

    mock_scalps = [
        # Trade 1: dict meta (+32.13% com $100.02 margem -> +$32.13)
        MockTrade("CLOSED_TRAILING", 32.124, {"margin": 100.02, "total_fees_usd": 1.69, "leverage": 13.0}),
        # Trade 2: JSON string meta (+32.13% com $100.02 margem -> +$32.13)
        MockTrade("CLOSED_TRAILING", 32.124, '{"margin": 100.02, "total_fees_usd": 1.69, "leverage": 13.0}'),
        # Trade 3: ACTIVE (não deve ser contado no realizado)
        MockTrade("ACTIVE", -10.0, {"margin": 100.0}),
    ]

    import unittest.mock as mock
    with mock.patch("services.database_service.database_service.get_sandbox_trades", return_value=mock_scalps):
        with mock.patch("services.database_service.database_service.get_swing_trades", return_value=[]):
            bal = await srv.recalculate_realized_balance()
            assert bal > 10000.0
            # 10000.0 + 32.13 + 32.13 = 10064.26
            assert round(bal, 2) == 10064.26
            assert srv.base_balance_cache == 10064.26
            assert srv.total_fees_paid_cache == 3.38
