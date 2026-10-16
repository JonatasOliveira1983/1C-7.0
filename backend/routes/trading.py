from fastapi import APIRouter, Depends, Header, HTTPException, Request
from typing import Optional, List
from services.auth_service import User, get_current_user
import logging
import asyncio
import datetime
import time
from config import settings

_cached_price_map = {}
_last_price_map_ts = 0.0

router = APIRouter(prefix="/api", tags=["Trading"])

logger = logging.getLogger("1CRYPTEN-TRADING")

# Imports lazy to avoid circular dependency if any
def get_services():
    from services.firebase_service import firebase_service
    from services.okx_rest import okx_rest_service
    from services.execution_protocol import execution_protocol
    from services.vault_service import vault_service
    from services.bankroll import bankroll_manager
    return firebase_service, okx_rest_service, execution_protocol, vault_service, bankroll_manager

async def verify_api_key(x_api_key: str = Header(None)):
    if settings.DEBUG:
        return True
    if x_api_key != settings.ADMIN_API_KEY:
        logger.warning(f"🔒 Security Alert: Unauthorized access attempt in Trading Route")
        raise HTTPException(status_code=403, detail="Acesso Proibido: Chave de API Inválida")
    return True

def _map_sandbox_trade_to_slot(trade, lab_type: str) -> dict:
    """[V127] Converte um trade do Sandbox (Scalping/Swing) em slot-like p/ Cockpit em PAPER."""
    if not isinstance(trade, dict):
        trade = {c.name: getattr(trade, c.name) for c in trade.__table__.columns}
    direction = str(trade.get("direction") or "LONG").upper()
    side = "Buy" if direction in ("LONG", "BUY") else "Sell"
    opened = trade.get("opened_at")
    if opened and hasattr(opened, "isoformat"):
        opened = opened.isoformat()
    meta = trade.get("contract_meta") if isinstance(trade.get("contract_meta"), dict) else {}
    ep = float(trade.get("entry_price") or 0.0)
    cp = float(trade.get("current_price") or ep)
    sl = float(trade.get("stop_loss") or trade.get("current_stop") or 0.0)
    tp = float(trade.get("target") or trade.get("target_price") or 0.0)
    if sl <= 0 and ep > 0:
        sl = round(ep * (0.975 if direction in ("LONG", "BUY") else 1.025), 4)
    if tp <= 0 and ep > 0:
        tp = round(ep * (1.050 if direction in ("LONG", "BUY") else 0.950), 4)
    raw_pnl = trade.get("pnl_pct") if trade.get("pnl_pct") is not None else trade.get("current_roi")
    pnl = float(raw_pnl or 0.0)

    return {
        "id": trade.get("id"),
        "symbol": trade.get("symbol"),
        "side": side,
        "qty": trade.get("qty") or 0,
        "entry_price": ep,
        "current_price": cp,
        "entry_margin": trade.get("entry_margin") or meta.get("margin") or 200.0,
        "current_stop": sl,
        "initial_stop": sl,
        "order_id": trade.get("id"),
        "target_price": tp,
        "leverage": trade.get("leverage") or meta.get("leverage") or settings.LEVERAGE or 15,
        "contract_meta": meta,
        "slot_type": lab_type,
        "status_risco": trade.get("status"),
        "pnl_percent": round(pnl, 2),
        "strategy": trade.get("strategy"),
        "strategy_label": trade.get("strategy"),
        "opened_at": opened or 0,
        "updated_at": opened or 0,
        "direction": direction,
        "lab": lab_type,
    }


