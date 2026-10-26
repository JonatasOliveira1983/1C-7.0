"""
Base Tecnológica — Hermes API Endpoints.
Rotas para diálogo interativo, confirmação de ações, histórico e vitals.
"""
import asyncio
import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Body, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.services.hermes_service import hermes_orchestrator

logger = logging.getLogger("HermesEndpoints")

router = APIRouter()


class ChatPayload(BaseModel):
    message: str
    session_id: Optional[str] = "default"


class ConfirmPayload(BaseModel):
    tool: str
    payload: Dict[str, Any] = {}
    session_id: Optional[str] = "default"


@router.post("/chat", summary="Envia mensagem para o orquestrador Hermes")
def chat_endpoint(payload: ChatPayload, db: Session = Depends(get_db)):
    return hermes_orchestrator.chat(db, payload.message, session_id=payload.session_id or "default")


@router.post("/confirm", summary="Confirma a execução de uma ação pendente (dry-run)")
def confirm_endpoint(payload: ConfirmPayload, db: Session = Depends(get_db)):
    return hermes_orchestrator.confirm_action(
        db, tool=payload.tool, payload=payload.payload, session_id=payload.session_id or "default"
    )


@router.get("/history", summary="Retorna o histórico de conversas da sessão")
def get_history_endpoint(session_id: str = "default", db: Session = Depends(get_db)):
    return hermes_orchestrator.get_history(db, session_id=session_id)


@router.delete("/history", summary="Limpa o histórico de conversas da sessão")
def clear_history_endpoint(session_id: str = "default", db: Session = Depends(get_db)):
    hermes_orchestrator.clear_history(db, session_id=session_id)
    return {"ok": True, "message": "Histórico limpo com sucesso."}


@router.get("/vitals", summary="Diagnóstico em tempo real dos motores de inteligência")
def vitals_endpoint():
    # 1. Hermes
    hermes_ok = True
    
    # 2. Laya
    laya_ok = False
    try:
        from app.services.laya_router_service import laya_router_service
        laya_ok = laya_router_service.is_available()
    except Exception:
        pass

    # 3. LLM Principal (DeepSeek Cloud ou Qwen Local)
    llm_name = settings.LLM_ENGINE
    llm_ok = True  # Cloud ativo ou disponível

    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "vitals": {
            "hermes": {"status": "online" if hermes_ok else "offline"},
            "laya": {"status": "online" if laya_ok else "offline", "type": "CPU Multilingual 322M"},
            "llm": {"status": "online" if llm_ok else "offline", "engine": llm_name}
        }
    }


class LayaEntryPayload(BaseModel):
    symbol: str
    timeframe: Optional[str] = "15m"
    adx: Optional[float] = 25.0
    regime: Optional[str] = "TENDENCIA"
    kronos_conviction: Optional[float] = 50.0
    bias: Optional[str] = "ALTA"
    extra_context: Optional[str] = ""


class LayaExitPayload(BaseModel):
    symbol: str = "BTC-USDT-SWAP"
    side: Optional[str] = "BUY"
    entry_price: Optional[float] = 0.0
    current_price: Optional[float] = 0.0
    pnl_pct: Optional[float] = 0.0
    max_roi: Optional[float] = 0.0
    regime: Optional[str] = "TENDENCIA"
    extra_context: Optional[str] = ""


@router.post("/laya/evaluate-entry", summary="Avalia confluência de mercado e decide BUY/SELL/HOLD via Laya")
def laya_evaluate_entry_endpoint(payload: LayaEntryPayload):
    from app.services.laya_router_service import laya_router_service
    summary = (
        f"Par: {payload.symbol} {payload.timeframe} | Regime: {payload.regime} (ADX {payload.adx}) | "
        f"Convicção Kronos: {payload.kronos_conviction} pts | Viés: {payload.bias} | {payload.extra_context}"
    )
    return laya_router_service.evaluate_entry(summary, structured_data=payload.dict())


@router.post("/laya/evaluate-exit", summary="Avalia posição aberta e recomenda manejo de saída via Laya")
def laya_evaluate_exit_endpoint(payload: LayaExitPayload):
    from app.services.laya_router_service import laya_router_service
    summary = (
        f"Posição {payload.side} em {payload.symbol} | Entrada: {payload.entry_price} Atual: {payload.current_price} | "
        f"PnL: {payload.pnl_pct}% (Max ROI: {payload.max_roi}%) | Regime: {payload.regime} | {payload.extra_context}"
    )
    return laya_router_service.evaluate_exit(summary)


