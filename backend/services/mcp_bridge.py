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
            "leverage_band": "15x-20x (Piso 15X, Teto 20X)",
            "doctrine": "INSTITUTIONAL_LIQUIDITY_HUNTER"
        }
    except Exception as e:
        return {"status": "error", "message": f"Snapshot failed: {str(e)}"}


async def _tool_quarantine_symbol(symbol: str, duration_seconds: int = 7200) -> Dict[str, Any]:
    """Coloca um par em quarentena forçada impedindo novas ordens pela Laya."""
    try:
        from app.services.laya_router_service import laya_router_service
        clean = symbol.upper().replace("-USDT-SWAP", "").replace("USDT", "")
        laya_router_service.record_stop_loss(clean, direction="ALL", cooldown_seconds=duration_seconds)
        return {
            "status": "success",
            "symbol": clean,
            "action": "QUARANTINE_APPLIED",
            "duration_seconds": duration_seconds,
            "message": f"{clean} colocado em quarentena soberana por {duration_seconds} segundos (2h)."
        }
    except Exception as e:
        return {"status": "error", "message": f"Falha ao colocar em quarentena: {str(e)}"}


async def _tool_get_quarantines() -> Dict[str, Any]:
    """Lista todos os ativos atualmente em quarentena e tempo restante."""
    try:
        from app.services.laya_router_service import laya_router_service
        now = asyncio.get_event_loop().time() if hasattr(asyncio, "get_event_loop") else time.time()
        import time as _t
        now_t = _t.time()
        quarantines = {}
        for sym, expire in laya_router_service._symbol_cooldowns.items():
            remaining = max(0, int(expire - now_t))
            if remaining > 0:
                quarantines[sym] = {"remaining_seconds": remaining, "remaining_minutes": round(remaining / 60, 1)}
        return {"status": "success", "total_quarantined": len(quarantines), "quarantines": quarantines}
    except Exception as e:
        return {"status": "error", "message": f"Falha ao listar quarentenas: {str(e)}"}


async def _tool_query_rag(query: str, top_k: int = 4) -> Dict[str, Any]:
    """Consulta a inteligência semântica unificada do RAG (MASTER_ARCHITECTURE, vault_galaxy, docs)."""
    try:
        from services.rag_service import rag_service
        results = rag_service.search(query, top_k=top_k)
        return {"status": "success", "query": query, "total_matches": len(results), "matches": results}
    except Exception as e:
        return {"status": "error", "message": f"Falha na consulta RAG: {str(e)}"}


async def _tool_get_market_intel_screener(universe: str = "all") -> Dict[str, Any]:
    """Varre o universo de 507 pares da OKX ou os 30 Titãs calculando 1C-EXP, 1C-RANGE e aceleração de robôs."""
    try:
        from app.services.market_intel_engine import market_intel_engine
        from app.services.okx_universe_service import okx_universe_service
        tickers = await okx_universe_service.sync_tickers()
        min_vol = 500_000.0 if universe == "all" else 3_000_000.0
        results = market_intel_engine.scan_universal_market(tickers, min_volume_usd=min_vol, exclude_btc=True)
        if universe == "titans":
            results = [r for r in results if r["symbol"] in okx_universe_service._titans_30_altcoins]
        ignited_count = sum(1 for r in results if r.get("bot_ignition"))
        return {
            "status": "success",
            "universe": universe,
            "total_scanned": len(results),
            "ignited_count": ignited_count,
            "top_ignitions": [r for r in results if r.get("bot_ignition")][:10],
            "assets": results[:25]
        }
    except Exception as e:
        return {"status": "error", "message": f"Falha no screener de mercado: {str(e)}"}


async def _tool_get_contract_precision_audit(symbol: str) -> Dict[str, Any]:
    """Audita especificações exatas de contrato OKX (ctVal, tickSize, lotSize, minSz e quantização)."""
    try:
        from app.services.okx_universe_service import okx_universe_service
        specs = okx_universe_service.get_specs(symbol)
        quant = okx_universe_service.quantize_order_contracts(symbol, margin_usd=100.0, leverage=15.0, price=10.0)
        return {
            "status": "success",
            "symbol": symbol,
            "specs": specs,
            "simulation_100usd_15x": quant
        }
    except Exception as e:
        return {"status": "error", "message": f"Falha na auditoria de contrato: {str(e)}"}


async def _tool_viking_tree(path: str = "viking://") -> Dict[str, Any]:
    """Retorna a árvore do sistema de arquivos virtual OpenViking (resources, user/memories, agent/skills)."""
    try:
        from services.openviking_context_service import openviking_context_service
        return {
            "status": "success",
            "path": path,
            "tree": openviking_context_service.tree(path)
        }
    except Exception as e:
        return {"status": "error", "message": f"Erro OpenViking tree: {str(e)}"}


async def _tool_viking_read(uri: str, level: int = 1) -> Dict[str, Any]:
    """Lê um nó virtual OpenViking com Progressive Disclosure (0=Abstract L0, 1=Overview L1, 2=Detail L2)."""
    try:
        from services.openviking_context_service import openviking_context_service, ContextLevel
        lvl = ContextLevel(level) if level in (0, 1, 2) else ContextLevel.OVERVIEW
        content = openviking_context_service.read(uri, level=lvl)
        return {
            "status": "success" if content is not None else "not_found",
            "uri": uri,
            "level": int(lvl),
            "content": content
        }
    except Exception as e:
        return {"status": "error", "message": f"Erro OpenViking read: {str(e)}"}


