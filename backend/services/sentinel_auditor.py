import asyncio
import time
import logging
from typing import Dict, Any, List, Optional
from services.firebase_service import firebase_service
from services.okx_rest import okx_rest_service
from services.database_service import database_service
from services.bankroll import bankroll_manager
from config import settings

logger = logging.getLogger("SentinelAuditor")

class SentinelAuditor:
    def __init__(self):
        self.heartbeats: Dict[str, float] = {}
        self.last_reconciliation_at: float = 0.0
        self.divergences_detected: int = 0
        self.auto_healings: List[Dict[str, Any]] = []
        self.is_active: bool = True
        self._lock = asyncio.Lock()

    def record_heartbeat(self, module_name: str):
        """[V126] Registra o batimento cardíaco (liveness) de um loop operacional."""
        self.heartbeats[module_name] = time.time()
        # logger.debug(f"💓 [SENTINEL-HEARTBEAT] {module_name} está ativo.")

    def get_health_status(self) -> dict:
        """[V126] Retorna o status de integridade de todos os loops monitorados."""
        now = time.time()
        status_map = {}
        is_healthy = True

        expected_modules = ["signal_generator", "portfolio_guardian"]
        if okx_rest_service.execution_mode == "PAPER":
            expected_modules.append("paper_execution_loop")
        else:
            expected_modules.append("real_execution_loop")

        for module in expected_modules:
            last_ts = self.heartbeats.get(module, 0)
            if last_ts == 0:
                status_map[module] = {"status": "STANDBY", "last_heartbeat_seconds_ago": -1}
            elif now - last_ts > 45.0:
                status_map[module] = {"status": "INACTIVE", "last_heartbeat_seconds_ago": round(now - last_ts, 1)}
                is_healthy = False
            else:
                status_map[module] = {"status": "ACTIVE", "last_heartbeat_seconds_ago": round(now - last_ts, 1)}

        return {
            "status": "HEALTHY" if is_healthy else "DEGRADED",
            "timestamp": int(now),
            "monitors": status_map
        }

    async def start(self):
        """Inicia o loop assíncrono isolado do Sentinela."""
        logger.info("🛡️ [SENTINEL] Sentinel Auditor Core ativado e rodando...")
        asyncio.create_task(self._reconciliation_loop())

    async def _reconciliation_loop(self):
        """Loop de varredura tríplice a cada 20 segundos."""
        await asyncio.sleep(5)  # Delay inicial para o boot estável do sistema
        while self.is_active:
            try:
                self.record_heartbeat("sentinel_auditor")
                await self.reconcile()
            except Exception as e:
                logger.error(f"❌ [SENTINEL-RECONCILE-LOOP] Erro crítico no loop de reconciliação: {e}")
            await asyncio.sleep(20)

    async def reconcile(self):
        """Executa a reconciliação tríplice determinística."""
        async with self._lock:
            now = time.time()
            self.last_reconciliation_at = now
            
            # 1. Pega slots no banco (Firestore/Postgres)
            firestore_slots = await firebase_service.get_active_slots(force_refresh=True)
            if firestore_slots is None:
                firestore_slots = []
            
            # 2. Pega posições na exchange (real ou paper)
            exchange_positions = await okx_rest_service.get_active_positions()
            if exchange_positions is None:
                exchange_positions = []

            # 3. Mapeamentos por símbolo limpo (remover .P e formatar)
            slots_by_symbol = {}
            for s in firestore_slots:
                sym = s.get("symbol")
                if sym:
                    clean_sym = okx_rest_service._strip_p(sym).upper()
                    slots_by_symbol[clean_sym] = s

            positions_by_symbol = {}
            for p in exchange_positions:
                sym = p.get("symbol")
                if sym:
                    clean_sym = okx_rest_service._strip_p(sym).upper()
                    positions_by_symbol[clean_sym] = p

            # -----------------------------------------------------------------
            # FASE 1: CASO C/D - INCONSISTÊNCIA CRÍTICA (Linha 4 - Ativos Diferentes no mesmo Slot)
            # -----------------------------------------------------------------
            # Executado primeiro para evitar que conflitos de ativos no mesmo slot
            # sejam interpretados incorretamente como posições órfãs separadas.
            # -----------------------------------------------------------------
            for s in firestore_slots:
                slot_id = s.get("id")
                slot_sym = s.get("symbol")
                if not slot_sym:
                    continue

                clean_slot_sym = okx_rest_service._strip_p(slot_sym).upper()
                
                # Procura se há posição na exchange associada ao ID deste slot
                pos_in_slot = None
                for p in exchange_positions:
                    p_slot_id = p.get("slot_id")
                    if p_slot_id == slot_id:
                        pos_in_slot = p
                        break
                
                if pos_in_slot:
                    clean_pos_sym = okx_rest_service._strip_p(pos_in_slot.get("symbol", "")).upper()
                    if clean_pos_sym != clean_slot_sym:
                        logger.warning(
                            f"🚨 [SENTINEL-INCONSISTÊNCIA] Conflito Crítico no Slot {slot_id}: "
                            f"Banco={clean_slot_sym} vs. Corretora/RAM={clean_pos_sym}!"
                        )

                        # Auto-Cura: Protocolo de Consulta da Ordem de Origem
                        self.divergences_detected += 1
                        
                        # 1. Consulta gênese para verificar se a posição física tem registro legítimo
                        genesis_legit = False
                        try:
                            genesis_id = pos_in_slot.get("genesis_id") or ""
                            if genesis_id:
                                doc_genesis = await firebase_service.get_order_genesis(genesis_id)
                                if doc_genesis and doc_genesis.get("symbol"):
                                    genesis_legit = True
                            
                            # Fallback: se não tiver genesis_id direto, busca em recent signals
                            if not genesis_legit:
                                recent_signals = await firebase_service.get_recent_signals(limit=20)
                                for sig in recent_signals:
                                    sig_sym = okx_rest_service._strip_p(sig.get("symbol", "")).upper()
                                    if sig_sym == clean_pos_sym:
                                        genesis_legit = True
                                        break
                        except Exception as e_gen:
                            logger.error(f"Error checking genesis validity: {e_gen}")

                        # 2. Se legítimo: Corrige o Firestore de forma autônoma
                        if genesis_legit:
                            logger.info(
                                f"🧬 [SENTINEL-AUTO-HEAL] Origem confirmada para {clean_pos_sym} (RG legítimo). "
                                f"Corrigindo Firestore de forma autônoma e mantendo o trade rodando..."
                            )
                            self.auto_healings.append({
                                "ts": now,
                                "type": "INCONSISTENCY_GENESIS_HEAL",
                                "symbol": clean_pos_sym,
                                "slot_id": slot_id,
                                "details": f"Firestore corrigido de {clean_slot_sym} para {clean_pos_sym} após validação de gênese legítima."
                            })
                            try:
                                entry_p = float(pos_in_slot.get("avgPrice", 0))
                                qty_val = float(pos_in_slot.get("size", 0))
                                leverage = float(pos_in_slot.get("leverage", 50))
                                margin = (qty_val * entry_p) / leverage if leverage > 0 else 0
                                
                                updated_slot_data = {
                                    "symbol": clean_pos_sym + ".P",
                                    "side": pos_in_slot.get("side", "Buy"),
                                    "qty": qty_val,
                                    "entry_price": entry_p,
                                    "entry_margin": round(margin, 4),
                                    "current_stop": float(pos_in_slot.get("stopLoss", 0)),
                                    "initial_stop": float(pos_in_slot.get("stopLoss", 0)),
                                    "genesis_id": pos_in_slot.get("genesis_id") or f"SNT-{int(now)}-{clean_pos_sym[:4]}",
                                    "target_price": float(pos_in_slot.get("takeProfit", 0)),
                                    "status_risco": "ATIVO",
                                    "pensamento": "🚑 Re-sincronizado e corrigido com sucesso pelo Sentinel Auditor.",
                                    "timestamp_last_update": now
                                }
                                await firebase_service.update_slot(slot_id, updated_slot_data)
                                
                                # Atualiza o estado em memória para que o Caso A e Caso B saibam que está em sincronia
                                slots_by_symbol.pop(clean_slot_sym, None)
                                slots_by_symbol[clean_pos_sym] = {**s, **updated_slot_data}
                                
                            except Exception as e_corr:
                                logger.error(f"❌ [SENTINEL] Falha ao corrigir slot {slot_id} para {clean_pos_sym}: {e_corr}")
                        
                        # 3. Se fantasma (sem rastro): Limpa banco e protege passivamente com Stop Loss
                        else:
                            logger.warning(
                                f"👻 [SENTINEL-ALERT] Ordem FANTASMA detectada na exchange: {clean_pos_sym} no Slot {slot_id}! "
                                f"Executando encerramento de proteção passiva (Stop Loss no Break Even)..."
                            )
                            self.auto_healings.append({
                                "ts": now,
                                "type": "INCONSISTENCY_GHOST_HEAL",
                                "symbol": clean_pos_sym,
                                "slot_id": slot_id,
                                "details": f"Ordem fantasma detectada. Slot do banco purgado. Stop Loss de proteção definido na OKX/RAM."
                            })
                            
                            # Limpa o slot do banco para liberar vaga
                            try:
                                await firebase_service.hard_reset_slot(slot_id, reason="Sentinel Auto-Cura: Purga de Ordem Fantasma")
                                
                                # Atualiza o estado em memória
                                slots_by_symbol.pop(clean_slot_sym, None)
                                
                            except Exception as e_purge:
                                logger.error(f"❌ [SENTINEL] Falha ao purgar slot fantasma {slot_id}: {e_purge}")

                            # Atualiza Stop Loss físico diretamente na exchange para Break Even ou preço atual para saída passiva
                            try:
                                entry_p = float(pos_in_slot.get("avgPrice", 0))
                                current_p = await slot_operator_price_fallback(pos_in_slot.get("symbol"))
                                
                                side_norm = pos_in_slot.get("side", "Buy").lower()
                                if side_norm == "buy":
                                    preventive_sl = entry_p if current_p >= entry_p else current_p
                                else:
                                    preventive_sl = entry_p if current_p <= entry_p else current_p
                                
                                sl_result = await okx_rest_service.set_trading_stop(
                                    category="linear",
                                    symbol=pos_in_slot.get("symbol"),
                                    stopLoss=str(preventive_sl),
                                    side=pos_in_slot.get("side")
                                )
                                success = (sl_result.get("retCode") == 0) if isinstance(sl_result, dict) else False
                                if success:
                                    logger.info(
                                        f"🛡️ [SENTINEL-PROTEÇÃO-PASSIVA] Stop Loss de proteção passiva definido "
                                        f"com sucesso para {clean_pos_sym} @ ${preventive_sl:.6f}."
                                    )
                                
                                # Remove de positions_by_symbol para que o Caso B não tente adotá-la na mesma rodada
                                positions_by_symbol.pop(clean_pos_sym, None)
                                
                            except Exception as e_protect:
                                logger.error(f"❌ [SENTINEL] Falha ao aplicar stop preventivo na exchange para {clean_pos_sym}: {e_protect}")

            # -----------------------------------------------------------------
            # FASE 2: CASO A - POSIÇÃO ÓRFÃ NO BANCO (Exchange Vazia, Banco com Slot ativo)
            # -----------------------------------------------------------------
            for clean_sym, slot in list(slots_by_symbol.items()):
                if clean_sym not in positions_by_symbol:
                    opened_at = slot.get("opened_at", 0)
                    from datetime import datetime
                    if isinstance(opened_at, datetime):
                        opened_at_ts = opened_at.timestamp()
                    elif isinstance(opened_at, (int, float)):
                        opened_at_ts = float(opened_at)
                    else:
                        opened_at_ts = 0.0

                    if 0 <= (now - opened_at_ts) < 15.0:
                        continue  # Dá um grace period de 15s para a criação se consolidar
                    
                    slot_id = slot.get("id")
                    logger.warning(
                        f"🚑 [SENTINEL-AUTO-HEAL] Posição órfã no banco detectada: {clean_sym} (Slot {slot_id}). "
                        f"Encerrando slot deterministicamente e registrando no Vault..."
                    )
                    
                    self.divergences_detected += 1
                    self.auto_healings.append({
                        "ts": now,
                        "type": "ORPHAN_BANK_HEAL",
                        "symbol": clean_sym,
                        "slot_id": slot_id,
                        "details": "Posição fechada na exchange/RAM. Slot de banco purgado e arquivado."
                    })
                    
                    try:
                        # Extrai metadados do slot e calcula PnL residual com base no preço de mercado
                        side = slot.get("side", "Buy")
                        entry_price = float(slot.get("entry_price") or 0)
                        qty = float(slot.get("qty") or 0)
                        entry_margin = float(slot.get("entry_margin") or 0)
                        leverage = float(slot.get("leverage") or 50)
                        genesis_id = slot.get("genesis_id") or f"SNT-{int(now)}-{clean_sym[:4]}"
                        
                        exit_price = await slot_operator_price_fallback(clean_sym)
                        if exit_price <= 0:
                            # Fallback para o stop atual do slot se não obtiver o ticker
                            exit_price = float(slot.get("current_stop") or entry_price)
                        
                        pnl_percent = 0.0
                        pnl_val = 0.0
                        if entry_price > 0 and exit_price > 0:
                            if side.lower() in ["buy", "long"]:
                                price_diff_pct = (exit_price - entry_price) / entry_price
                            else:
                                price_diff_pct = (entry_price - exit_price) / entry_price
                            pnl_percent = round(price_diff_pct * leverage * 100, 2)
                            pnl_val = round(entry_margin * (pnl_percent / 100), 4)

                        reason = f"Sentinel Auto-Cura: Posição órfã encerrada na corretora."
                        
                        trade_data = {
                            "symbol": slot.get("symbol") or (clean_sym + ".P"),
                            "side": side,
                            "qty": qty,
                            "entry_price": entry_price,
                            "exit_price": exit_price,
                            "entry_margin": entry_margin,
                            "leverage": leverage,
                            "pnl": pnl_val,
                            "pnl_percent": pnl_percent,
                            "final_roi": pnl_percent,
                            "genesis_id": genesis_id,
                            "slot_id": slot_id,
                            "slot_type": slot.get("slot_type", "BLITZ_30M"),
                            "opened_at": slot.get("opened_at") or now,
                            "closed_at": now,
                            "close_reason": reason,
                            "pensamento": slot.get("pensamento", "🚑 Posição órfã encerrada e arquivada pelo Sentinel Auditor.")
                        }

                        await firebase_service.hard_reset_slot(
                            slot_id, 
                            reason=reason,
                            pnl=pnl_val,
                            trade_data=trade_data
                        )
                    except Exception as he:
                        logger.error(f"❌ [SENTINEL] Falha ao curar slot órfão {slot_id}: {he}")

            # -----------------------------------------------------------------
            # FASE 3: CASO B - POSIÇÃO ÓRFÃ NA EXCHANGE (Exchange Ativa, Banco Vazio)
            # -----------------------------------------------------------------
            for clean_sym, pos in list(positions_by_symbol.items()):
                # Ignora se for emancipada (Moonbag), pois Moonbags não ocupam slots táticos normais
                is_emancipated = pos.get("status") == "EMANCIPATED"
                
                if is_emancipated:
                    continue

                if clean_sym not in slots_by_symbol:
                    # Grace period para aberturas recentes (evita conflito enquanto o Captain escreve no Firestore)
                    opened_at = float(pos.get("opened_at", 0)) if pos.get("opened_at") else 0
                    if opened_at > 0 and 0 <= (now - opened_at) < 15.0:
                        continue
                    
                    # Verifica se o ativo está registrado como Moonbag no Firestore
                    moonbags = await firebase_service.get_moonbags()
                    if any(okx_rest_service._strip_p(m.get("symbol", "")).upper() == clean_sym for m in moonbags):
                        continue # É uma Moonbag legítima no banco, ignorar do slot tático

                    # Só adota a posição se ela tiver origem legítima no sistema (Genesis ID registrado)
                    genesis_legit = False
                    genesis_id = pos.get("genesis_id") or ""
                    try:
                        if genesis_id:
                            doc_genesis = await firebase_service.get_order_genesis(genesis_id)
                            if doc_genesis and doc_genesis.get("symbol"):
                                genesis_legit = True
                        
                        if not genesis_legit:
                            recent_signals = await firebase_service.get_recent_signals(limit=20)
                            for sig in recent_signals:
                                sig_sym = okx_rest_service._strip_p(sig.get("symbol", "")).upper()
                                if sig_sym == clean_sym:
                                    genesis_legit = True
                                    break
                    except Exception as e_gen:
                        logger.error(f"Error checking genesis validity in Caso B: {e_gen}")

                    if not genesis_legit:
                        # Posição fantasma sem slot no banco. Ignora adoção para evitar re-adoção ou adoção indesejada.
                        logger.warning(f"⚠️ [SENTINEL] Ignorando adoção de posição fantasma {clean_sym} na exchange (sem gênese).")
                        continue

                    logger.warning(
                        f"🚑 [SENTINEL-AUTO-HEAL] Posição órfã na exchange detectada: {clean_sym}. "
                        f"Tentando alocar slot tático de auto-cura..."
                    )

                    # Auto-Cura: Encontra um slot tático fisicamente vazio no banco
                    slot_id = None
                    for s in firestore_slots:
                        if not s.get("symbol"):
                            slot_id = s.get("id")
                            break

                    if slot_id:
                        self.divergences_detected += 1
                        self.auto_healings.append({
                            "ts": now,
                            "type": "ORPHAN_EXCHANGE_HEAL",
                            "symbol": clean_sym,
                            "slot_id": slot_id,
                            "details": "Posição órfã na exchange adotada e slot tático recriado."
                        })
                        try:
                            # Reconstruir metadados mínimos do slot
                            entry_price = float(pos.get("avgPrice", 0))
                            qty = float(pos.get("size", 0))
                            leverage = float(pos.get("leverage", 50))
                            margin = (qty * entry_price) / leverage if leverage > 0 else 0
                            
                            await firebase_service.update_slot(slot_id, {
                                "symbol": clean_sym + ".P",
                                "side": pos.get("side", "Buy"),
                                "qty": qty,
                                "entry_price": entry_price,
                                "entry_margin": round(margin, 4),
                                "current_stop": float(pos.get("stopLoss", 0)),
                                "initial_stop": float(pos.get("stopLoss", 0)),
                                "genesis_id": pos.get("genesis_id") or f"SNT-{int(now)}-{clean_sym[:4]}",
                                "target_price": float(pos.get("takeProfit", 0)),
                                "leverage": leverage,
                                "slot_type": "BLITZ_30M",
                                "status_risco": "ATIVO",
                                "pnl_percent": 0.0,
                                "pensamento": "🚑 Posição órfã adotada e estabilizada pelo Sentinel Auditor.",
                                "opened_at": opened_at or now,
                                "timestamp_last_update": now
                            })
                            logger.info(f"✅ [SENTINEL-AUTO-HEAL] Posição órfã {clean_sym} adotada com sucesso no Slot {slot_id}.")
                        except Exception as e_adopt:
                            logger.error(f"❌ [SENTINEL] Falha ao adotar posição órfã {clean_sym}: {e_adopt}")
                    else:
                        logger.error(f"❌ [SENTINEL-CAP] Não há slots livres para adotar a posição órfã {clean_sym}!")

            # -----------------------------------------------------------------
            # MÁQUINA DE ESTADOS: PROTOCOLO "IRON SWEEP" (GENESIS TIMEOUT)
            # Se um sinal foi emitido mas não preenchido em 120s, purga
            # -----------------------------------------------------------------
            # Em modo Paper, podemos monitorar tentativas de abertura travadas
            for (pending_sym, pending_slot), start_ts in list(bankroll_manager.pending_slots.items()):
                if now - start_ts > 120.0:
                    logger.warning(
                        f"🛡️ [SENTINEL-IRON-SWEEP] Genesis Timeout (120s) atingido para {pending_sym} no Slot {pending_slot}! "
                        f"Executando varredura preventiva e liberação automática de slot..."
                    )
                    self.divergences_detected += 1
                    self.auto_healings.append({
                        "ts": now,
                        "type": "IRON_SWEEP_TIMEOUT",
                        "symbol": pending_sym,
                        "slot_id": pending_slot,
                        "details": "Sinal travado em envio por mais de 120s. Slot liberado e ordens pendentes canceladas preventivamente."
                    })
                    # 1. Remove da RAM do bankroll
                    bankroll_manager.pending_slots.pop((pending_sym, pending_slot), None)
                    # 2. Cancela qualquer ordem residual
                    try:
                        await okx_rest_service.close_position(
                            symbol=pending_sym + ".P",
                            side="Buy", # tenta ambas por segurança
                            qty=0,
                            reason="SENTINEL_IRON_SWEEP_TIMEOUT"
                        )
                        await okx_rest_service.close_position(
                            symbol=pending_sym + ".P",
                            side="Sell",
                            qty=0,
                            reason="SENTINEL_IRON_SWEEP_TIMEOUT"
                        )
                    except:
                        pass
                    # 3. Limpa banco
                    try:
                        await firebase_service.hard_reset_slot(pending_slot, reason="Sentinel Iron Sweep: Genesis Timeout")
                    except:
                        pass

async def slot_operator_price_fallback(symbol: str) -> float:
    """Obtém o preço atual do ativo para o cálculo do Stop preventivo."""
    from services.bybit_ws import bybit_ws_service
    try:
        price = getattr(bybit_ws_service, 'get_current_price', lambda s: 0.0)(symbol)
        if price > 0:
            return price
    except:
        pass
    try:
        ticker = await okx_rest_service.get_tickers(symbol)
        if ticker and ticker.get("result", {}).get("list"):
            return float(ticker["result"]["list"][0].get("lastPrice", 0))
    except:
        pass
    return 0.0

# Instanciação Singleton global do Sentinel Auditor
sentinel_auditor = SentinelAuditor()