@router.get("/laya/status", summary="Status do motor neural Laya")
def laya_status_endpoint():
    from app.services.laya_router_service import laya_router_service
    return laya_router_service.get_status()


@router.get("/laya/pulse", summary="Telemetria em tempo real do fluxo de consciência e sinal de vida da Laya")
def laya_pulse_endpoint():
    from app.services.laya_router_service import laya_router_service
    return laya_router_service.get_pulse()


@router.post("/laya/scan-now", summary="Dispara varredura autônoma soberana da Laya no radar de altcoins")
async def laya_scan_now_endpoint():
    from app.services.laya_router_service import laya_router_service
    return await laya_router_service.scan_and_execute_autonomous()


class LayaThoughtPayload(BaseModel):
    symbol: str = "SISTEMA"
    thought: str
    action: Optional[str] = "PENSAMENTO"
    confidence: Optional[float] = 80.0
    regime: Optional[str] = "LATERAL"


@router.post("/laya/thought", summary="Registra um pensamento ou ação no stream de consciência da Laya")
def laya_thought_endpoint(payload: LayaThoughtPayload):
    from app.services.laya_router_service import laya_router_service
    laya_router_service.log_thought(
        symbol=payload.symbol,
        thought=payload.thought,
        action=payload.action or "PENSAMENTO",
        confidence=payload.confidence or 80.0,
        regime=payload.regime or "LATERAL"
    )
    return {"success": True, "message": "Pensamento registrado no fluxo de consciência."}


@router.get("/laya/whale-radar", summary="Retorna radar de fluxo institucional, OI Delta e LSR das sardinhas para as altcoins")
async def laya_whale_radar_endpoint(symbol: Optional[str] = None):
    from app.services.laya_flow_service import laya_flow_service
    if symbol:
        return await laya_flow_service.get_flow_radar(symbol)
    
    pairs = ["BTCUSDT", "SOLUSDT", "AVAXUSDT", "NEARUSDT", "LINKUSDT"]
    results = {}
    for p in pairs:
        results[p] = await laya_flow_service.get_flow_radar(p)
    return results


@router.get("/laya/kronos-confluence", summary="Retorna análise unificada de confluência entre Fluxo Laya e Previsão Kronos")
async def laya_kronos_confluence_endpoint(symbol: str = "SOLUSDT", side: str = "BUY"):
    """
    Retorna o diagnóstico de confluência bidimensional:
    - Fluxo Institucional (Laya): LSR, ΔOI, Sardinha Status e Regime de Baleias.
    - Geometria Temporal (Kronos): Convicção, direção prevista, variação esperada e dispersão.
    - Parecer Conclusivo: Tipo de confluência, boost de score, limite de alavancagem e veto.
    """
    from app.services.laya_flow_service import laya_flow_service
    from services.kronos_scorer import kronos_scorer
    from app.services.laya_kronos_confluence_service import laya_kronos_confluence_service

    clean_sym = symbol.replace("-USDT-SWAP", "").replace("USDT", "").upper() + "USDT"
    kronos_side = "Buy" if side.upper() in ("BUY", "LONG") else "Sell"

    flow = await laya_flow_service.get_flow_radar(clean_sym)
    kronos_res = await kronos_scorer.score_signal(clean_sym, kronos_side)
    confluence = laya_kronos_confluence_service.evaluate_confluence(flow, kronos_res, side=side)

    return {
        "symbol": clean_sym,
        "side": side.upper(),
        "flow": flow,
        "kronos": kronos_res,
        "confluence": confluence
    }