def _map_sandbox_trade_to_history(trade, lab_type: str) -> dict:
    """[V129] Converte um trade fechado do Sandbox em formato de histórico para o Cockpit."""
    if not isinstance(trade, dict):
        trade = {c.name: getattr(trade, c.name) for c in trade.__table__.columns}
    meta = trade.get("contract_meta") if isinstance(trade.get("contract_meta"), dict) else {}
    
    exit_t = trade.get("exit_time")
    ts_str = exit_t.isoformat() if exit_t and hasattr(exit_t, "isoformat") else (exit_t or trade.get("opened_at") or 0)
    
    direction = str(trade.get("direction") or "LONG").upper()
    side = "Buy" if direction in ("LONG", "BUY") else "Sell"
    
    pnl_pct = float(trade.get("pnl_pct") or 0.0)
    margin = float(trade.get("entry_margin") or meta.get("margin") or 200.0)
    pnl_usd = (pnl_pct / 100.0) * margin
    
    return {
        "id": str(trade.get("id")),
        "symbol": trade.get("symbol"),
        "side": side,
        "qty": float(trade.get("qty") or 0.0),
        "entry_price": float(trade.get("entry_price") or 0.0),
        "exit_price": float(trade.get("exit_price") or 0.0),
        "pnl_percent": round(pnl_pct, 2),
        "pnl_usd": round(pnl_usd, 2),
        "timestamp": ts_str,
        "strategy": trade.get("strategy") or "SWING",
        "strategy_label": trade.get("strategy") or "SWING",
        "direction": direction,
        "leverage": int(trade.get("leverage") or meta.get("leverage") or settings.LEVERAGE or 15),
        "execution_mode": "PAPER",
        "lab": lab_type
    }



_last_slots_cache = None
_last_slots_ts = 0.0

