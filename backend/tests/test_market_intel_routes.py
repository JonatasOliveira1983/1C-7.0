# -*- coding: utf-8 -*-
"""
Endpoint Unit Tests: get_screener_matrix (all & titans) and get_ai_market_context
"""
import pytest
from unittest.mock import AsyncMock, patch
from backend.app.api.v1.endpoints.market_intel import get_screener_matrix, get_ai_market_context


@pytest.mark.asyncio
async def test_get_screener_matrix_titans_logic():
    mock_universe = [
        {"symbol": "ETH-USDT-SWAP", "pair": "ETHUSDT", "price": 2650.0, "high_24h": 2700.0, "low_24h": 2580.0, "change_24h": 2.5, "volume_24h_usd": 85000000.0},
        {"symbol": "SOL-USDT-SWAP", "pair": "SOLUSDT", "price": 180.0, "high_24h": 185.0, "low_24h": 172.0, "change_24h": 4.1, "volume_24h_usd": 95000000.0},
    ]

    mock_pulse = {
        "btc_climate": {
            "regime": "ALTCOIN_EXPANSION",
            "dominance": 56.5
        }
    }

    with patch("backend.app.api.v1.endpoints.market_intel.universe_service.get_tradable_universe", AsyncMock(return_value=mock_universe)), \
         patch("backend.app.api.v1.endpoints.market_intel.laya_router_service.get_pulse", return_value=mock_pulse):

        res = await get_screener_matrix(universe="titans")

        assert res["status"] == "SUCCESS"
        assert res["universe_mode"] == "titans"
        assert res["btc_climate"] == "ALTCOIN_EXPANSION"
        assert len(res["data"]) == 2
        first = res["data"][0]
        assert "symbol" in first
        assert "1c_exp" in first
        assert "1c_range" in first
        assert "setup" in first
        assert "action" in first


@pytest.mark.asyncio
async def test_get_screener_matrix_universal_507_logic():
    mock_tickers = {
        "ETH-USDT-SWAP": {"last": 2650.0, "high24h": 2700.0, "low24h": 2580.0, "open24h": 2600.0, "volume_24h_usd": 120_000_000.0},
        "BTC-USDT-SWAP": {"last": 65000.0, "high24h": 66000.0, "low24h": 64000.0, "open24h": 64500.0, "volume_24h_usd": 800_000_000.0},
        "TIA-USDT-SWAP": {"last": 6.50, "high24h": 6.60, "low24h": 6.45, "open24h": 6.10, "volume_24h_usd": 80_000_000.0},
        "ZOMBIE-USDT-SWAP": {"last": 0.01, "high24h": 0.01, "low24h": 0.01, "open24h": 0.01, "volume_24h_usd": 10_000.0},
    }

    mock_pulse = {
        "btc_climate": {
            "regime": "ALTCOIN_EXPANSION",
            "dominance": 56.5
        }
    }

    with patch("backend.app.api.v1.endpoints.market_intel.universe_service.sync_tickers", AsyncMock(return_value=mock_tickers)), \
         patch("backend.app.api.v1.endpoints.market_intel.laya_router_service.get_pulse", return_value=mock_pulse):

        res = await get_screener_matrix(universe="all", min_volume=500_000.0)

        assert res["status"] == "SUCCESS"
        assert res["universe_mode"] == "all"
        assert res["total_scanned"] == 2  # ETH e TIA (BTC excluído e ZOMBIE filtrado)
        symbols = [r["symbol"] for r in res["data"]]
        assert "TIA-USDT-SWAP" in symbols
        assert "ETH-USDT-SWAP" in symbols
        assert "BTC-USDT-SWAP" not in symbols


@pytest.mark.asyncio
async def test_get_ai_market_context_logic():
    mock_screener = {
        "status": "SUCCESS",
        "btc_climate": "ALTCOIN_EXPANSION",
        "btc_dominance": 56.5,
        "data": [
            {
                "symbol": "TIA-USDT-SWAP",
                "price": 6.50,
                "change_24h": 6.5,
                "1c_exp": 88.0,
                "1c_range": 61.5,
                "lsr": 0.95,
                "funding_rate": 0.0001,
                "setup": "MOMENTO_MOLA_COMPRESSION",
                "action": "LONG"
            }
        ]
    }

    with patch("backend.app.api.v1.endpoints.market_intel.get_screener_matrix", AsyncMock(return_value=mock_screener)):
        res = await get_ai_market_context(universe="all", top_limit=5)

        assert res["status"] == "SUCCESS"
        assert "context" in res
        ctx = res["context"]
        assert ctx["macro_climate"]["regime"] == "ALTCOIN_EXPANSION"
        assert len(ctx["top_explosive_assets"]) == 1
        assert "summary_prompt" in ctx
        assert "TIA-USDT-SWAP" in ctx["summary_prompt"]
