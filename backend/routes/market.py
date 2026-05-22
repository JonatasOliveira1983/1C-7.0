from fastapi import APIRouter, Depends, Header, HTTPException, Request
import logging
import asyncio
import time
import datetime
from config import settings

router = APIRouter(prefix="/api", tags=["Market"])
logger = logging.getLogger("1CRYPTEN-MARKET")

def get_services():
    services = [None] * 6
    service_names = ["BybitRest", "BybitWS", "Firebase", "SignalGen", "Captain", "Oracle"]
    
    try:
        from services.bybit_rest import bybit_rest_service
        services[0] = bybit_rest_service
        from services.bybit_ws import bybit_ws_service
        services[1] = bybit_ws_service
        from services.firebase_service import firebase_service
        services[2] = firebase_service
        from services.signal_generator import signal_generator
        services[3] = signal_generator
        from services.agents.captain import captain_agent
        services[4] = captain_agent
        from services.agents.oracle_agent import oracle_agent
        services[5] = oracle_agent
    except Exception as e:
        logger.error(f"❌ Error loading one or more services in Market Route: {e}")
        # We continue with what we have instead of returning all as None
        
    return tuple(services)

@router.get("/elite-pairs")
async def get_elite_pairs():
    try:
        bybit_rest_service, _, _, _, _, _ = get_services()
        if not bybit_rest_service: return {"symbols": ["BTCUSDT.P", "ETHUSDT.P", "SOLUSDT.P"], "count": 3}
        symbols = await bybit_rest_service.get_elite_50x_pairs()
        return {"symbols": symbols, "count": len(symbols)}
    except Exception as e:
        logger.error(f"Error fetching elite pairs: {e}")
        return {"symbols": ["BTCUSDT.P", "ETHUSDT.P", "SOLUSDT.P"], "count": 3}

@router.get("/btc/regime")
async def get_btc_regime():
    return {"regime": "BULLISH", "confidence": 0.95}

@router.get("/radar/pulse")
async def get_radar_pulse():
    try:
        _, _, firebase_service, _, _, _ = get_services()
        if not firebase_service: return {"signals": [], "decisions": [], "updated_at": 0}
        return await firebase_service.get_radar_pulse()
    except Exception as e:
        logger.error(f"Error in /radar/pulse: {e}")
        return {"signals": [], "decisions": [], "updated_at": 0}


@router.get("/radar/grid")
async def get_radar_grid():
    try:
        _, _, firebase_service, _, _, _ = get_services()
        if not firebase_service or not firebase_service.rtdb: return {}
        grid_data = await asyncio.to_thread(firebase_service.rtdb.child("market_radar").get)
        return grid_data if grid_data else {}
    except Exception as e:
        logger.error(f"Error fetching radar grid: {e}")
        return {}

@router.get("/radar/librarian")
async def get_radar_librarian():
    """V110.100: Rota REST para o Quartel General UI buscar o Historiador"""
    try:
        _, _, firebase_service, _, _, _ = get_services()
        if not firebase_service or not firebase_service.rtdb: return {"status": "error", "message": "Firebase Offline"}
        lib_data = await asyncio.to_thread(firebase_service.rtdb.child("librarian_intelligence").get)
        if not lib_data: return {"status": "success", "rankings": []}
        
        # Converte o dicionário de rankings em uma lista ordenada por win_rate
        rankings_dict = lib_data.get("top_rankings", {})
        rankings_list = sorted(rankings_dict.values(), key=lambda x: x.get("win_rate", 0), reverse=True)
        
        return {
            "status": "success",
            "rankings": rankings_list,
            "sector_analysis": lib_data.get("sector_analysis", {}),
            "last_study": lib_data.get("last_study", 0),
            "updated_at": lib_data.get("updated_at", 0),
            # [V110.42.2] Telemetria Expandida para Fallback UI
            "progress": lib_data.get("progress", 0),
            "total_assets": lib_data.get("total_assets", 0),
            "processed_count": lib_data.get("processed_count", 0),
            "current_symbol": lib_data.get("current_symbol", ""),
            "ghost_count_session": lib_data.get("ghost_count_session", 0),
            "study_status": lib_data.get("status", "IDLE")
        }
    except Exception as e:
        logger.error(f"Error fetching librarian intel: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/captain/tocaias")