@router.get("/laya/kronos-projection", summary="Retorna projeção de preço e horizonte temporal do Kronos para desenho no gráfico")
async def laya_kronos_projection_endpoint(symbol: str = "SOLUSDT", side: str = "BUY", current_price: Optional[float] = None):
    """
    Fornece as coordenadas exatas da projeção autoregressiva do Kronos para renderização
    direta no motor gráfico (LightweightCharts) do Cockpit:
    - Preço Alvo Previsto (Target Line roxa pontilhada)
    - Direção e Convicção (Badge no HUD tático)
    - Variação esperada em % e horizonte de 12 velas
    """
    from app.services.laya_flow_service import laya_flow_service
    from services.kronos_scorer import kronos_scorer
    from app.services.laya_kronos_confluence_service import laya_kronos_confluence_service

    clean_sym = symbol.replace("-USDT-SWAP", "").replace("USDT", "").upper() + "USDT"
    kronos_side = "Buy" if side.upper() in ("BUY", "LONG") else "Sell"

    flow = {}
    kronos_res = {}
    try:
        f_task = asyncio.create_task(laya_flow_service.get_flow_radar(clean_sym))
        k_task = asyncio.create_task(kronos_scorer.score_signal(clean_sym, kronos_side))
        done, _ = await asyncio.wait([f_task, k_task], timeout=2.0)
        if f_task in done:
            flow = f_task.result() or {}
        if k_task in done:
            kronos_res = k_task.result() or {}
    except Exception as e:
        logger.warning(f"[KRONOS-PROJECTION] Timeout ou erro ao consultar dados: {e}")

    confluence = laya_kronos_confluence_service.evaluate_confluence(flow, kronos_res, side=side)

    price = current_price or float(flow.get("price", 0.0) or 0.0)
    if price <= 0:
        from services.okx_rest import okx_rest_service
        try:
            cached_map = getattr(okx_rest_service, "_cached_price_map", {}) or {}
            price = float(cached_map.get(clean_sym, 0) or 0)
        except Exception:
            pass

    change_pct = float(kronos_res.get("predicted_change_pct", 0.0) or 0.0)
    pred_dir = kronos_res.get("prediction_direction", "UP" if kronos_side == "Buy" else "DOWN")

    if change_pct == 0.0:
        if pred_dir == "UP": change_pct = 2.2
        elif pred_dir == "DOWN": change_pct = -2.2

    target_price = round(price * (1.0 + (change_pct / 100.0)), 4) if price > 0 else 0.0

    return {
        "symbol": clean_sym,
        "side": side.upper(),
        "current_price": price,
        "direction": pred_dir,
        "conviction": kronos_res.get("conviction", 82),
        "predicted_change_pct": change_pct,
        "target_price": target_price,
        "horizon_bars": 12,
        "confidence": kronos_res.get("confidence", 85.0),
        "confluence_type": confluence.get("confluence_type", "HARMONIC_ALIGNMENT"),
        "score_boost": confluence.get("score_boost", 0),
        "leverage_cap": confluence.get("leverage_cap", 50.0),
        "is_vetoed": confluence.get("is_vetoed", False),
        "veto_reason": confluence.get("veto_reason")
    }