@router.get("/slots")
async def get_slots():
    """[V110.999] Rota pública — lê slots globais do Postgres. Auth removida para evitar 401 com Fortress Auth."""
    global _last_slots_cache, _last_slots_ts
    now = time.time()
    if _last_slots_cache is not None and (now - _last_slots_ts < 3.5):
        return _last_slots_cache

    from services.database_service import database_service as _ds
    from services.order_projection_service import order_projection_service
    _, okx_rest_service, execution_protocol, _, _ = get_services()
    try:
        db_slots = await _ds.get_active_slots()
        slots = []
        for s in db_slots:
            if not isinstance(s, dict):
                # Fallback caso seja um objeto ORM
                s = {c.name: getattr(s, c.name) for c in s.__table__.columns}
                
            slots.append({
                "id": s.get("id"),
                "symbol": s.get("symbol"),
                "side": s.get("side"),
                "qty": s.get("qty"),
                "entry_price": s.get("entry_price"),
                "entry_margin": s.get("entry_margin"),
                "current_stop": s.get("current_stop"),
                "initial_stop": s.get("initial_stop"),
                "order_id": s.get("order_id"),
                "target_price": s.get("target_price"),
                "leverage": s.get("leverage"),
                "slot_type": s.get("slot_type") or s.get("strategy") or "SWING",
                "status_risco": s.get("status_risco"),
                "pnl_percent": s.get("pnl_percent"),
                "strategy": s.get("strategy"),
                "strategy_label": s.get("strategy_label"),
                "genesis_id": s.get("genesis_id"),
                "opened_at": s.get("opened_at").isoformat() if s.get("opened_at") and hasattr(s.get("opened_at"), "isoformat") else (s.get("opened_at") or 0),
                "updated_at": s.get("updated_at").isoformat() if s.get("updated_at") and hasattr(s.get("updated_at"), "isoformat") else (s.get("updated_at") or 0),
                "pensamento": s.get("pensamento"),
                "liq_price": s.get("liq_price"),
                "structural_target": s.get("structural_target"),
                "target_extended": s.get("target_extended"),
                "is_ranging_sniper": s.get("is_ranging_sniper"),
                "v42_tag": s.get("v42_tag"),
                "move_room_pct": s.get("move_room_pct"),
                "pattern": s.get("pattern"),
                "unified_confidence": s.get("unified_confidence"),
                "fleet_intel": s.get("fleet_intel"),
                "execution_audit": s.get("execution_audit"),
                "is_reverse_sniper": s.get("is_reverse_sniper"),
                "market_regime": s.get("market_regime"),
                "rescue_activated": s.get("rescue_activated"),
                "rescue_resolved": s.get("rescue_resolved"),
                "projection": s.get("projection")
            })

        # [V127] PAPER: espelha as ordens do Sandbox (Scalping + Swing) como slots no Cockpit
        is_paper = getattr(okx_rest_service, "execution_mode", None) == "PAPER" or getattr(settings, "OKX_EXECUTION_MODE", None) == "PAPER" or getattr(okx_rest_service, "is_mock", True)
        if is_paper:
            try:
                scalp = await _ds.get_sandbox_trades(active_only=True)
                swing = await _ds.get_swing_trades(active_only=True)
                for t in scalp:
                    slots.append(_map_sandbox_trade_to_slot(t, "SCALPING"))
                for t in swing:
                    slots.append(_map_sandbox_trade_to_slot(t, "SWING"))
            except Exception as e:
                logger.error(f"[PAPER] Erro ao mesclar ordens do Sandbox nos slots: {e}")

        # [V157] Trava de Deduplicação Rígida para Slots do Cockpit
        deduped_slots = []
        seen_slot_keys = set()
        for s in slots:
            raw_sym = str(s.get("symbol") or "").upper().strip()
            if not raw_sym:
                continue
            base = raw_sym.split("-")[0].replace("USDT", "").replace("USDC", "")
            if base in seen_slot_keys or raw_sym in seen_slot_keys:
                logger.warning(f"[DEDUP-SLOT] Ignorando slot duplicado para {raw_sym} (base: {base})")
                continue
            seen_slot_keys.add(base)
            seen_slot_keys.add(raw_sym)
            deduped_slots.append(s)
        slots = deduped_slots

        if slots:
            global _cached_price_map, _last_price_map_ts
            now_ts = time.time()
            price_map = dict(_cached_price_map) if _cached_price_map else {}
            
            # Atualiza preços a partir de WebSocket em tempo real, dados dos slots e cache
            from services.okx_ws_public import okx_ws_public_service
            for s in slots:
                sym = s.get("symbol")
                if sym:
                    clean = okx_rest_service._strip_p(sym).upper() if hasattr(okx_rest_service, "_strip_p") else sym.replace("-SWAP", "").replace("-", "").upper()
                    ws_p = okx_ws_public_service.get_current_price(sym) or okx_ws_public_service.get_current_price(clean)
                    db_p = float(s.get("current_price") or 0.0)
                    ep = float(s.get("entry_price") or 0.0)
                    cur_p = float(ws_p or db_p or ep)
                    if cur_p > 0:
                        price_map[clean] = cur_p
                        price_map[sym] = cur_p
                        s["current_price"] = cur_p
            
            _cached_price_map = price_map
            _last_price_map_ts = now_ts

            for slot in slots:
                # [V110.999] FIX: Só limpa slots sem símbolo — não zero por qty/entry_price
                if not slot.get("symbol"):
                    slot.update({
                        "symbol": None,
                        "status_risco": "IDLE",
                        "visual_status": "SCANNING",
                        "score": 0,
                        "qty": 0,
                        "entry_price": 0,
                        "pnl_percent": 0,
                        "side": None,
                        "opened_at": 0
                    })
                    continue

                if slot.get("symbol") and slot.get("entry_price", 0) > 0:
                    try:
                        slot_id = int(slot.get("id", 0))
                    except (TypeError, ValueError):
                        slot_id = 0
                    slot["slot_type"] = slot.get("slot_type") or slot.get("strategy") or "SWING"
                    entry = float(slot.get("entry_price", 0))
                    side = slot.get("side", "Buy")
                    sym_clean = okx_rest_service._strip_p(slot["symbol"])
                    live_price = price_map.get(sym_clean, 0) or price_map.get(slot["symbol"], 0) or float(slot.get("current_price") or 0)
                    if live_price > 0:
                        slot["current_price"] = live_price
                    
                    if live_price > 0 and entry > 0:
                        projection = await order_projection_service.build_projection(
                            slot,
                            current_price=live_price,
                            phase_hint="SLOT",
                            fetch_contract=False,
                        )
                        if abs(live_price - entry) > 1e-8:
                            roi = max(-500, min(5000, float(projection.get("roi_percent") or 0)))
                            projection["roi_percent"] = roi
                            slot["pnl_percent"] = round(roi, 2)
                        elif slot.get("pnl_percent") is not None and abs(float(slot.get("pnl_percent") or 0)) > 1e-6:
                            slot["pnl_percent"] = round(float(slot["pnl_percent"]), 2)
                        else:
                            slot["pnl_percent"] = 0.0
                        slot["projection"] = projection
                        if "liq_price" in projection:
                            slot["liq_price"] = projection["liq_price"]
                    
                    roi = slot.get("pnl_percent", 0)
                    phase_info = execution_protocol.get_sl_phase_info(roi, slot_data=slot)
                    slot["sl_phase"] = phase_info.get("phase", "SAFE")
                    slot["sl_phase_icon"] = "SHIELD"
                    slot["sl_phase_color"] = phase_info.get("color", "gold")
                    slot["visual_status"] = phase_info.get("phase", "SAFE")
                else:
                    slot["sl_phase"] = "IDLE"
                    slot["sl_phase_icon"] = "IDLE"
                    slot["sl_phase_color"] = "gray"
        
        _last_slots_cache = slots
        _last_slots_ts = now
        return slots
    except Exception as e:
        logger.error(f"Error fetching slots: {e}")
    
    return []  # [V111.0] Ultra-Diversification: sem slots fantasma fixos, retorna vazio se não houver posições