async def get_captain_tocaias():
    try:
        _, _, _, _, captain_agent, _ = get_services()
        if not captain_agent: return {"active": []}
        raw_tocaias = getattr(captain_agent, 'active_tocaias', set())
        norm_tocaias = [s.replace(".P", "").replace(".p", "").upper() for s in raw_tocaias]
        return {"active": norm_tocaias}
    except Exception as e:
        logger.error(f"Error in /api/captain/tocaias: {e}")
        return {"active": []}

@router.get("/trend/{symbol}")
async def get_trend_analysis(symbol: str):
    _, _, _, signal_generator, _, _ = get_services()
    try:
        analysis = await signal_generator.get_1h_trend_analysis(symbol)
        return {
            "symbol": symbol, "trend": analysis.get("trend", "sideways"),
            "pattern": analysis.get("pattern", "none"), "trend_strength": analysis.get("trend_strength", 0),
            "sma20": analysis.get("sma20", 0), "atr": analysis.get("atr", 0),
            "accumulation_boxes": analysis.get("accumulation_boxes", []), "liquidity_zones": analysis.get("liquidity_zones", [])
        }
    except Exception as e:
        logger.error(f"Error fetching trend for {symbol}: {e}")
        return {"symbol": symbol, "trend": "sideways", "pattern": "none", "trend_strength": 0}

@router.get("/market/klines")
async def get_klines_proxy(symbol: str, interval: str = "60", limit: int = 200):
    bybit_rest_service, _, _, _, _, _ = get_services()
    try:
        int_map = {"15m": "15", "1h": "60", "4h": "240"}
        bybit_interval = int_map.get(str(interval), str(interval))
        data = await bybit_rest_service.get_klines(symbol=symbol, interval=bybit_interval, limit=limit)
        if data: data.reverse()
        return data
    except Exception as e:
        logger.error(f"Klines Proxy Error: {e}")
        return []

_SYSTEM_STATE_CACHE = {"data": None, "ts": 0}

