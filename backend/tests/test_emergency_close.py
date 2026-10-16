import pytest
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_emergency_close_all_logic():
    from routes.sandbox import emergency_close_all
    
    mock_trade1 = MagicMock()
    mock_trade1.id = "trade-1"
    mock_trade1.symbol = "RENDER-USDT-SWAP"
    mock_trade1.direction = "SHORT"
    mock_trade1.entry_price = 1.95
    mock_trade1.current_price = 1.90
    mock_trade1.contract_meta = {"margin": 200.0, "leverage": 15.0}
    mock_trade1.flash_state = {"history": []}
    mock_trade1.entry_margin = 200.0
    mock_trade1.leverage = 15.0

    mock_trade2 = MagicMock()
    mock_trade2.id = "trade-2"
    mock_trade2.symbol = "FET-USDT-SWAP"
    mock_trade2.direction = "LONG"
    mock_trade2.entry_price = 0.20
    mock_trade2.current_price = 0.21
    mock_trade2.contract_meta = {"margin": 200.0, "leverage": 15.0}
    mock_trade2.flash_state = {"history": []}
    mock_trade2.entry_margin = 200.0
    mock_trade2.leverage = 15.0

    with patch("routes.sandbox.database_service.get_sandbox_trades", AsyncMock(return_value=[mock_trade1, mock_trade2])), \
         patch("routes.sandbox.database_service.get_swing_trades", AsyncMock(return_value=[])), \
         patch("routes.sandbox.database_service.update_sandbox_trade", AsyncMock()) as mock_update, \
         patch("routes.sandbox.sandbox_service._get_current_price", AsyncMock(side_effect=[1.90, 0.21])), \
         patch("routes.sandbox.sandbox_service.reset_balance_cache") as mock_reset:

        res = await emergency_close_all()
        assert res["success"] is True
        assert res["closed_count"] == 2
        assert mock_update.call_count == 2
        mock_reset.assert_called_once()