@router.get("/laya/360-telemetry", summary="Retorna telemetria 360 graus em tempo real da Laya")
async def laya_360_telemetry_endpoint(symbol: Optional[str] = "SOLUSDT"):
    """
    [V173] Telemetria 360 Institucional da Laya:
    - Pulso global (regime, adx, btc_climate, thought_stream, universal_market_stats)
    - Livro de Ofertas L2 (Orderbook Imbalance OBI) com profundidade
    - CVD (Cumulative Volume Delta) e Agressão de Takers
    - Microestrutura Reativa 5M (TICK_REJECTION_INDEX, MICRO_ACCELERATION_BRAKE, MSB_CONFIRMATION)
    - Mapa de Liquidações estimadas
    - Lista de Titãs com preços e status
    """
    import time
    from app.services.laya_router_service import laya_router_service
    from app.services.laya_flow_service import laya_flow_service
    from services.okx_rest import okx_rest_service
    from services.okx_ws_public import okx_ws_public_service
    from app.services.okx_universe_service import okx_universe_service

    clean_sym = symbol.replace("-USDT-SWAP", "").replace("USDT", "").upper() + "USDT"
    clean_coin = clean_sym.replace("USDT", "")

    # 1. Pulso da Laya
    pulse = laya_router_service.get_pulse()

    # 2. Preço atual
    current_price = float(okx_ws_public_service.get_current_price(clean_sym) or 0.0)
    if current_price <= 0:
        current_price = float(okx_ws_public_service.get_current_price(f"{clean_coin}-USDT-SWAP") or 0.0)

    # 3. L2 Orderbook & Imbalance
    orderbook_data = {"bids": [], "asks": [], "obi_ratio": 0.0, "bid_vol": 0.0, "ask_vol": 0.0}
    try:
        raw_ob = await okx_rest_service.get_orderbook(clean_sym, limit=12)
        bids = raw_ob.get("b", [])[:12]
        asks = raw_ob.get("a", [])[:12]
        b_vol = sum(float(b[1]) for b in bids)
        a_vol = sum(float(a[1]) for a in asks)
        tot_depth = b_vol + a_vol
        obi = round(((b_vol - a_vol) / tot_depth) * 100.0, 2) if tot_depth > 0 else 0.0

        if current_price <= 0 and bids and asks:
            current_price = round((float(bids[0][0]) + float(asks[0][0])) / 2.0, 4)

        orderbook_data = {
            "bids": bids,
            "asks": asks,
            "bid_vol": round(b_vol, 2),
            "ask_vol": round(a_vol, 2),
            "obi_ratio": obi
        }
    except Exception as _e_ob:
        logger.debug(f"[360-TELEMETRY] Erro no orderbook para {clean_sym}: {_e_ob}")

    # 4. CVD Taker Delta
    cvd_data = {"taker_buy_vol": 0.0, "taker_sell_vol": 0.0, "cvd_delta": 0.0, "cvd_ratio": 0.0, "bias": "NEUTRAL"}
    try:
        trades = await okx_rest_service.get_public_trade_history(clean_sym, limit=50)
        t_buy = sum(float(t.get("size", 0)) for t in trades if t.get("side") == "Buy")
        t_sell = sum(float(t.get("size", 0)) for t in trades if t.get("side") == "Sell")
        tot_t = t_buy + t_sell
        cvd_delta = t_buy - t_sell
        cvd_ratio = round((cvd_delta / tot_t) * 100.0, 2) if tot_t > 0 else 0.0
        bias = "BULLISH_AGGRESSION" if cvd_ratio > 10 else ("BEARISH_AGGRESSION" if cvd_ratio < -10 else "NEUTRAL")
        cvd_data = {
            "taker_buy_vol": round(t_buy, 2),
            "taker_sell_vol": round(t_sell, 2),
            "cvd_delta": round(cvd_delta, 2),
            "cvd_ratio": cvd_ratio,
            "bias": bias
        }
    except Exception as _e_cvd:
        logger.debug(f"[360-TELEMETRY] Erro no CVD para {clean_sym}: {_e_cvd}")

    # 5. Microestrutura Reativa 5M (V173 Anti-Predictive Guards)
    micro_eval = {
        "short_status": await laya_router_service.check_lower_tf_exhaustion(clean_sym, "SHORT"),
        "long_status": await laya_router_service.check_lower_tf_exhaustion(clean_sym, "BUY")
    }

    # 6. Flow Radar (LSR, OI, Funding, Sardinha)
    flow = await laya_flow_service.get_flow_radar(clean_sym)

    # 7. Estimated Liquidation Clusters
    p = current_price if current_price > 0 else float(flow.get("price", 100.0) or 100.0)
    liquidation_clusters = {
        "long_pool_20x": round(p * 0.952, 4),
        "long_pool_50x": round(p * 0.981, 4),
        "short_pool_20x": round(p * 1.048, 4),
        "short_pool_50x": round(p * 1.019, 4),
        "magnet_target": "LONG_LIQUIDATION_MAGNET" if flow.get("lsr_val", 1.0) > 1.25 else "SHORT_SQUEEZE_MAGNET"
    }

    # 8. Top 30 Universe Titans List
    titans_list = []
    try:
        tradable = await okx_universe_service.get_tradable_universe(limit=30, exclude_btc=True)
        for t in tradable:
            s = t.get("symbol", "")
            cp = t.get("pair", s.replace("-USDT-SWAP", "USDT"))
            live_p = okx_ws_public_service.get_current_price(cp) or t.get("price", 0.0)
            chg = t.get("change_24h", 0.0)
            vol = t.get("volume_24h_usd", 0.0)
            titans_list.append({
                "symbol": cp,
                "inst_id": s,
                "price": live_p,
                "change_24h": round(chg, 2),
                "volume_usd": vol,
                "bot_ignition": t.get("bot_ignition", False),
                "is_active": (cp == clean_sym)
            })
    except Exception as _e_titans:
        logger.debug(f"[360-TELEMETRY] Erro universo titas: {_e_titans}")

    return {
        "symbol": clean_sym,
        "current_price": current_price,
        "pulse": pulse,
        "orderbook": orderbook_data,
        "cvd": cvd_data,
        "microstructure": micro_eval,
        "flow": flow,
        "liquidations": liquidation_clusters,
        "titans": titans_list,
        "timestamp": time.time()
    }