@router.get("/system/state")
async def get_system_state():
    global _SYSTEM_STATE_CACHE
    now = time.time()
    
    # [V110.50] Short-term cache (1s) to prevent Cloud Run CPU spikes from concurrent UI tabs
    if _SYSTEM_STATE_CACHE["data"] and (now - _SYSTEM_STATE_CACHE["ts"] < 1.0):
        return _SYSTEM_STATE_CACHE["data"]
        
    try:
        # [V20.0] Safe Access to main variables to avoid circular imports during startup
        from main import sig_gen as main_sig_gen
        bybit_rest_service, bybit_ws_service, firebase_service, signal_generator, captain_agent, oracle_agent = get_services()
        
        target_sig_gen = main_sig_gen if main_sig_gen is not None else signal_generator
        
        # Safe Fallback values
        btc_price = 0
        btc_var_1h = 0
        btc_cvd = 0
        btc_adx = 0
        btc_dominance = 0
        
        if bybit_ws_service:
            try:
                btc_price = bybit_ws_service.get_current_price("BTCUSDT")
                btc_var_1h = getattr(bybit_ws_service, 'btc_variation_1h', 0)
                btc_cvd = bybit_ws_service.get_cvd_score("BTCUSDT")
            except Exception as btc_err:
                logger.warning(f"Error fetching BTC telemetry: {btc_err}")

        # 🆕 [V110.32.1] Fetch Oracle Context for REST Fallback
        oracle_status = "SECURE"
        stabilization_progress = 1.0
        if oracle_agent:
            try:
                oracle_ctx = oracle_agent.get_validated_context()
                oracle_status = oracle_ctx.get("status", "SECURE")
                # Progress calculation: 150s base
                uptime = time.time() - oracle_agent.boot_time
                stabilization_progress = min(1.0, uptime / 150.0) if oracle_status == "STABILIZING" else 1.0
                # Override ADX with Oracle validated ADX for consistency
                btc_adx = oracle_ctx.get("btc_adx", btc_adx)
                btc_dominance = oracle_ctx.get("dominance", btc_dominance)
            except Exception as orc_err:
                logger.warning(f"Error fetching Oracle context: {orc_err}")

        is_thinking = False
        if firebase_service and firebase_service.rtdb:
            try:
                # [V110.117] Proteção 504: Timeout de 2s para resposta do RTDB
                chat_status = await asyncio.wait_for(
                    asyncio.to_thread(firebase_service.rtdb.child("chat_status").get),
                    timeout=2.0
                )
                if chat_status: is_thinking = chat_status.get("is_thinking", False)
            except asyncio.TimeoutError:
                logger.warning("⏱️ [SYSTEM-STATE] RTDB Chat Status Timeout (2s). Usando fallback False.")
            except Exception as chat_err:
                logger.warning(f"Error fetching Chat Status: {chat_err}")

        # 🆕 [V110.34] Calculate Captain-Aligned Direction for REST fallback
        btc_var_15m = getattr(bybit_ws_service, 'btc_variation_15m', 0) if bybit_ws_service else 0
        effective_adx = btc_adx if btc_adx else (getattr(bybit_ws_service, 'btc_adx', 0) if bybit_ws_service else 0)
        if effective_adx >= 30:
            if btc_var_15m > 0 and btc_var_1h > 0:
                btc_direction = "UP"
            elif btc_var_15m < 0 and btc_var_1h < 0:
                btc_direction = "DOWN"
            else:
                btc_direction = "LATERAL"
        else:
            btc_direction = "LATERAL"

        res = {
            "current": getattr(target_sig_gen, 'system_state', 'PAUSED') if target_sig_gen else 'OFFLINE',
            "slots_occupied": getattr(target_sig_gen, 'occupied_count', 0) if target_sig_gen else 0,
            "message": getattr(target_sig_gen, 'system_message', 'Iniciando...') if target_sig_gen else 'Sistema Indisponível',
            "protocol": "Sniper V110.100",
            "is_thinking": is_thinking,
            "oracle_status": oracle_status,
            "oracle_message": oracle_status,
            "stabilization_progress": stabilization_progress,
            "last_reconciliation": getattr(captain_agent, 'last_reconciliation_time', 0) * 1000 if captain_agent else 0,
            "btc_price": btc_price, 
            "btc_variation_1h": btc_var_1h, 
            "btc_variation_24h": getattr(bybit_ws_service, 'btc_variation_24h', 0) if bybit_ws_service else 0,
            "btc_adx": effective_adx, 
            "decorrelation_avg": getattr(bybit_ws_service, 'decorrelation_avg', 0) if bybit_ws_service else 0,
            "btc_dominance": btc_dominance,
            "btc_var_15m": btc_var_15m,
            "btc_direction": btc_direction,
            "btc_cvd": btc_cvd, 
            "btc_drag_mode": getattr(target_sig_gen, 'btc_drag_mode', False) if target_sig_gen else False,
            "exhaustion": getattr(target_sig_gen, 'exhaustion_level', 0) if target_sig_gen else 0,
            "radar_mode": getattr(target_sig_gen, 'current_radar_mode', 'SENTINELA_STANDBY') if target_sig_gen else 'STANDBY',
            "updated_at": int(time.time() * 1000),
            "timestamp": datetime.datetime.now().isoformat()
        }
        _SYSTEM_STATE_CACHE = {"data": res, "ts": now}
        return res
    except Exception as e:
        import traceback
        logger.error(f"❌ CRITICAL ERROR in /system/state: {e}")
        logger.error(traceback.format_exc())
        err_res = {
            "current": "ERROR",
            "message": f"Erro Crítico: {str(e)}",
            "protocol": "RECOVERY-MODE",
            "updated_at": time.time() * 1000
        }
        return err_res