async def _tool_viking_search(query: str, level: int = 1, limit: int = 5) -> Dict[str, Any]:
    """Busca estruturada no banco de dados de contexto OpenViking por regras, padrões ou casos."""
    try:
        from services.openviking_context_service import openviking_context_service, ContextLevel
        lvl = ContextLevel(level) if level in (0, 1, 2) else ContextLevel.OVERVIEW
        matches = openviking_context_service.search(query=query, level=lvl, limit=limit)
        return {
            "status": "success",
            "query": query,
            "total_matches": len(matches),
            "matches": matches
        }
    except Exception as e:
        return {"status": "error", "message": f"Erro OpenViking search: {str(e)}"}


async def _tool_viking_commit_lesson(category: str, title: str, content: str) -> Dict[str, Any]:
    """Grava um aprendizado permanente no grafo OpenViking e persiste no Obsidian Vault."""
    try:
        from services.openviking_context_service import openviking_context_service
        node = openviking_context_service.commit_lesson(category=category, title=title, content=content)
        return {
            "status": "success",
            "uri": node.uri,
            "title": node.title,
            "abstract": node.l0_abstract
        }
    except Exception as e:
        return {"status": "error", "message": f"Erro OpenViking commit: {str(e)}"}


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

        @mcp.tool()
        async def quarantine_symbol(symbol: str, duration_seconds: int = 7200) -> Dict[str, Any]:
            """Coloca um par em quarentena forçada na Laya por N segundos (padrão: 7200s / 2 horas)."""
            return await _tool_quarantine_symbol(symbol, duration_seconds)

        @mcp.tool()
        async def get_quarantines() -> Dict[str, Any]:
            """Lista todos os ativos atualmente em quarentena e o tempo restante."""
            return await _tool_get_quarantines()

        @mcp.tool()
        async def query_rag_intelligence(query: str, top_k: int = 4) -> Dict[str, Any]:
            """Consulta a inteligência semântica do RAG (arquitetura, regras, journal e histórico de trades)."""
            return await _tool_query_rag(query, top_k)

        @mcp.tool()
        async def get_market_intel_screener(universe: str = "all") -> Dict[str, Any]:
            """Varre o mercado OKX (507 pares ou Titãs) calculando 1C-EXP, 1C-RANGE e robôs ativados."""
            return await _tool_get_market_intel_screener(universe)

        @mcp.tool()
        async def get_contract_precision_audit(symbol: str) -> Dict[str, Any]:
            """Audita especificações exatas de contrato OKX (ctVal, tickSize, lotSize, minSz e quantização)."""
            return await _tool_get_contract_precision_audit(symbol)

        @mcp.tool()
        async def viking_tree(path: str = "viking://") -> Dict[str, Any]:
            """Retorna a árvore do sistema de arquivos virtual OpenViking (resources, user/memories, agent/skills)."""
            return await _tool_viking_tree(path)

        @mcp.tool()
        async def viking_read(uri: str, level: int = 1) -> Dict[str, Any]:
            """Lê um nó virtual OpenViking com Progressive Disclosure (0=Abstract L0, 1=Overview L1, 2=Detail L2)."""
            return await _tool_viking_read(uri, level)

        @mcp.tool()
        async def viking_search(query: str, level: int = 1, limit: int = 5) -> Dict[str, Any]:
            """Busca estruturada no banco de dados de contexto OpenViking por regras, padrões ou casos."""
            return await _tool_viking_search(query, level, limit)

        @mcp.tool()
        async def viking_commit_lesson(category: str, title: str, content: str) -> Dict[str, Any]:
            """Grava um aprendizado permanente no grafo OpenViking e persiste no Obsidian Vault."""
            return await _tool_viking_commit_lesson(category, title, content)
            
        logger.info("✅ [MCP] 14 ferramentas oficiais do 1Crypten registradas no MCP Server (incluindo OpenViking Context Database).")
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
                            {"name": "get_system_snapshot", "description": "Returns high-level system telemetry, active slots, and risk state."},
                            {"name": "quarantine_symbol", "description": "Forces an asset into sovereign quarantine for N seconds (default 7200s)."},
                            {"name": "get_quarantines", "description": "Lists all quarantined assets with remaining cooldown time."},
                            {"name": "query_rag_intelligence", "description": "Performs semantic search across MASTER_ARCHITECTURE, vault_galaxy, rules and docs."},
                            {"name": "viking_tree", "description": "Navigates OpenViking virtual filesystem tree (viking://)."},
                            {"name": "viking_read", "description": "Reads OpenViking node with progressive disclosure (L0 abstract, L1 overview, L2 detail)."},
                            {"name": "viking_search", "description": "Searches rules, cases and patterns in OpenViking context database."},
                            {"name": "viking_commit_lesson", "description": "Persists an episodic memory lesson to OpenViking and Obsidian Vault."}
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