@router.get("/signals")
async def get_signals(min_score: int = 0, limit: int = 20):
    firebase_service, _, _, _, _ = get_services()
    try:
        signals = await firebase_service.get_recent_signals(limit=limit)
        filtered = [s for s in signals if s.get("score", 0) >= min_score]
        if not filtered:
             return [{
                "id": "forced_debug",
                "symbol": "BTCUSDT",
                "score": 95,
                "indicators": {"cvd": 12.5},
                "is_elite": True,
                "timestamp": "Now"
            }]
        return filtered
    except Exception as e:
        logger.error(f"Error fetching signals: {e}")
        return [{"id": "forced_debug", "symbol": "BTCUSDT", "score": 95, "indicators": {"cvd": 10.5}, "is_elite": True, "timestamp": "Now"}]

@router.get("/history")
async def get_history(limit: int = 50, last_timestamp: str = None, symbol: str = None, start_date: str = None, end_date: str = None, page: int = 1):
    firebase_service, okx_rest_service, _, _, _ = get_services()
    try:
        # [V129] Em PAPER mode, retornar o histórico de trades do Sandbox (Postgres)
        if okx_rest_service and okx_rest_service.execution_mode == "PAPER":
            from services.database_service import database_service as _ds
            scalp = await _ds.get_sandbox_trades(active_only=False)
            swing = await _ds.get_swing_trades(active_only=False)
            
            closed_trades = []
            for t in scalp:
                if t.status != "ACTIVE":
                    closed_trades.append(_map_sandbox_trade_to_history(t, "SCALPING"))
            for t in swing:
                if t.status != "ACTIVE":
                    closed_trades.append(_map_sandbox_trade_to_history(t, "SWING"))
                    
            closed_trades.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
            offset = (page - 1) * limit
            return closed_trades[offset : offset + limit]

        return await firebase_service.get_trade_history(
            limit=limit, 
            last_timestamp=last_timestamp,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            page=page
        )
    except Exception as e:
        logger.error(f"Error fetching trade history: {e}")
        return []

@router.delete("/history/{id}")
async def delete_history_item(id: str):
    firebase_service, okx_rest_service, _, _, _ = get_services()
    try:
        if okx_rest_service and okx_rest_service.execution_mode == "PAPER":
            # Em PAPER, apenas retornar sucesso local (não há deleção individual por enquanto)
            return {"status": "success", "message": f"Item {id} excluído com sucesso virtual (PAPER)."}
            
        success = await firebase_service.delete_trade_history_item(id)
        if success:
            return {"status": "success", "message": f"Item {id} excluído com sucesso."}
        return {"status": "error", "message": "Falha ao excluir item do histórico."}
    except Exception as e:
        logger.error(f"Error deleting trade history item: {e}")
        return {"status": "error", "message": str(e)}

