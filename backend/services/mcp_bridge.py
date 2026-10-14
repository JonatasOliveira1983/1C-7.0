# -*- coding: utf-8 -*-
"""
1CRYPTEN 7.0 — Model Context Protocol (MCP) Bridge
Exposes core trading, risk, and intelligence tools to the AIOS / n8n / Claude ecosystem.
Compatible with MCP SDK 2.x and 1.x.
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional

logger = logging.getLogger("1CRYPTEN-MCP")

# Try importing MCP SDK (supports both 2.x and 1.x)
mcp = None
_mcp_asgi_app = None

try:
    try:
        from mcp.server.mcpserver import MCPServer
        mcp = MCPServer(
            name="1Crypten-OKX",
            version="7.0.0",
            description="1Crypten Autonomous Trading & Intelligence System for OKX SWAP"
        )
        logger.info("🔌 [MCP] Initialized MCPServer (SDK 2.x)")
    except ImportError:
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("1Crypten-OKX")
        logger.info("🔌 [MCP] Initialized FastMCP (SDK 1.x)")
except Exception as e:
    logger.warning(f"⚠️ [MCP] MCP SDK not available: {e}")


# ---------------------------------------------------------
# TOOL DEFINITIONS
# ---------------------------------------------------------

async def _tool_get_balance() -> Dict[str, Any]:
    """Fetches unified bankroll and equity across Sandbox and OKX."""
    from services.database_service import database_service
    from services.okx_rest import okx_rest_service
    try:
        sandbox_balance = await database_service.get_sandbox_unified_balance()
        is_paper = okx_rest_service.execution_mode == "PAPER"
        return {
            "status": "success",
            "execution_mode": "PAPER" if is_paper else "REAL",
            "unified_balance_usd": round(sandbox_balance, 2),
            "simulated_base_usd": 10000.0,
            "currency": "USDT"
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to get balance: {str(e)}"}


async def _tool_get_positions() -> Dict[str, Any]:
    """Lists all active trading positions with real-time entry, stop loss, take profit and PnL."""
    from services.database_service import database_service
    try:
        scalp = await database_service.get_sandbox_trades(active_only=True)
        swing = await database_service.get_swing_trades(active_only=True)
        
        positions = []
        for t in scalp:
            positions.append({
                "id": t.id,
                "symbol": t.symbol,
                "type": "SCALPING",
                "direction": t.direction,
                "entry_price": t.entry_price,
                "current_price": t.current_price,
                "stop_loss": t.stop_loss,
                "target": t.target,
                "pnl_percent": round(t.pnl_pct or 0.0, 2),
                "opened_at": t.opened_at
            })
        for t in swing:
            positions.append({
                "id": t.id,
                "symbol": t.symbol,
                "type": "SWING",
                "direction": t.direction,
                "entry_price": t.entry_price,
                "current_price": t.current_price,
                "stop_loss": t.stop_loss,
                "target": t.target,
                "pnl_percent": round(t.pnl_pct or 0.0, 2),
                "opened_at": t.opened_at
            })
        return {"status": "success", "total_active": len(positions), "positions": positions}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get positions: {str(e)}"}


async def _tool_get_radar_signals() -> Dict[str, Any]:
    """Fetches real-time institutional whale and retail flow signals from Laya Sovereign Engine."""
    try:
        from app.services.laya_router_service import laya_sovereign_engine
        pulse = await laya_sovereign_engine.get_radar_pulse()
        return {"status": "success", "data": pulse}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get radar signals: {str(e)}"}


async def _tool_evaluate_asset(symbol: str, side: str = "BUY") -> Dict[str, Any]:
    """Evaluates entry confluence for an asset combining Laya Whale Flow and Kronos Time-Series AI."""
    try:
        from app.services.laya_flow_service import laya_flow_service
        from services.kronos_scorer import kronos_scorer
        from app.services.laya_kronos_confluence_service import laya_kronos_confluence_service
        
        clean_sym = symbol.replace("-USDT-SWAP", "").replace("USDT", "") + "USDT"
        k_side = "Buy" if side.upper() in ("BUY", "LONG") else "Sell"
        
        flow = await laya_flow_service.get_flow_radar(clean_sym)
        kronos_res = await kronos_scorer.score_signal(clean_sym, k_side)
        confluence = laya_kronos_confluence_service.evaluate_confluence(flow, kronos_res, side=side)
        
        return {
            "status": "success",
            "symbol": clean_sym,
            "side": side.upper(),
            "flow": flow,
            "kronos": kronos_res,
            "confluence": confluence
        }
    except Exception as e:
        return {"status": "error", "message": f"Evaluation failed: {str(e)}"}


async def _tool_get_system_snapshot() -> Dict[str, Any]:
    """Fetches a high-level system telemetry snapshot: market regime, master ADX, BTC direction, and fleet health."""
    try:
        from app.services.laya_router_service import laya_sovereign_engine
        from services.database_service import database_service
        
        balance = await database_service.get_sandbox_unified_balance()
        trades = await database_service.get_sandbox_trades(active_only=True)
        
        return {
            "status": "success",
            "version": "1Crypten 7.0 (V143)",
            "conductor": "LAYA SOBERANA",
            "regime_mode": getattr(laya_sovereign_engine, "regime_mode", "MEAN_REVERSION"),
            "master_adx": getattr(laya_sovereign_engine, "master_adx", 24.2),
            "unified_balance_usd": round(balance, 2),
            "active_positions_count": len(trades),
            "doctrine": "INSTITUTIONAL_LIQUIDITY_HUNTER"
        }
    except Exception as e:
        return {"status": "error", "message": f"Snapshot failed: {str(e)}"}


# Register tools on MCP server if active
if mcp is not None:
    try:
        @mcp.tool()
        async def get_balance() -> Dict[str, Any]:
            """Fetches unified bankroll and equity across Sandbox and OKX."""
            return await _tool_get_balance()

        @mcp.tool()
        async def get_positions() -> Dict[str, Any]:
            """Lists all active trading positions with real-time entry, stop loss, take profit and PnL."""
            return await _tool_get_positions()

        @mcp.tool()
        async def get_radar_signals() -> Dict[str, Any]:
            """Fetches real-time institutional whale and retail flow signals from Laya Sovereign Engine."""
            return await _tool_get_radar_signals()

        @mcp.tool()
        async def evaluate_asset(symbol: str, side: str = "BUY") -> Dict[str, Any]:
            """Evaluates entry confluence for an asset combining Laya Whale Flow and Kronos Time-Series AI."""
            return await _tool_evaluate_asset(symbol, side)

        @mcp.tool()
        async def get_system_snapshot() -> Dict[str, Any]:
            """Fetches a high-level system telemetry snapshot."""
            return await _tool_get_system_snapshot()
            
        logger.info("✅ [MCP] 5 ferramentas oficiais do 1Crypten registradas no MCP Server.")
    except Exception as _e_reg:
        logger.warning(f"⚠️ [MCP] Failed to register tools on MCP Server: {_e_reg}")


def get_asgi_app():
    """Returns the ASGI app for mounting under FastAPI /mcp."""
    global _mcp_asgi_app
    if _mcp_asgi_app is not None:
        return _mcp_asgi_app

    if mcp is not None:
        # MCP 2.x
        if hasattr(mcp, "sse_app"):
            _mcp_asgi_app = mcp.sse_app()
            try:
                from starlette.responses import JSONResponse
                from starlette.routing import Route
                async def _list_tools_endpoint(request):
                    return JSONResponse({
                        "tools": [
                            {"name": "get_balance", "description": "Fetches unified bankroll and equity across Sandbox and OKX."},
                            {"name": "get_positions", "description": "Lists all active trading positions with real-time entry, stop loss, take profit and PnL."},
                            {"name": "get_radar_signals", "description": "Fetches real-time whale & retail order flow signals from OKX Rubik."},
                            {"name": "evaluate_asset", "description": "Evaluates candidate asset entry with dual-engine Laya + Kronos."},
                            {"name": "get_system_snapshot", "description": "Returns high-level system telemetry, active slots, and risk state."}
                        ]
                    })
                _mcp_asgi_app.routes.append(Route("/tools", _list_tools_endpoint, methods=["GET"]))
            except Exception as _e_tools:
                logger.warning(f"⚠️ [MCP] Erro ao injetar /tools no sse_app: {_e_tools}")
            return _mcp_asgi_app
        # MCP 1.x
        if hasattr(mcp, "get_asgi_app"):
            _mcp_asgi_app = mcp.get_asgi_app()
            return _mcp_asgi_app
        if hasattr(mcp, "_app"):
            _mcp_asgi_app = mcp._app
            return _mcp_asgi_app

    # Fallback Starlette/FastAPI sub-app exposing MCP tools via JSON-RPC / REST
    from fastapi import FastAPI
    fallback_app = FastAPI(title="1Crypten MCP Fallback", version="7.0.0")

    @fallback_app.get("/tools")
    async def list_tools():
        return {
            "tools": [
                {"name": "get_balance", "description": "Fetches unified bankroll and equity."},
                {"name": "get_positions", "description": "Lists active trading positions."},
                {"name": "get_radar_signals", "description": "Fetches whale & retail flow signals."},
                {"name": "evaluate_asset", "description": "Evaluates entry with Laya + Kronos."},
                {"name": "get_system_snapshot", "description": "High-level telemetry snapshot."}
            ]
        }

    @fallback_app.get("/balance")
    async def balance():
        return await _tool_get_balance()

    @fallback_app.get("/positions")
    async def positions():
        return await _tool_get_positions()

    @fallback_app.get("/signals")
    async def signals():
        return await _tool_get_radar_signals()

    @fallback_app.get("/evaluate")
    async def evaluate(symbol: str = "BTCUSDT", side: str = "BUY"):
        return await _tool_evaluate_asset(symbol, side)

    @fallback_app.get("/snapshot")
    async def snapshot():
        return await _tool_get_system_snapshot()

    _mcp_asgi_app = fallback_app
    return _mcp_asgi_app