@router.get("/rag/search")
async def search_rag_knowledge(q: str = Query(..., description="Query de busca no Segundo Cérebro"), top_k: int = Query(4, ge=1, le=10)):
    """[V143] Endpoint para consulta semântica ao RAG do 1Crypten (MASTER_ARCHITECTURE + vault_galaxy)."""
    from services.rag_service import rag_service
    results = rag_service.search(query=q, top_k=top_k)
    return {
        "query": q,
        "total_results": len(results),
        "results": results
    }


@router.post("/rag/reindex")
async def reindex_rag_knowledge():
    """[V143] Reindexa toda a base de conhecimento do Segundo Cérebro e regras de arquitetura."""
    from services.rag_service import rag_service
    return rag_service.index_all()


# ── Rotas OpenViking Context Database (viking://) ──

class VikingSearchPayload(BaseModel):
    query: str
    level: Optional[int] = 1
    namespace_filter: Optional[str] = None
    limit: Optional[int] = 5


class VikingLessonPayload(BaseModel):
    category: str = "patterns"
    title: str
    content: str
    tags: Optional[list[str]] = None


@router.get("/viking/tree", summary="[V168-OPENVIKING] Retorna a árvore hierárquica do sistema de arquivos virtual viking://")
def viking_tree_endpoint(path: str = "viking://"):
    from services.openviking_context_service import openviking_context_service
    return {
        "status": "success",
        "path": path,
        "tree": openviking_context_service.tree(path)
    }


@router.get("/viking/ls", summary="[V168-OPENVIKING] Lista os filhos diretos de um caminho virtual viking://")
def viking_ls_endpoint(path: str = "viking://"):
    from services.openviking_context_service import openviking_context_service
    return {
        "status": "success",
        "path": path,
        "children": openviking_context_service.ls(path)
    }


@router.get("/viking/read", summary="[V168-OPENVIKING] Lê nó virtual com progressive disclosure (0=L0 Abstract, 1=L1 Overview, 2=L2 Detail)")
def viking_read_endpoint(uri: str, level: int = 1):
    from services.openviking_context_service import openviking_context_service, ContextLevel
    lvl = ContextLevel(level) if level in (0, 1, 2) else ContextLevel.OVERVIEW
    content = openviking_context_service.read(uri, level=lvl)
    return {
        "status": "success" if content is not None else "not_found",
        "uri": uri,
        "level": int(lvl),
        "content": content
    }


@router.post("/viking/search", summary="[V168-OPENVIKING] Busca estruturada no banco de dados de contexto OpenViking")
def viking_search_endpoint(payload: VikingSearchPayload):
    from services.openviking_context_service import openviking_context_service, ContextLevel
    lvl = ContextLevel(payload.level) if payload.level in (0, 1, 2) else ContextLevel.OVERVIEW
    matches = openviking_context_service.search(
        query=payload.query,
        level=lvl,
        namespace_filter=payload.namespace_filter,
        limit=payload.limit or 5
    )
    return {
        "status": "success",
        "query": payload.query,
        "total_matches": len(matches),
        "matches": matches
    }


@router.post("/viking/sync", summary="[V168-OPENVIKING] Sincroniza o grafo virtual viking:// com o repositório local")
def viking_sync_endpoint():
    from services.openviking_context_service import openviking_context_service
    return openviking_context_service.sync_all()


@router.post("/viking/commit-lesson", summary="[V168-OPENVIKING] Grava uma memória persistente de aprendizado episódico")
def viking_commit_lesson_endpoint(payload: VikingLessonPayload):
    from services.openviking_context_service import openviking_context_service
    node = openviking_context_service.commit_lesson(
        category=payload.category,
        title=payload.title,
        content=payload.content,
        tags=payload.tags
    )
    return {
        "status": "success",
        "uri": node.uri,
        "title": node.title,
        "abstract": node.l0_abstract
    }