@router.delete("/history/clear/all")
async def clear_all_history():
    firebase_service, okx_rest_service, _, _, _ = get_services()
    try:
        if okx_rest_service and okx_rest_service.execution_mode == "PAPER":
            from services.database_service import database_service as _ds
            await _ds.clear_sandbox_trades()
            await _ds.clear_swing_trades()
            return {"status": "success", "message": "Histórico do Sandbox limpo com sucesso (PAPER)."}

        success = await firebase_service.clear_all_trade_history()
        if success:
            return {"status": "success", "message": "Histórico do Vault limpo com sucesso."}
        return {"status": "error", "message": "Falha ao limpar histórico."}
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/history/stats")
async def get_history_stats(symbol: str = None, start_date: str = None, end_date: str = None):
    firebase_service, okx_rest_service, _, _, _ = get_services()
    try:
        if okx_rest_service and okx_rest_service.execution_mode == "PAPER":
            from services.database_service import database_service as _ds
            scalp = await _ds.get_sandbox_trades(active_only=False)
            swing = await _ds.get_swing_trades(active_only=False)
            
            closed_scalps = [t for t in scalp if t.status != "ACTIVE"]
            closed_swings = [t for t in swing if t.status != "ACTIVE"]
            
            total_count = len(closed_scalps) + len(closed_swings)
            total_pnl = 0.0
            
            for t in closed_scalps:
                pnl_pct = float(t.pnl_pct or 0.0)
                margin = float(t.contract_meta.get("margin", 200.0)) if t.contract_meta else 200.0
                total_pnl += (pnl_pct / 100.0) * margin
                
            for t in closed_swings:
                pnl_pct = float(t.pnl_pct or 0.0)
                margin = float(t.contract_meta.get("margin", 200.0)) if t.contract_meta else 200.0
                total_pnl += (pnl_pct / 100.0) * margin
                
            return {
                "total_count": total_count,
                "total_pnl": round(total_pnl, 2),
                "win_rate": 100.0 if total_pnl >= 0 else 0.0
            }

        return await firebase_service.get_trade_history_stats(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        logger.error(f"Error fetching trade stats: {e}")
        return {"total_count": 0, "total_pnl": 0.0}

@router.post("/history/report")
async def get_trade_report(payload: dict):
    trade_data = payload.get("trade_data")
    if not trade_data:
        return {"error": "Missing trade data"}
    
    symbol = trade_data.get("symbol", "Desconhecido")
    pnl = trade_data.get("pnl", 0)
    side = trade_data.get("side", "N/A")
    roi = trade_data.get("roi", 0)
    
    report = f"""**Telemetria de Combate: {symbol}**
Posição {side} encerrada com resultado de **${pnl:.2f}** ({roi:.2f}% ROI).
A justificativa primária de fechamento computada foi: `{trade_data.get('close_reason', 'N/A')}`.
A diretriz segue inalterada: Disciplina sobre a emoção."""
    return {"report": report}

@router.get("/moonbags")
async def get_moonbags(limit: int = 10):
    try:
        from services.database_service import database_service as _ds

        moonbags_list = await _ds.get_moonbags()
        # Se for None ou não for lista, garante lista vazia
        if not isinstance(moonbags_list, list):
            moonbags_list = []
        return moonbags_list[:limit]
    except Exception as e:
        logger.error(f"Error fetching moonbags: {e}")
        return []

@router.post("/nuke-paper")
async def nuke_paper_state(current_user: User = Depends(get_current_user)):
    _, okx_rest_service, _, _, bankroll_manager = get_services()
    from services.firebase_service import firebase_service
    cleared = []
    if okx_rest_service:
        okx_rest_service.paper_positions.clear()
        okx_rest_service.paper_moonbags.clear()
        okx_rest_service.paper_orders_history.clear()
        okx_rest_service.paper_balance = 100.0
        if hasattr(okx_rest_service, 'pending_closures'):
             okx_rest_service.pending_closures.clear()
        if hasattr(okx_rest_service, 'emancipating_symbols'):
             okx_rest_service.emancipating_symbols.clear()
        cleared.append("RAM deep cleanup")
        okx_rest_service._save_paper_state()
        cleared.append("disk-sync")
    if firebase_service:
        for i in range(1, 5):
            try: await firebase_service.hard_reset_slot(i, "NUKE_PAPER_API", pnl=0.0)
            except: pass
        try:
            await firebase_service.update_bankroll(100.0)
            cleared.append("banca_status_global_firestore")
        except: pass
        try:
            await asyncio.to_thread(firebase_service.rtdb.child("banca_status/status").update, {"saldo_total": 100.0, "lucro_acumulado": 0.0, "base_capital": 100.0})
            cleared.append("banca_status_rtdb")
        except: pass
        if current_user and current_user.username:
            try:
                await asyncio.to_thread(
                    firebase_service.db.collection("users").document(current_user.username).update,
                    {"bankroll_balance": 100.0}
                )
                cleared.append(f"user-{current_user.username}-bankroll")
            except Exception as e:
                logger.error(f"Error resetting Firestore user bankroll: {e}")
    return {"status": "success", "cleared": cleared}

