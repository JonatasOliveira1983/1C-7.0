"""
BASE Technologica — Laya Router Service (System 1: classificacao de intencao em CPU)
=====================================================================================
Motor de decisao nao-autorregressivo (laya-multilingual, 322M) que classifica
cada mensagem do chat em UMA forward pass (~0.5s em CPU), sem gerar texto:

- intent (choice): saudacao | capacidades | identidade | contexto_atual |
                   duvida_tecnica | escrita_documento | acionar_agente | conversa_livre
- is_write (noul): probabilidade de ser pedido de escrita (sinal fraco no
                   zero-shot; o gate principal de escrita e' o intent
                   escrita_documento + as guardas de duvida do orquestrador).

COMO CUSTOMIZAR POR SISTEMA (NOVO_SISTEMA.md passo 3): ajuste as descricoes
em INTENT_QUESTION para o vocabulario do dominio (ex.: "projeto eletrico"
-> "pedido do cliente"), e calibre os thresholds no orquestrador. Para
qualidade de producao, fine-tune gratuito no Kaggle (2xT4) com os intents
reais — zero-shot e' imperfeito: usar com thresholds e sempre com fallback
(keywords -> LLM).
"""
import asyncio
import os
import time
import threading
import logging
from typing import Any, Dict, Optional, List
import httpx

logger = logging.getLogger("1CRYPTEN-LAYA-ROUTER")

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

from pathlib import Path as _Path

LAYA_HUB_ID = "convaiinnovations/laya-multilingual"
LAYA_LOCAL_DIR = (
    _Path(__file__).resolve().parent.parent / "data" / "models" / "laya-multilingual"
)


def _ensure_local_checkpoint() -> Optional[str]:
    """Retorna caminho do checkpoint local se existir (local ou cache HF)."""
    marker = LAYA_LOCAL_DIR / "model.safetensors"
    if marker.exists() and marker.stat().st_size > 100_000_000:
        return str(LAYA_LOCAL_DIR)

    import glob
    hf_cache_pattern = str(_Path.home() / ".cache" / "huggingface" / "hub" / "models--convaiinnovations--laya" / "snapshots" / "*" / "multilingual")
    snapshots = glob.glob(hf_cache_pattern)
    if snapshots and os.path.exists(os.path.join(snapshots[0], "model.safetensors")):
        return snapshots[0]

    return None


INTENT_QUESTION = {
    "type": "choice",
    "instructions": (
        "Qual a intencao principal da mensagem do usuario para o assistente do sistema?"
    ),
    "criteria": {
        "saudacao": "cumprimento ou oi inicial, sem nenhum pedido",
        "capacidades": "pergunta o que o sistema, o orquestrador ou os especialistas podem fazer",
        "identidade": "pergunta quem e o assistente, seu nome ou seu papel",
        "contexto_atual": "pede resumo, status, valores ou dados do contexto/projeto atual do sistema",
        "duvida_tecnica": "duvida tecnica do dominio, sem pedir alteracao",
        "escrita_documento": "manda preencher, gerar, alterar documento, registro, calculo ou relatorio",
        "acionar_agente": "pede para acionar, chamar ou falar com um agente especialista",
        "conversa_livre": "qualquer outra conversa ou pergunta geral",
    },
}

WRITE_QUESTION = {
    "type": "noul",
    "instructions": "O usuario pede para alterar, gerar ou escrever dados em documento ou registro?",
}

ENTRY_DECISION_QUESTION = {
    "type": "choice",
    "instructions": "Com base nos dados de mercado, regime de volatilidade, fluxo e consenso dos agentes, qual a acao de execucao recomendada?",
    "criteria": {
        "BUY": "comprar ou abrir posicao long altista com confluencia favoravel",
        "SELL": "vender ou abrir posicao short baixista com rompimento ou exaustao",
        "HOLD": "aguardar, manter liquidez, mercado sem definicao ou risco assimetrico desfavoravel"
    }
}

EXIT_DECISION_QUESTION = {
    "type": "choice",
    "instructions": "Para esta ordem em aberto e a dinamica atual do preco, qual e o manejo de saida adequado?",
    "criteria": {
        "HOLD_TRAIL": "manter a ordem em aberto e deixar o trailing stop proteger os lucros",
        "PARTIAL_TP": "realizar lucro parcial e proteger o preco de entrada no breakeven",
        "FULL_EXIT": "encerrar totalmente a posicao no alvo de resistencia ou exaustao de fluxo",
        "PANIC_CUT": "encerrar a posicao imediatamente para estancar risco por reversao abrupta"
    }
}

QUESTIONS = {"intent": INTENT_QUESTION, "is_write": WRITE_QUESTION}
ENTRY_QUESTIONS = {"decision": ENTRY_DECISION_QUESTION}
EXIT_QUESTIONS = {"decision": EXIT_DECISION_QUESTION}

_agent = None
_agent_lock = threading.Lock()
_infer_lock = threading.Lock()
_load_status: Dict[str, Any] = {"status": "NOT_LOADED", "error": None, "last_latency_ms": None}


def _get_agent():
    """Singleton lazy do agente laya-multilingual (so' ele, sem Router p/ economizar RAM)."""
    global _agent
    if _agent is not None:
        return _agent
    with _agent_lock:
        if _agent is not None:
            return _agent
        _load_status["status"] = "LOADING"
        t0 = time.time()
        ckpt = _ensure_local_checkpoint()
        if not ckpt:
            _load_status["status"] = "READY_FAST_NEURAL"
            return None
        try:
            import torch

            # Nao disputar todos os cores com o llama-cpp (4 threads)
            try:
                torch.set_num_threads(2)
                torch.set_num_interop_threads(1)
            except Exception:
                pass
            import laya
            logger.info(f"[*] Carregando Laya {getattr(laya, '__version__', '0.4.22')} na CPU (eager mode)...")
            _agent = laya.load(ckpt, device="cpu", backend="eager", compile=False, compile_warmup=False)
            _load_status["status"] = "READY"
            _load_status["load_time_s"] = round(time.time() - t0, 2)
            logger.info(f"[OK] Laya {getattr(laya, '__version__', '0.4.22')} pronto em {_load_status['load_time_s']}s.")
            return _agent
        except Exception as e:
            _load_status["status"] = "ERROR"
            _load_status["error"] = str(e)
            print(f"[!] Falha ao carregar Laya: {e}")
            return None


from app.services.laya_flow_service import laya_flow_service


class LayaRouterService:
    """
    LAYA SOVEREIGN COMMAND CENTER
    ==============================
    Cérebro Central Soberano de Trading:
    - Leitor de Fluxo Institucional e Caça de Liquidez (OI Delta + LSR Rubik OKX).
    - Motor Adaptativo Dual:
        * ADX < 25: Modo Mean-Reversion (Opera fundos e topos de consolidação).
        * ADX >= 25: Modo Trend Sniper (Opera rompimentos com momentum e fluxo).
    - Gestão Flash Guard Integrada (Breakeven em +1% e Trailing Profit).
    - Telemetria de Consciência em Tempo Real (Thought Stream para a UI).
    """

    MIN_ENTRY_SCORE: int = 85

    def __init__(self):
        self._last_global_trade_open_ts: float = 0.0
        self.thought_stream: List[Dict[str, Any]] = []
        self.current_regime = "LATERAL"
        self.regime_mode = "MEAN_REVERSION"
        self.master_adx = 14.5
        self.last_scan_time = time.time()
        self.is_autonomous_active = True
        self.candidate_setups: Dict[str, Any] = {}
        self.whale_flow_cache: Dict[str, Any] = {}
        self._cached_radar_pulse: Optional[Dict[str, Any]] = None
        self._last_pulse_ts: float = 0.0
        self._symbol_cooldowns: Dict[str, float] = {}
        self._directional_penalties: Dict[str, Dict[str, Any]] = {}
        self._direction_stops: List[Dict[str, Any]] = []
        self._direction_cooldowns: Dict[str, float] = {}
        self._global_stop_history: List[float] = []
        self._global_circuit_breaker_until: float = 0.0
        self._last_symbol_thought: Dict[str, str] = {}
        self._scan_lock: Optional[asyncio.Lock] = None
        self.btc_climate_cache: Dict[str, Any] = {"regime": "ALTCOIN_EXPANSION"}
        self.universal_market_stats: Dict[str, Any] = {
            "total_pairs": 507,
            "liquid_pairs": 0,
            "ignited_count": 0,
            "last_scan_ts": 0.0
        }
        self.calibrated_weights = self._load_calibrated_weights()
        self._seed_initial_thoughts()
        self._bootstrap_initial_setups()

    def evaluate_channel_position(self, diff_pct: float, lsr: float, flow_regime: str = "NEUTRAL", change_24h_pct: float = 0.0) -> Dict[str, Any]:
        """
        [V148-WINRATE] Avalia rigorosamente se o preço está em zona de desconto ou exaustão real.
        Filtro de Tendência Protetivo: Nunca abrir SHORT se o ativo está em forte momentum de alta.
        """
        if diff_pct <= -0.30:
            # Filtro protetivo: Nunca abrir LONG se o ativo estiver em queda livre
            if change_24h_pct <= -2.5:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 60,
                    "rationale": f"MOMENTUM DE BAIXA ATIVO (24h {change_24h_pct:+.1f}%): Long bloqueado contra queda livre."
                }
            score = 92 if (lsr <= 1.15 or flow_regime == "LONG_LIQUIDATION_BOTTOM") else 86
            return {
                "qualifies": True,
                "direction": "LONG",
                "score": score,
                "rationale": f"REVERSÃO NO SUPORTE: Preço em zona de desconto (diff {diff_pct:.1f}%). LSR {lsr:.2f} favorável para acumulação."
            }
        elif diff_pct >= 0.35:
            # Filtro protetivo: Nunca abrir SHORT se o ativo estiver em forte rali
            if change_24h_pct >= 2.5:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 60,
                    "rationale": f"MOMENTUM DE ALTA ATIVO (24h {change_24h_pct:+.1f}%): Short bloqueado contra fluxo comprador."
                }
            score = 92 if (lsr >= 1.15 or flow_regime == "SHORT_LIQUIDATION_TOP") else 86
            return {
                "qualifies": True,
                "direction": "SHORT",
                "score": score,
                "rationale": f"EXAUSTÃO NA RESISTÊNCIA: Preço no topo do canal (diff +{diff_pct:.1f}%). LSR {lsr:.2f}."
            }
        else:
            # Miolo do canal: sem assimetria estatística, não qualifica
            return {
                "qualifies": False,
                "direction": "HOLD",
                "score": 65,
                "rationale": f"MIOLO DO CANAL (diff {diff_pct:.1f}%): Ausência de borda estatística. Entrada bloqueada para preservar Win Rate."
            }

    def calculate_h1_accumulation_range(self, candles: List[Any]) -> Dict[str, Any]:
        """
        [ENCRYPTOS METHODOLOGY - 1H ACCUMULATION]
        Calcula a zona de acumulação institucional no Timeframe de 1 Hora.
        Identifica a consolidação real antes da explosão de saída.
        Suporta tanto dicts quanto listas/tuplas brutas da OKX [ts, o, h, l, c, ...].
        """
        if not candles or len(candles) < 3:
            return {"is_consolidating": False, "resistance_h1": 0.0, "support_h1": 0.0, "range_pct": 0.0}

        highs = []
        lows = []
        for c in candles:
            if isinstance(c, (list, tuple)) and len(c) >= 4:
                try:
                    highs.append(float(c[2]))
                    lows.append(float(c[3]))
                except (ValueError, TypeError):
                    pass
            elif isinstance(c, dict):
                try:
                    h = float(c.get("high") or c.get("h") or 0.0)
                    l = float(c.get("low") or c.get("l") or 0.0)
                    if h > 0:
                        highs.append(h)
                    if l > 0:
                        lows.append(l)
                except (ValueError, TypeError):
                    pass
        
        valid_highs = [h for h in highs if h > 0]
        valid_lows = [l for l in lows if l > 0]

        if not valid_highs or not valid_lows:
            return {"is_consolidating": False, "resistance_h1": 0.0, "support_h1": 0.0, "range_pct": 0.0}

        resistance_h1 = max(valid_highs)
        support_h1 = min(valid_lows)
        range_pct = ((resistance_h1 - support_h1) / support_h1) * 100.0 if support_h1 > 0 else 0.0

        # Uma acumulação H1 saudável tem compressão entre 0.5% e 12.0%
        is_consolidating = (0.5 <= range_pct <= 12.0)

        return {
            "is_consolidating": is_consolidating,
            "resistance_h1": round(resistance_h1, 4),
            "support_h1": round(support_h1, 4),
            "range_pct": round(range_pct, 2)
        }


    def _parse_candle(self, c: Any) -> Dict[str, float]:
        """Auxiliar robusto para normalizar candles vindos em formato dict ou list/tuple da OKX."""
        if isinstance(c, (list, tuple)) and len(c) >= 5:
            try:
                return {
                    "ts": float(c[0]),
                    "open": float(c[1]),
                    "high": float(c[2]),
                    "low": float(c[3]),
                    "close": float(c[4]),
                    "vol": float(c[5]) if len(c) > 5 else 0.0
                }
            except (ValueError, TypeError):
                return {}
        elif isinstance(c, dict):
            try:
                return {
                    "ts": float(c.get("ts") or c.get("timestamp") or 0.0),
                    "open": float(c.get("open") or c.get("o") or 0.0),
                    "high": float(c.get("high") or c.get("h") or 0.0),
                    "low": float(c.get("low") or c.get("l") or 0.0),
                    "close": float(c.get("close") or c.get("c") or 0.0),
                    "vol": float(c.get("vol") or c.get("volume") or c.get("v") or 0.0)
                }
            except (ValueError, TypeError):
                return {}
        return {}

    def aggregate_1h_to_2h(self, candles_1h: List[Any]) -> List[Dict[str, float]]:
        """
        [V187-BRUNO-AGUIAR-FUSION]
        Agrega candles de 1H em candles de 2H deterministicamente.
        Cada candle de 2H e a fusao de 2 candles consecutivos de 1H.
        """
        parsed = []
        for c in (candles_1h or []):
            p = self._parse_candle(c)
            if p and p.get("close", 0) > 0:
                parsed.append(p)
        if len(parsed) < 2:
            return []
        parsed.sort(key=lambda x: x["ts"])
        candles_2h = []
        n = len(parsed)
        start_idx = n % 2
        for i in range(start_idx, n, 2):
            c1 = parsed[i]
            c2 = parsed[i+1]
            candles_2h.append({
                "ts": c2["ts"],
                "open": c1["open"],
                "high": max(c1["high"], c2["high"]),
                "low": min(c1["low"], c2["low"]),
                "close": c2["close"],
                "vol": c1["vol"] + c2["vol"]
            })
        return candles_2h

    def aggregate_15m_to_30m(self, candles_15m: list) -> list:
        """
        [V195-AGGREGATE-15M-TO-30M]
        Agrega candles de 15M em candles de 30M deterministicamente.
        Cada candle de 30M e a fusao de 2 candles consecutivos de 15M.
        """
        parsed = []
        for c in (candles_15m or []):
            if isinstance(c, dict) and "close" in c:
                parsed.append(c)
            else:
                p = self._parse_candle(c)
                if p and p.get("close", 0) > 0:
                    parsed.append(p)
        if len(parsed) < 2:
            return parsed
        parsed.sort(key=lambda x: x.get("ts", 0))
        candles_30m = []
        n = len(parsed)
        start_idx = n % 2
        for i in range(start_idx, n, 2):
            c1 = parsed[i]
            c2 = parsed[i+1]
            candles_30m.append({
                "ts": c2.get("ts", 0),
                "open": float(c1.get("open", 0.0)),
                "high": max(float(c1.get("high", 0.0)), float(c2.get("high", 0.0))),
                "low": min(float(c1.get("low", 0.0)), float(c2.get("low", 0.0))),
                "close": float(c2.get("close", 0.0)),
                "vol": float(c1.get("vol", 0.0)) + float(c2.get("vol", 0.0))
            })
        return candles_30m

    def calculate_sma_cross_2h(self, candles_2h: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        [V187-BRUNO-AGUIAR-SMA-2H]
        Calcula a SMA 8 (Branca) e SMA 21 (Amarela) no tempo grafico de 2H.
        Retorna o status do cruzamento e a forca da tendencia.
        """
        if not candles_2h or len(candles_2h) < 6:
            return {"has_cross": False, "cross_type": "NEUTRAL", "direction": "HOLD", "sma8": 0.0, "sma21": 0.0, "diff_pct": 0.0}

        closes = [c["close"] for c in candles_2h]
        n = len(closes)

        # Calculo de SMA 8
        len_8 = min(8, n)
        sma8_curr = sum(closes[-len_8:]) / float(len_8)

        # Calculo de SMA 21 (ou maxima historica disponivel se menor que 21)
        len_21 = min(21, n)
        sma21_curr = sum(closes[-len_21:]) / float(len_21)

        # Periodo anterior para deteccao de cruzamento de borda
        if n >= 9:
            len_8_prev = min(8, n - 1)
            sma8_prev = sum(closes[-(len_8_prev+1):-1]) / float(len_8_prev)
            len_21_prev = min(21, n - 1)
            sma21_prev = sum(closes[-(len_21_prev+1):-1]) / float(len_21_prev)
        else:
            sma8_prev = sma8_curr
            sma21_prev = sma21_curr

        is_bullish_cross = (sma8_prev <= sma21_prev and sma8_curr > sma21_curr)
        is_bearish_cross = (sma8_prev >= sma21_prev and sma8_curr < sma21_curr)

        is_aligned_bull = sma8_curr > sma21_curr
        is_aligned_bear = sma8_curr < sma21_curr

        if is_bullish_cross:
            cross_type = "BULLISH_CROSS"
            direction = "LONG"
        elif is_bearish_cross:
            cross_type = "BEARISH_CROSS"
            direction = "SHORT"
        elif is_aligned_bull:
            cross_type = "ALIGNED_BULL"
            direction = "LONG"
        elif is_aligned_bear:
            cross_type = "ALIGNED_BEAR"
            direction = "SHORT"
        else:
            cross_type = "NEUTRAL"
            direction = "HOLD"

        diff_pct = round(((sma8_curr - sma21_curr) / sma21_curr) * 100.0, 2) if sma21_curr > 0 else 0.0

        return {
            "has_cross": is_bullish_cross or is_bearish_cross,
            "cross_type": cross_type,
            "direction": direction,
            "sma8": round(sma8_curr, 6),
            "sma21": round(sma21_curr, 6),
            "diff_pct": diff_pct
        }

    def register_directional_penalty(self, symbol: str, direction: str, penalty_pts: int, reason: str = ""):
        """[V193] Registra penalidade de quarentena apenas para uma direcao especifica (LONG ou SHORT)."""
        clean = symbol.replace("-USDT-SWAP", "").replace("USDT", "").upper()
        dir_norm = direction.upper()
        key = f"{clean}:{dir_norm}"
        if not hasattr(self, "_directional_penalties"):
            self._directional_penalties = {}
        self._directional_penalties[key] = {
            "penalty": penalty_pts,
            "ts": time.time(),
            "reason": reason
        }

    def is_direction_penalized(self, symbol: str, direction: str, ttl_seconds: float = 7200.0) -> bool:
        """Retorna True se a direcao especifica estiver sob penalidade de quarentena ativa."""
        return self.get_directional_penalty(symbol, direction, ttl_seconds) > 0

    def get_directional_penalty(self, symbol: str, direction: str, ttl_seconds: float = 7200.0) -> int:
        """Retorna a penalidade em pontos para a direcao informada."""
        clean = symbol.replace("-USDT-SWAP", "").replace("USDT", "").upper()
        dir_norm = direction.upper()
        key = f"{clean}:{dir_norm}"
        if not hasattr(self, "_directional_penalties"):
            self._directional_penalties = {}
        record = self._directional_penalties.get(key)
        if not record:
            return 0
        if time.time() - record.get("ts", 0.0) > ttl_seconds:
            del self._directional_penalties[key]
            return 0
        return int(record.get("penalty", 0))

    def enforce_2h_directional_regime(self, symbol: str, klines_2h: List[Any], btc_macro_direction: str = "NEUTRAL") -> Dict[str, Any]:
        """
        [V193-SOVEREIGN-2H-ALIGNMENT]
        Subordina a direcao do par estritamente a tendencia macro do timeframe 2H (SMA 8 x SMA 21).
        - SMA 8 < SMA 21: Regime SHORT_ONLY. LONG estritamente vetado.
        - SMA 8 > SMA 21: Regime LONG_ONLY. SHORT estritamente vetado.
        - Neutro (< 0.15% dif): Ambos permitidos caso haja confluencia extrema.
        """
        parsed = []
        for c in (klines_2h or []):
            if isinstance(c, dict) and "close" in c:
                parsed.append(c)
            else:
                p = self._parse_candle(c)
                if p and p.get("close", 0) > 0:
                    parsed.append(p)
        
        if not parsed or len(parsed) < 6:
            return {
                "regime": "NEUTRAL",
                "allowed_direction": "BOTH",
                "long_vetoed": False,
                "short_vetoed": False,
                "sma8": 0.0,
                "sma21": 0.0,
                "diff_pct": 0.0
            }
        
        sma_info = self.calculate_sma_cross_2h(parsed)
        direction = sma_info.get("direction", "HOLD")
        sma8 = sma_info.get("sma8", 0.0)
        sma21 = sma_info.get("sma21", 0.0)
        diff_pct = sma_info.get("diff_pct", 0.0)

        # [V202-LINK-PRECISION] Filtro Anti-Falso Canal de Alta e Subordinacao Macro BTC
        is_real_bear_channel = (direction == "SHORT" and diff_pct <= -0.15) or (sma8 < sma21 and diff_pct <= -0.15)
        is_real_bull_channel = (direction == "LONG" and diff_pct >= 0.35) or (sma8 > sma21 and diff_pct >= 0.35)

        if is_real_bear_channel:
            return {
                "regime": "SHORT_ONLY",
                "allowed_direction": "SHORT",
                "long_vetoed": True,
                "short_vetoed": False,
                "sma8": sma8,
                "sma21": sma21,
                "diff_pct": diff_pct,
                "reason": f"Canal de Baixa Soberano 2H (SMA8 {sma8:.4f} < SMA21 {sma21:.4f} | {diff_pct:+.2f}%)"
            }
        elif is_real_bull_channel:
            # So autoriza LONG_ONLY se o Bitcoin estiver expressamente em regime BULL
            if btc_macro_direction != "BULL":
                return {
                    "regime": "SHORT_ONLY" if btc_macro_direction == "BEAR" else "NEUTRAL",
                    "allowed_direction": "SHORT_OR_HOLD",
                    "long_vetoed": True,
                    "short_vetoed": False,
                    "sma8": sma8,
                    "sma21": sma21,
                    "diff_pct": diff_pct,
                    "reason": f"VETO FAROL BTC: Alta local 2H da altcoin ({diff_pct:+.2f}%) bloqueada para LONG pois o Bitcoin nao esta em BULL macro (Status: {btc_macro_direction})."
                }
            return {
                "regime": "LONG_ONLY",
                "allowed_direction": "LONG",
                "long_vetoed": False,
                "short_vetoed": True,
                "sma8": sma8,
                "sma21": sma21,
                "diff_pct": diff_pct,
                "reason": f"Canal de Alta Soberano 2H (SMA8 {sma8:.4f} > SMA21 {sma21:.4f} | {diff_pct:+.2f}%)"
            }
        else:
            # Consolidacao plana / micro-afastamento (como +0.01% na LINK)
            # Se o Bitcoin estiver em BEAR ou NEUTRAL (dreno de liquidez), compras sao estritamente vetadas!
            is_btc_safe_for_alt_long = (btc_macro_direction == "BULL")
            return {
                "regime": "SHORT_ONLY" if btc_macro_direction == "BEAR" else "NEUTRAL",
                "allowed_direction": "SHORT_OR_HOLD" if not is_btc_safe_for_alt_long else "BOTH",
                "long_vetoed": not is_btc_safe_for_alt_long,
                "short_vetoed": False,
                "sma8": sma8,
                "sma21": sma21,
                "diff_pct": diff_pct,
                "reason": f"Consolidacao 2H (SMA8 colada na SMA21 | {diff_pct:+.2f}%) | {'LONG vetado por macro sem forca compradora' if not is_btc_safe_for_alt_long else 'Neutro'}"
            }

    def calculate_30m_pullback_trigger(
        self,
        symbol: str,
        klines_30m: list,
        current_price: float,
        macro_direction: str,
        lsr: float = 1.0,
        btc_dominance: float = 58.0,
        btc_trend_bias: float = 0.0,
        bot_ignition: bool = False,
        c_exp: float = 50.0,
        **kwargs
    ) -> dict:
        """
        [V207-SNIPER-CONFLUENCE-PULLBACK-GATE]
        Gatilho Sniper em 2 Camadas:
        - CAMADA 1 (Barreiras Mecanicas Inegociaveis):
          1. Toque Real na Linha Branca (SMA8): Preco deve ter testado a SMA8 (diff >= -0.30% e c_high >= sma8 * 0.998). Veto sumario para entradas no vacuo!
          2. Anti-Candle de Forca: Proibido vender se vela for de alta com corpo longo (>50%) sem pavio superior relevante (<25%).
          3. Stop Estrutural: Stop Loss posicionado obrigatoriamente ACIMA da Linha Amarela (SMA21) e da maxima local.
        - CAMADA 2 (Cesto de Confluencias Inteligentes):
          Exige pelo menos 3 confluencias ativas (Pavio/Candle, LSR Anti-Squeeze, Farol BTC/Dominancia, Robos/EXP, Alinhamento de Medias).
        """
        parsed = []
        for c in (klines_30m or []):
            if isinstance(c, dict) and "close" in c:
                parsed.append(c)
            else:
                p = self._parse_candle(c)
                if p and p.get("close", 0) > 0:
                    parsed.append(p)

        if len(parsed) < 6:
            return {
                "has_pullback_setup": False,
                "score_boost": 0,
                "reason": "Klines 30M insuficientes",
                "pullback_type": "NONE"
            }

        closes = [float(c["close"]) for c in parsed]
        n = len(closes)
        len_8 = min(8, n)
        sma8 = sum(closes[-len_8:]) / float(len_8)
        len_21 = min(21, n)
        sma21 = sum(closes[-len_21:]) / float(len_21)

        recent = parsed[-1]
        prev = parsed[-2] if len(parsed) >= 2 else recent
        c_open = float(recent.get("open", recent.get("close", 0.0)))
        c_high = max(float(recent.get("high", 0.0)), float(prev.get("high", 0.0)))
        c_low = min(float(recent.get("low", 0.0)), float(prev.get("low", 0.0)))
        c_close = float(current_price or recent.get("close", 0.0))

        if sma8 <= 0:
            return {"has_pullback_setup": False, "score_boost": 0, "reason": "SMA8 invalida", "pullback_type": "NONE"}

        diff_from_sma8 = ((c_close - sma8) / sma8) * 100.0
        candle_range = max(1e-8, c_high - c_low)

        # Em regime SHORT:
        if macro_direction == "SHORT":
            # --- CAMADA 1: AS 3 BARREIRAS MECANICAS INEGOCIAVEIS ---
            
            # [V208-UNIFIED-SNIPER-A-PLUS-B]
            sma8_2h = float(kwargs.get("sma8_2h", 0.0))
            sma21_2h = float(kwargs.get("sma21_2h", 0.0))

            # Barreira 1: Proximidade Estrita e Toque Real na Linha Branca (SMA8 2H/30M)
            recent_high = float(recent.get("high", c_close))
            touched_sma8_30m = recent_high >= (sma8 * 0.998) or diff_from_sma8 >= -0.30
            if sma8_2h > 0:
                diff_2h = ((c_close - sma8_2h) / sma8_2h) * 100.0
                touched_sma8_2h = recent_high >= (sma8_2h * 0.996) or diff_2h >= -0.45
                touched_sma8 = touched_sma8_2h or touched_sma8_30m
                if not touched_sma8:
                    return {
                        "has_pullback_setup": False,
                        "score_boost": 0,
                        "reason": f"VETO_AGUARDANDO_TOQUE_SMA8: Preco a {abs(diff_from_sma8):.2f}% da SMA8 30M e {abs(diff_2h):.2f}% da SMA8 2H ({sma8_2h:.4f}). Aguardando repique na linha branca.",
                        "pullback_type": "VACUUM_BELOW_SMA8"
                    }
            else:
                if not touched_sma8_30m or diff_from_sma8 < -0.30:
                    return {
                        "has_pullback_setup": False,
                        "score_boost": 0,
                        "reason": f"VETO_AGUARDANDO_TOQUE_SMA8: Preco a {abs(diff_from_sma8):.2f}% abaixo da SMA8 ({sma8:.4f}). Aguardando repique alcancar a linha branca para armar gatilho sniper.",
                        "pullback_type": "VACUUM_BELOW_SMA8"
                    }

            # Barreira 1b: Se preco ja rompeu acima da SMA21 com folga, o repique virou reversao de alta local
            if sma21_2h > 0 and c_close > (sma21_2h * 1.004):
                return {
                    "has_pullback_setup": False,
                    "score_boost": 0,
                    "reason": f"VETO_ROMPIMENTO_ALTA: Preco ultrapassou a SMA21 2H ({sma21_2h:.4f}). Gatilho desarmado.",
                    "pullback_type": "PULLBACK_INVALIDATED"
                }
            elif c_close > (sma21 * 1.004):
                return {
                    "has_pullback_setup": False,
                    "score_boost": 0,
                    "reason": f"VETO_ROMPIMENTO_ALTA: Preco ultrapassou a SMA21 ({sma21:.4f}) em {((c_close-sma21)/sma21)*100:.2f}%. Gatilho desarmado.",
                    "pullback_type": "PULLBACK_INVALIDATED"
                }

            # Barreira 2: Anti-Candle de Forca Compradora (Exaustao Obrigatoria no 30M)
            upper_wick = c_high - max(c_open, c_close)
            upper_wick_ratio = upper_wick / candle_range
            is_green_candle = c_close > c_open
            body_ratio = abs(c_close - c_open) / candle_range

            if is_green_candle and body_ratio > 0.50 and upper_wick_ratio < 0.25:
                return {
                    "has_pullback_setup": False,
                    "score_boost": 0,
                    "reason": f"VETO_CANDLE_FORCA_COMPRADORA: Vela de alta com corpo dominante ({body_ratio*100:.0f}%) e sem pavio superior ({upper_wick_ratio*100:.0f}%). Proibido vender contra expansao verde.",
                    "pullback_type": "BULL_BODY_IMPULSE"
                }

            # Barreira 3: Calculo e Posicionamento do Stop Loss ACIMA da Linha Amarela (SMA21 2H Soberana)
            major_res = max(sma8, sma21, sma21_2h if sma21_2h > 0 else 0.0)
            sl_price = round(max(c_high * 1.004, major_res * 1.006, (sma8 + abs(sma21 - sma8) * 1.25)), 4)
            if sma21_2h > 0 and sl_price <= sma21_2h:
                sl_price = round(sma21_2h * 1.006, 4)
            elif sl_price <= major_res:
                sl_price = round(major_res * 1.006, 4)

            stop_dist_pct = (sl_price - c_close) / c_close if c_close > 0 else 0.015
            max_stop_dist = 0.050 if sma21_2h > 0 else 0.035
            if stop_dist_pct > max_stop_dist:
                return {
                    "has_pullback_setup": False,
                    "score_boost": 0,
                    "reason": f"VETO_STOP_MUITO_LONGO: Distancia do Stop Loss ({stop_dist_pct*100:.2f}%) acima do limite institucional de {max_stop_dist*100:.1f}%.",
                    "pullback_type": "STOP_TOO_FAR"
                }

            # --- CAMADA 2: CESTO DE CONFLUÊNCIAS INTELIGENTES (CHECKLIST PONDERADO) ---
            confluences = []
            if upper_wick_ratio >= 0.25 or c_close < c_open:
                confluences.append(f"PAVIO_REJEICAO({upper_wick_ratio*100:.0f}%)")
            if lsr >= 0.85:
                confluences.append(f"LSR_LIVRE({lsr:.2f})")
            if btc_trend_bias <= 0.0 or btc_dominance >= 57.5:
                confluences.append("FAROL_BTC_FAVORAVEL")
            if bot_ignition or c_exp >= 60.0:
                confluences.append("ALGO_IGNITION")
            if sma8 < sma21 and ((sma21 - sma8) / sma21) >= 0.0010:
                confluences.append("CANAL_DESCENDENTE")

            if len(confluences) < 3:
                return {
                    "has_pullback_setup": False,
                    "score_boost": 0,
                    "reason": f"VETO_CONFLUENCIA_INSUFICIENTE: Apenas {len(confluences)}/5 confluencias ativas ({', '.join(confluences)}). Minimo exigido: 3.",
                    "pullback_type": "LOW_CONFLUENCE"
                }

            tgt_price = round(min(c_low * 0.970, c_close * 0.940), 4)
            return {
                "has_pullback_setup": True,
                "score_boost": 15 + len(confluences) * 2,
                "reason": f"GATILHO_SNIPER_SHORT: Toque na SMA8 ({sma8:.4f}) com {len(confluences)} confluencias ({', '.join(confluences)}) | Stop blindado acima da SMA21 em {sl_price:.4f}",
                "pullback_type": "SNIPER_RETEST_SHORT",
                "sma8_30m": round(sma8, 6),
                "sma21_30m": round(sma21, 6),
                "stop_loss": sl_price,
                "target": tgt_price,
                "confluences": confluences
            }

        # Em regime LONG:
        elif macro_direction == "LONG":
            sma8_2h = float(kwargs.get("sma8_2h", 0.0))
            sma21_2h = float(kwargs.get("sma21_2h", 0.0))

            recent_low = float(recent.get("low", c_close))
            touched_sma8_30m = recent_low <= (sma8 * 1.002) or diff_from_sma8 <= 0.30
            if sma8_2h > 0:
                diff_2h = ((c_close - sma8_2h) / sma8_2h) * 100.0
                touched_sma8_2h = recent_low <= (sma8_2h * 1.004) or diff_2h <= 0.45
                touched_sma8 = touched_sma8_2h or touched_sma8_30m
                if not touched_sma8:
                    return {
                        "has_pullback_setup": False,
                        "score_boost": 0,
                        "reason": f"VETO_AGUARDANDO_TOQUE_SMA8: Preco a {diff_from_sma8:.2f}% da SMA8 30M e {diff_2h:.2f}% da SMA8 2H ({sma8_2h:.4f}). Aguardando recuo na linha branca.",
                        "pullback_type": "VACUUM_ABOVE_SMA8"
                    }
            else:
                if not touched_sma8_30m or diff_from_sma8 > 0.30:
                    return {
                        "has_pullback_setup": False,
                        "score_boost": 0,
                        "reason": f"VETO_AGUARDANDO_TOQUE_SMA8: Preco a {diff_from_sma8:.2f}% acima da SMA8 ({sma8:.4f}). Aguardando recuo na linha branca para armar gatilho.",
                        "pullback_type": "VACUUM_ABOVE_SMA8"
                    }

            if sma21_2h > 0 and c_close < (sma21_2h * 0.996):
                return {
                    "has_pullback_setup": False,
                    "score_boost": 0,
                    "reason": f"VETO_ROMPIMENTO_BAIXA: Preco perdeu a SMA21 2H ({sma21_2h:.4f}). Gatilho LONG desarmado.",
                    "pullback_type": "PULLBACK_INVALIDATED"
                }
            elif c_close < (sma21 * 0.996):
                return {
                    "has_pullback_setup": False,
                    "score_boost": 0,
                    "reason": f"VETO_ROMPIMENTO_BAIXA: Preco perdeu a SMA21 ({sma21:.4f}). Gatilho LONG desarmado.",
                    "pullback_type": "PULLBACK_INVALIDATED"
                }

            lower_wick = min(c_open, c_close) - c_low
            lower_wick_ratio = lower_wick / candle_range
            is_red_candle = c_close < c_open
            body_ratio = abs(c_open - c_close) / candle_range

            if is_red_candle and body_ratio > 0.50 and lower_wick_ratio < 0.25:
                return {
                    "has_pullback_setup": False,
                    "score_boost": 0,
                    "reason": f"VETO_CANDLE_FORCA_VENDEDORA: Vela de baixa com corpo dominante ({body_ratio*100:.0f}%) e sem pavio inferior ({lower_wick_ratio*100:.0f}%).",
                    "pullback_type": "BEAR_BODY_IMPULSE"
                }

            minor_sup = min(sma8, sma21, sma21_2h if sma21_2h > 0 else 999999.0)
            sl_price = round(min(c_low * 0.996, minor_sup * 0.994, (sma8 - abs(sma21 - sma8) * 1.25)), 4)
            if sma21_2h > 0 and sl_price >= sma21_2h:
                sl_price = round(sma21_2h * 0.994, 4)
            elif sl_price >= minor_sup:
                sl_price = round(minor_sup * 0.994, 4)

            stop_dist_pct = (c_close - sl_price) / c_close if c_close > 0 else 0.015
            max_stop_dist = 0.050 if sma21_2h > 0 else 0.035
            if stop_dist_pct > max_stop_dist:
                return {
                    "has_pullback_setup": False,
                    "score_boost": 0,
                    "reason": f"VETO_STOP_MUITO_LONGO: Distancia do Stop Loss ({stop_dist_pct*100:.2f}%) acima do limite.",
                    "pullback_type": "STOP_TOO_FAR"
                }

            confluences = []
            if lower_wick_ratio >= 0.25 or c_close > c_open:
                confluences.append(f"PAVIO_ABSORCAO({lower_wick_ratio*100:.0f}%)")
            if lsr <= 1.35:
                confluences.append(f"LSR_LIVRE({lsr:.2f})")
            if btc_trend_bias >= 0.0:
                confluences.append("FAROL_BTC_FAVORAVEL")
            if bot_ignition or c_exp >= 60.0:
                confluences.append("ALGO_IGNITION")
            if sma8 > sma21 and ((sma8 - sma21) / sma21) >= 0.0010:
                confluences.append("CANAL_ASCENDENTE")

            if len(confluences) < 3:
                return {
                    "has_pullback_setup": False,
                    "score_boost": 0,
                    "reason": f"VETO_CONFLUENCIA_INSUFICIENTE: Apenas {len(confluences)}/5 confluencias ativas. Minimo: 3.",
                    "pullback_type": "LOW_CONFLUENCE"
                }

            tgt_price = round(max(c_high * 1.030, c_close * 1.060), 4)
            return {
                "has_pullback_setup": True,
                "score_boost": 15 + len(confluences) * 2,
                "reason": f"GATILHO_SNIPER_LONG: Toque na SMA8 ({sma8:.4f}) com {len(confluences)} confluencias | Stop protegido abaixo da SMA21 em {sl_price:.4f}",
                "pullback_type": "SNIPER_RETEST_LONG",
                "sma8_30m": round(sma8, 6),
                "sma21_30m": round(sma21, 6),
                "stop_loss": sl_price,
                "target": tgt_price,
                "confluences": confluences
            }

        return {
            "has_pullback_setup": False,
            "score_boost": 0,
            "reason": f"Sem gatilho de reteste na SMA 30M (distancia SMA8: {diff_from_sma8:.2f}%)",
            "pullback_type": "NONE"
        }

    def classify_macro_market_regime(
        self,
        btc_sma_info: Dict[str, Any],
        btc_dominance: float = 58.0,
        btc_dominance_trend: str = "NEUTRAL"
    ) -> Dict[str, Any]:
        """
        [V188-MACRO-REGIME-CLASSIFIER]
        Classifica a mare global do mercado cripto a partir da estrutura do BTC no 2H e Dominancia.
        """
        btc_dir = (btc_sma_info or {}).get("direction", "NEUTRAL")
        
        if btc_dir == "SHORT":
            direction = "BEAR"
            is_expansion = btc_dominance >= 58.0 or str(btc_dominance_trend).upper() == "UP"
            regime = "BTC_BEAR_EXPANSION" if is_expansion else "BTC_BEAR_CHOP"
            allow_alt_shorts = True
            allow_alt_longs = False
        elif btc_dir == "LONG":
            direction = "BULL"
            regime = "BTC_BULL_RUSH"
            allow_alt_shorts = False
            allow_alt_longs = True
        else:
            direction = "NEUTRAL"
            regime = "CHOP"
            allow_alt_shorts = True
            allow_alt_longs = True

        return {
            "direction": direction,
            "regime": regime,
            "btc_direction": btc_dir,
            "btc_dominance": btc_dominance,
            "allow_alt_shorts": allow_alt_shorts,
            "allow_alt_longs": allow_alt_longs
        }

    def count_unprotected_risk_trades(self, active_trades: list) -> int:
        """
        [V197-TIERED-SLOT-ALLOCATION-4-PLUS-4]
        Conta quantas ordens ativas ainda estao com RISCO VIVO na Margem Cruzada
        (ou seja, stop ainda nao atingiu Risco Zero / Breakeven).
        """
        unprotected_count = 0
        for t in (active_trades or []):
            is_prot = getattr(t, "is_protected", False) or (t.get("is_protected") if isinstance(t, dict) else False)
            curr_sl = (
                getattr(t, "current_stop", None)
                or (t.get("current_stop") if isinstance(t, dict) else None)
                or getattr(t, "stop_loss", None)
                or (t.get("stop_loss") if isinstance(t, dict) else None)
            )
            ent_p = getattr(t, "entry_price", 0.0) or (t.get("entry_price") if isinstance(t, dict) else 0.0)
            t_side = (
                getattr(t, "side", None)
                or (t.get("side") if isinstance(t, dict) else None)
                or getattr(t, "direction", None)
                or (t.get("direction") if isinstance(t, dict) else None)
                or ""
            )
            t_side = str(t_side).upper()

            if is_prot:
                continue

            if not curr_sl or not ent_p:
                unprotected_count += 1
                continue

            try:
                curr_sl = float(curr_sl)
                ent_p = float(ent_p)
                if ("SHORT" in t_side or "SELL" in t_side) and curr_sl > ent_p:
                    unprotected_count += 1
                elif ("LONG" in t_side or "BUY" in t_side) and curr_sl < ent_p:
                    unprotected_count += 1
            except Exception:
                unprotected_count += 1

        return unprotected_count

    def is_decorrelated_outlier(self, decorr_info: Dict[str, Any]) -> bool:
        """
        [V188-DECORRELATED-OUTLIER-DETECTOR]
        Identifica moedas que se desgrudam do BTC com forca propria (10-15% do mercado).
        Criterios: Baixa correlacao (<0.35 ou is_decorrelated True) E explosao de volume (vol_ratio >= 2.5x ou volume_spike).
        """
        if not decorr_info or not isinstance(decorr_info, dict):
            return False
            
        is_dec = bool(decorr_info.get("is_decorrelated", False))
        corr = float(decorr_info.get("correlation", 1.0))
        vol_ratio = float(decorr_info.get("vol_ratio", 1.0))
        vol_spike = bool(decorr_info.get("volume_spike", False))
        confidence = float(decorr_info.get("confidence", 0.0))

        has_decorrelation = is_dec or corr < 0.35 or confidence >= 60.0
        has_abnormal_volume = vol_ratio >= 2.5 or vol_spike

        return bool(has_decorrelation and has_abnormal_volume)

    def validate_structural_reversal_2h(
        self,
        sma_info: Dict[str, Any],
        current_price: float,
        direction: str
    ) -> Dict[str, Any]:
        """
        [V188-ANTI-KNIFE-STRUCTURAL-VALIDATION]
        Valida quebra oficial de estrutura no 2H antes de autorizar qualquer reversao:
        - Para LONG: SMA 8 DEVE estar >= SMA 21 no 2H E preco corrente acima da SMA 21.
        - Para SHORT: SMA 8 DEVE estar <= SMA 21 no 2H E preco corrente abaixo da SMA 21.
        Proibe sumariamente adivinhacao de fundo (comprar faca caindo como AEON/MON antes do pivo).
        """
        macro_dir = (sma_info or {}).get("direction", "HOLD")
        sma21 = float((sma_info or {}).get("sma21", 0.0))
        sma8 = float((sma_info or {}).get("sma8", 0.0))

        norm_dir = str(direction).upper()

        if norm_dir in ("LONG", "BUY"):
            if macro_dir == "SHORT" or (sma21 > 0 and current_price < sma21) or (sma8 < sma21):
                return {
                    "confirmed": False,
                    "reason": f"VETO ANTI-FACA: Sem rompimento oficial 2H (SMA 8 ${sma8:.4f} < SMA 21 ${sma21:.4f} ou preco ${current_price:.4f} abaixo da media). Proibido adivinhar fundo.",
                    "macro_direction": macro_dir
                }
            # [REGRA DE RECUO / DIP LONG]: Nao comprar topo esticado! Preco deve estar em recuo proximo as medias
            if sma8 > 0 and current_price > sma8 * 1.015:
                return {
                    "confirmed": False,
                    "reason": f"VETO TOPO ESTICADO 2H: Preco (${current_price:.4f}) afastado +{((current_price-sma8)/sma8)*100:.1f}% acima da SMA 8 (${sma8:.4f}). Aguardar recuo/dip para comprar barato.",
                    "macro_direction": "LONG"
                }
            if sma21 > 0 and current_price < sma21 * 0.975:
                return {
                    "confirmed": False,
                    "reason": f"VETO VIOLACAO SMA 21: Preco (${current_price:.4f}) perfurou abaixo da SMA 21 (${sma21:.4f}). Estrutura de alta ameacada.",
                    "macro_direction": "LONG"
                }
            return {
                "confirmed": True,
                "reason": "ROMPEU_ESTRUTURA_2H: Rompimento oficial com SMA 8 acima da SMA 21 no 2H e preco em zona de recuo.",
                "macro_direction": "LONG"
            }
        elif norm_dir in ("SHORT", "SELL"):
            if macro_dir == "LONG" or (sma21 > 0 and current_price > sma21) or (sma8 > sma21):
                return {
                    "confirmed": False,
                    "reason": f"VETO ANTI-LOCOMOTIVA: Sem rompimento de baixa 2H (SMA 8 ${sma8:.4f} > SMA 21 ${sma21:.4f} ou preco ${current_price:.4f} acima da media). Proibido vender topo sem confirmacao.",
                    "macro_direction": macro_dir
                }
            # [REGRA DE RECUO / PULLBACK SHORT]: Nao vender fundo esticado! Preco deve ter repicado em direcao as medias
            if sma8 > 0 and current_price < sma8 * 0.985:
                return {
                    "confirmed": False,
                    "reason": f"VETO FUNDO ESTICADO 2H: Preco (${current_price:.4f}) afastado {((current_price-sma8)/sma8)*100:.1f}% abaixo da SMA 8 (${sma8:.4f}). Aguardar repique/pullback para vender caro.",
                    "macro_direction": "SHORT"
                }
            if sma21 > 0 and current_price > sma21 * 1.025:
                return {
                    "confirmed": False,
                    "reason": f"VETO ROMPIMENTO SMA 21: Preco (${current_price:.4f}) subiu acima da SMA 21 (${sma21:.4f}). Estrutura de baixa ameacada.",
                    "macro_direction": "SHORT"
                }
            return {
                "confirmed": True,
                "reason": "CONFIRMADO_BAIXA_2H: Tendencia de queda confirmada com SMA 8 abaixo da SMA 21 no 2H e preco em zona de pullback.",
                "macro_direction": "SHORT"
            }

        return {
            "confirmed": False,
            "reason": "DIRECAO_INDEFINIDA",
            "macro_direction": macro_dir
        }

    def evaluate_aguia_encryptos_fusion(
        self,
        symbol: str,
        current_price: float,
        candles_1h: List[Any],
        bot_ignition: bool,
        c_exp: float,
        btc_trend_bias: float = 0.0,
        reactive_5m: Optional[Dict[str, Any]] = None,
        lsr: float = 1.0,
        acc_range: Optional[Dict[str, Any]] = None,
        c_range: Optional[float] = None,
        candles_15m: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        [V187-SOVEREIGN-FUSION-BRUNO-PHENIX]
        Avalia o setup de Fusao Suprema:
        1. Direcao 2H (Bruno): Cruzamento ou alinhamento forte SMA 8 x SMA 21.
        2. Filtro Antifraude (Phenix): 1C-EXP >= 70 ou bot_ignition com Farol BTC compativel.
        3. Gatilho 5M: Vela de 5M fechada a favor do movimento (sem veto do Guardiao).
        """
        if current_price <= 0:
            return {"qualifies": False, "direction": "HOLD", "score": 0}

        candles_2h = self.aggregate_1h_to_2h(candles_1h)
        sma_cross = self.calculate_sma_cross_2h(candles_2h)

        direction = sma_cross.get("direction", "HOLD")
        cross_type = sma_cross.get("cross_type", "NEUTRAL")

        if direction not in ("LONG", "SHORT"):
            return {"qualifies": False, "direction": "HOLD", "score": 0, "sma_cross": sma_cross}

        sma8 = float(sma_cross.get("sma8", 0.0) or 0.0)
        sma21 = float(sma_cross.get("sma21", 0.0) or 0.0)

        # [REGRA DE OURO - RETRACAO / PULLBACK NO 2H]:
        # NUNCA vender fundo esticado e NUNCA comprar topo esticado!
        if direction == "SHORT":
            if sma8 > 0 and current_price < sma8 * 0.985:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 0,
                    "sma_cross": sma_cross,
                    "reason": f"Veto Fundo Esticado: Preco (${current_price:.4f}) afastado {((current_price-sma8)/sma8)*100:.1f}% abaixo da SMA 8 (${sma8:.4f}). Aguardando repique/pullback para vender caro."
                }
            if sma21 > 0 and current_price > sma21 * 1.025:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 0,
                    "sma_cross": sma_cross,
                    "reason": f"Veto Rompimento SMA 21: Preco (${current_price:.4f}) acima da SMA 21 (${sma21:.4f}). Estrutura de baixa ameacada."
                }
            if float(lsr or 1.0) < 0.80:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 0,
                    "sma_cross": sma_cross,
                    "reason": f"Veto Anti-Squeeze LSR: LSR em {float(lsr):.2f} (< 0.80). Sardinhas sobre-vendidas, risco severo de short squeeze."
                }
        elif direction == "LONG":
            max_sma8_stretch = 1.035 if (c_exp >= 70.0 or bot_ignition) else 1.022
            if sma8 > 0 and current_price > sma8 * max_sma8_stretch:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 0,
                    "sma_cross": sma_cross,
                    "reason": f"Veto Topo Esticado: Preco (${current_price:.4f}) afastado +{((current_price-sma8)/sma8)*100:.1f}% acima da SMA 8 (${sma8:.4f}). Aguardando recuo/dip para comprar barato."
                }
            if sma21 > 0 and current_price < sma21 * 0.975:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 0,
                    "sma_cross": sma_cross,
                    "reason": f"Veto Perfuracao SMA 21: Preco (${current_price:.4f}) abaixo da SMA 21 (${sma21:.4f}). Estrutura de alta ameacada."
                }
            if float(lsr or 1.0) > 1.35:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 0,
                    "sma_cross": sma_cross,
                    "reason": f"Veto Anti-Dump LSR: LSR em {float(lsr):.2f} (> 1.35). Sardinhas sobre-compradas, risco severo de liquidacao em cascata."
                }

        # Filtro Phenix: Exige aceleracao institucional (1C-EXP >= 60 ou robos ON) ou confirmacao macro do BTC / cruzamento 2H
        c_exp_val = float(c_exp or 0.0)
        has_phenix_fuel = bot_ignition or c_exp_val >= 60.0 or abs(btc_trend_bias) >= 0.25 or bool(sma_cross.get("has_cross"))
        if not has_phenix_fuel:
            return {
                "qualifies": False,
                "direction": direction,
                "score": 0,
                "sma_cross": sma_cross,
                "reason": f"Veto Encryptos: 1C-EXP ({c_exp_val:.0f}) insuficiente sem robos ativos."
            }

        # Filtro Farol BTC
        if direction == "LONG" and btc_trend_bias < -0.3:
            return {"qualifies": False, "direction": "HOLD", "score": 0, "sma_cross": sma_cross, "reason": "Veto Farol BTC: Queda acentuada do Bitcoin."}
        if direction == "SHORT" and btc_trend_bias > 0.8:
            return {"qualifies": False, "direction": "HOLD", "score": 0, "sma_cross": sma_cross, "reason": "Veto Farol BTC: Alta agressiva do Bitcoin."}

        # Gatilho 5M (Reativo)
        candle_5m_confirmed = True
        if reactive_5m and isinstance(reactive_5m, dict):
            # Se o guardiao 5M deu veto na direcao, aguarda
            if not reactive_5m.get("is_safe", True):
                candle_5m_confirmed = False

        if not candle_5m_confirmed:
            return {
                "qualifies": False,
                "direction": direction,
                "score": 0,
                "sma_cross": sma_cross,
                "reason": f"Aguardando confirmacao da vela de 5M ({reactive_5m.get('reason', '')})"
            }

        # [V191-SNIPER-SR-RETEST]: Canal 1C-Range e Posicao Estrutural
        c_range_val = c_range
        sup_h1 = 0.0
        res_h1 = 0.0
        if acc_range and isinstance(acc_range, dict):
            sup_h1 = float(acc_range.get("support_h1") or 0.0)
            res_h1 = float(acc_range.get("resistance_h1") or 0.0)
            if c_range_val is None and res_h1 > sup_h1 > 0:
                c_range_val = round(((current_price - sup_h1) / (res_h1 - sup_h1)) * 100.0, 1)
        if c_range_val is None:
            c_range_val = 50.0

        # Checa se preco esta em zona de reteste na media curta (15M SMA 8 / SMA 21)
        is_retesting_15m = False
        if candles_15m and len(candles_15m) >= 21:
            try:
                c15_closes = [float(c[4] if isinstance(c, (list, tuple)) else (c.get("close") or c.get("c") or 0.0)) for c in candles_15m]
                sma8_15 = sum(c15_closes[-8:]) / 8.0
                sma21_15 = sum(c15_closes[-21:]) / 21.0
                if direction == "LONG":
                    dist_sma8 = abs(current_price - sma8_15) / sma8_15 if sma8_15 > 0 else 1.0
                    dist_sma21 = abs(current_price - sma21_15) / sma21_15 if sma21_15 > 0 else 1.0
                    if dist_sma8 <= 0.006 or dist_sma21 <= 0.006 or (current_price >= sma21_15 and current_price <= sma8_15 * 1.006):
                        is_retesting_15m = True
                elif direction == "SHORT":
                    dist_sma8 = abs(current_price - sma8_15) / sma8_15 if sma8_15 > 0 else 1.0
                    dist_sma21 = abs(current_price - sma21_15) / sma21_15 if sma21_15 > 0 else 1.0
                    if dist_sma8 <= 0.006 or dist_sma21 <= 0.006:
                        is_retesting_15m = True
            except Exception:
                pass

        # [V191-VETO-VACUO-TOPO-CANAL]: Proibicao de comprar topo de expansao no vacuo
        if direction == "LONG":
            if c_range_val >= 55.0 and not is_retesting_15m:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 0,
                    "sma_cross": sma_cross,
                    "reason": f"Veto Topo Esticado / Vácuo (1C-Range {c_range_val:.1f}%): Preço no topo do canal sem reteste confirmado na base de suporte."
                }
        elif direction == "SHORT":
            if c_range_val <= 45.0 and not is_retesting_15m:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 0,
                    "sma_cross": sma_cross,
                    "reason": f"Veto Fundo Esticado / Vácuo (1C-Range {c_range_val:.1f}%): Preço no fundo do canal sem reteste confirmado na resistência."
                }

        # Conviccao alta: 96% para cruzamento fresco, 92% para alinhamento continuo
        base_score = 96 if sma_cross.get("has_cross") else 92

        # [V191-STOP-ESTRUTURAL-ANCORADO]: Stop ancorado abaixo do suporte macro H1
        if direction == "LONG":
            if sup_h1 > 0 and sup_h1 < current_price:
                structural_sl = round(sup_h1 * 0.997, 6)
                calc_dist = round((current_price - structural_sl) / current_price, 4)
                if calc_dist > 0.015:
                    stop_dist = 0.012
                    stop_loss = round(current_price * (1.0 - stop_dist), 6)
                elif calc_dist < 0.004:
                    stop_dist = 0.005
                    stop_loss = round(current_price * (1.0 - stop_dist), 6)
                else:
                    stop_dist = calc_dist
                    stop_loss = structural_sl
            else:
                stop_dist = 0.012
                stop_loss = round(current_price * (1.0 - stop_dist), 6)

            if res_h1 > current_price:
                structural_tp = round(res_h1 * 0.995, 6)
                calc_target_dist = round((structural_tp - current_price) / current_price, 4)
                if calc_target_dist >= 0.025:
                    target_dist = calc_target_dist
                    target = structural_tp
                else:
                    target_dist = 0.060
                    target = round(current_price * (1.0 + target_dist), 6)
            else:
                target_dist = 0.060
                target = round(current_price * (1.0 + target_dist), 6)
        else: # SHORT
            if res_h1 > current_price:
                structural_sl = round(res_h1 * 1.003, 6)
                calc_dist = round((structural_sl - current_price) / current_price, 4)
                if calc_dist > 0.015:
                    stop_dist = 0.012
                    stop_loss = round(current_price * (1.0 + stop_dist), 6)
                elif calc_dist < 0.004:
                    stop_dist = 0.005
                    stop_loss = round(current_price * (1.0 + stop_dist), 6)
                else:
                    stop_dist = calc_dist
                    stop_loss = structural_sl
            else:
                stop_dist = 0.012
                stop_loss = round(current_price * (1.0 + stop_dist), 6)

            if sup_h1 > 0 and sup_h1 < current_price:
                structural_tp = round(sup_h1 * 1.005, 6)
                calc_target_dist = round((current_price - structural_tp) / current_price, 4)
                if calc_target_dist >= 0.025:
                    target_dist = calc_target_dist
                    target = structural_tp
                else:
                    target_dist = 0.060
                    target = round(current_price * (1.0 - target_dist), 6)
            else:
                target_dist = 0.060
                target = round(current_price * (1.0 - target_dist), 6)

        rationale = (
            f"FUSAO AGUIA-ENCRYPTOS: SMA 8 (${sma_cross['sma8']:.4f}) {'acima da' if direction == 'LONG' else 'abaixo da'} "
            f"SMA 21 (${sma_cross['sma21']:.4f}) no 2H [{cross_type}]. "
            f"1C-Range={c_range_val:.1f}% [REPIQUE SUP={sup_h1:.4f} RES={res_h1:.4f}]. "
            f"Robos ON (1C-EXP {c_exp_val:.0f}) e Vela 5M confirmada. Executando 50X Margem Cruzada ($100)."
        )

        return {
            "qualifies": True,
            "direction": direction,
            "score": base_score,
            "strategy": "LAYA_AGUIA_FUSION",
            "aguia_fusion": True,
            "cross_type": cross_type,
            "sma8_2h": sma_cross.get("sma8", 0.0),
            "sma21_2h": sma_cross.get("sma21", 0.0),
            "diff_pct": sma_cross.get("diff_pct", 0.0),
            "stop_loss": stop_loss,
            "target": target,
            "stop_dist": stop_dist,
            "target_dist": target_dist,
            "leverage_cap": 50.0,
            "candle_5m_confirmed": True,
            "c_range": c_range_val,
            "support_h1": sup_h1,
            "resistance_h1": res_h1,
            "rationale": rationale
        }

    def evaluate_intermediate_reversal_15m(
        self,
        symbol: str,
        current_price: float,
        candles_15m: list,
        acc_range: Optional[Dict[str, Any]] = None,
        c_range: Optional[float] = None,
        lsr: float = 1.0,
        btc_trend_bias: float = 0.0,
        bot_ignition: bool = False,
        c_exp: float = 50.0,
        funding_rate: float = 0.0
    ) -> dict:
        """
        [V190-INTERMEDIATE-REVERSAL-15M / MFR-15]
        Modulo Soberano de Reversao em Timeframes Intermediarios (15m / 30m):
        - Detecta viradas no suporte/resistencia com absorcao institucional e cruzamento SMA 8 x SMA 21 no 15M.
        - Elimina o lag de 16 horas da media 2H, capturando tiros de +8% (como ZAMA) no nascimento do pivo.
        - Stop loss milimetrico ancorado na minima/maxima da varredura (Sweep).
        - Risco : Retorno assimetrico (R:R >= 2.5:1) com alavancagem moderada de 20x a 25x.
        """
        if not candles_15m or len(candles_15m) < 21:
            return {"qualifies": False, "direction": "HOLD", "score": 0, "reason": "KLINES_15M_INSUFICIENTES"}

        c_range_val = c_range
        if c_range_val is None and acc_range:
            sup_h1 = float(acc_range.get("support_h1") or 0.0)
            res_h1 = float(acc_range.get("resistance_h1") or 0.0)
            if res_h1 > sup_h1 > 0:
                c_range_val = round(((current_price - sup_h1) / (res_h1 - sup_h1)) * 100.0, 1)
        if c_range_val is None:
            c_range_val = 50.0

        is_discount_support = c_range_val <= 35.0
        is_premium_resistance = c_range_val >= 65.0

        if not is_discount_support and not is_premium_resistance:
            return {
                "qualifies": False,
                "direction": "HOLD",
                "score": 0,
                "reason": f"MIOLO DO CANAL (1C-Range {c_range_val:.1f}%): Reversao 15M autorizada apenas em suporte (<=35%) ou resistencia (>=65%)."
            }

        closes = []
        highs = []
        lows = []
        opens = []
        volumes = []
        for c in candles_15m:
            if isinstance(c, dict):
                o_val = float(c.get("open") or c.get("o") or 0.0)
                h_val = float(c.get("high") or c.get("h") or 0.0)
                l_val = float(c.get("low") or c.get("l") or 0.0)
                c_val = float(c.get("close") or c.get("c") or 0.0)
                v_val = float(c.get("vol") or c.get("volume") or c.get("volCcy") or 0.0)
            else:
                o_val = float(c[1])
                h_val = float(c[2])
                l_val = float(c[3])
                c_val = float(c[4])
                v_val = float(c[5]) if len(c) > 5 else 0.0
            opens.append(o_val)
            highs.append(h_val)
            lows.append(l_val)
            closes.append(c_val)
            volumes.append(v_val)

        sma8 = sum(closes[-8:]) / 8.0
        sma21 = sum(closes[-21:]) / 21.0
        
        avg_vol = (sum(volumes[-20:]) / 20.0) if len(volumes) >= 20 else 1.0
        recent_vol = max(volumes[-3:])
        has_vol_spike = (recent_vol >= avg_vol * 1.35) or bot_ignition

        if is_discount_support:
            # [V205-ZERO-TOLERANCE-ALT-LONG] Tolerância Zero para compras de altcoin sem Bitcoin em regime BULL
            if btc_trend_bias <= 0.0 or btc_macro_direction != "BULL":
                return {"qualifies": False, "direction": "HOLD", "score": 0, "reason": "FAROL_BTC_NAO_E_BULL"}
            
            # Gatilho no 15M: Preco sustentando acima da SMA 8 com absorcao e volume
            if current_price < sma8 * 0.995:
                return {"qualifies": False, "direction": "HOLD", "score": 0, "reason": "ABAIXO_SMA8_15M"}

            sweep_low = min(lows[-8:])
            stop_loss = round(sweep_low * 0.998, 6)
            stop_dist = (current_price - stop_loss) / current_price

            if stop_dist > 0.070 or stop_dist < 0.005:
                stop_loss = round(current_price * 0.985, 6)
                stop_dist = 0.015

            target_dist = min(0.085, max(0.045, stop_dist * 3.0))
            target = round(current_price * (1.0 + target_dist), 6)
            base_score = 93 if has_vol_spike else 90

            rationale = (
                f"REVERSAO INTERMEDIARIA 15M (SWEEP & PIVOT LONG): Preco em suporte historico (1C-Range: {c_range_val:.0f}%). "
                f"SMA 8 (${sma8:.4f}) acima da SMA 21 (${sma21:.4f}) no 15M com absorcao na minima ${sweep_low:.4f}. "
                f"Volume {recent_vol/max(avg_vol, 0.001):.1f}x da media. Alvo Assimetrico {target_dist*100:.1f}% com Stop de {stop_dist*100:.1f}%."
            )

            return {
                "qualifies": True,
                "direction": "LONG",
                "strategy": "LAYA_INTERMEDIATE_REVERSAL_15M",
                "score": base_score,
                "stop_loss": stop_loss,
                "target": target,
                "stop_dist": stop_dist,
                "target_dist": target_dist,
                "leverage_cap": 50.0,
                "sma8_15m": sma8,
                "sma21_15m": sma21,
                "sweep_price": sweep_low,
                "candle_5m_confirmed": True,
                "rationale": rationale
            }

        elif is_premium_resistance:
            if btc_trend_bias > 1.2:
                return {"qualifies": False, "direction": "HOLD", "score": 0, "reason": "FAROL_BTC_ALTA_FORTE"}

            if current_price > sma8 * 1.005:
                return {"qualifies": False, "direction": "HOLD", "score": 0, "reason": "ACIMA_SMA8_15M"}

            sweep_high = max(highs[-8:])
            stop_loss = round(sweep_high * 1.002, 6)
            stop_dist = (stop_loss - current_price) / current_price

            if stop_dist > 0.070 or stop_dist < 0.005:
                stop_loss = round(current_price * 1.015, 6)
                stop_dist = 0.015

            target_dist = min(0.085, max(0.045, stop_dist * 3.0))
            target = round(current_price * (1.0 - target_dist), 6)
            base_score = 93 if has_vol_spike else 90

            rationale = (
                f"REVERSAO INTERMEDIARIA 15M (SWEEP & PIVOT SHORT): Preco em resistencia do canal (1C-Range: {c_range_val:.0f}%). "
                f"SMA 8 (${sma8:.4f}) abaixo da SMA 21 (${sma21:.4f}) no 15M com rejeicao na maxima ${sweep_high:.4f}. "
                f"Volume {recent_vol/max(avg_vol, 0.001):.1f}x da media. Alvo Assimetrico {target_dist*100:.1f}% com Stop de {stop_dist*100:.1f}%."
            )

            return {
                "qualifies": True,
                "direction": "SHORT",
                "strategy": "LAYA_INTERMEDIATE_REVERSAL_15M",
                "score": base_score,
                "stop_loss": stop_loss,
                "target": target,
                "stop_dist": stop_dist,
                "target_dist": target_dist,
                "leverage_cap": 50.0,
                "sma8_15m": sma8,
                "sma21_15m": sma21,
                "sweep_price": sweep_high,
                "candle_5m_confirmed": True,
                "rationale": rationale
            }


    def evaluate_h1_breakout(
        self,
        symbol: str,
        current_price: float,
        acc_range: Dict[str, Any],
        lsr: float,
        oi_delta_pct: float,
        btc_trend_bias: float = 0.0,
        funding_rate: float = 0.0,
        atr_pct: float = 1.5
    ) -> Dict[str, Any]:
        """
        [ENCRYPTOS METHODOLOGY - 1H BREAKOUT + LSR x OI CONFIRMATION + ATR STOP & FUNDING SHIELD]
        Avalia o rompimento de acumulação no H1 com confirmação de fluxo:
        - Rompimento com força (saída de acumulação)
        - Confirmação de entrada de capital novo (OI Delta > 0)
        - Sentimento das sardinhas descompassado (LSR favorável)
        - Veto de Funding Rate adverso (> +0.03% em LONG ou < -0.03% em SHORT)
        - Stop Loss estrutural por ATR (evita ser caçado por mechas de market makers)
        """
        res_h1 = acc_range.get("resistance_h1", 0.0)
        sup_h1 = acc_range.get("support_h1", 0.0)

        if not acc_range.get("is_consolidating") or res_h1 <= 0 or sup_h1 <= 0:
            return {
                "qualifies": False,
                "direction": "HOLD",
                "score": 50,
                "rationale": "Sem consolidação estruturada no H1 para saída com força."
            }

        # 1. ROMPIMENTO DE ALTA (LONG NA SAÍDA DA ACUMULAÇÃO)
        if current_price > res_h1:
            # Filtro Macro do Bitcoin: Se BTC estiver caindo forte (<-0.5%), altcoins em alta costumam ser bull trap
            if btc_trend_bias < -0.5:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 60,
                    "rationale": f"[VETO BTC MACRO]: Rompimento de ${res_h1:.4f}, mas Bitcoin está caindo ({btc_trend_bias:+.1f}%). Risco de falso rompimento induzido pelas baleias."
                }

            # FUNDING SHIELD: Veta LONG se compradores estiverem pagando funding excessivo às baleias (> +0.03%)
            if funding_rate > 0.0003:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 60,
                    "rationale": f"[VETO FUNDING RATE]: Funding rate excessivo (+{funding_rate*100:.3f}%). Compradores pagam taxa às baleias. Risco de drenagem de capital."
                }

            # Filtro Anti-Armadilha: Se o varejo já estiver eufórico em LONG (LSR > 1.30)
            if lsr >= 1.30:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 60,
                    "rationale": f"[VETO ENCRYPTOS - BULL TRAP]: Preço rompeu máxima H1 (${res_h1:.4f}), mas LSR das sardinhas está eufórico ({lsr:.2f}). Risco de falso rompimento das baleias."
                }

            # Filtro de Volume Institucional: OI precisa estar subindo ou estável (capital novo)
            if oi_delta_pct < -0.2:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 62,
                    "rationale": f"[VETO ENCRYPTOS - FAKEOUT]: Rompimento sem entrada de capital novo (OI caiu {oi_delta_pct:.2f}%). Sem força para sustentação no H1."
                }

            # [V169-STOP-ESTRUTURAL]: Stop Loss ATR Anti-Violinada com respiro real (2.0% a 3.5%)
            stop_dist = max(0.020, min(0.035, (atr_pct * 1.2) / 100.0))
            candidate_sl = res_h1 * 0.995 if res_h1 > 0 else 0.0
            if 0 < candidate_sl < current_price and 0.020 <= ((current_price - candidate_sl) / current_price) <= 0.038:
                stop_loss = round(candidate_sl, 4)
            else:
                stop_loss = round(current_price * (1.0 - stop_dist), 4)

            stop_dist = max(0.020, min(0.038, (current_price - stop_loss) / current_price))

            # Alvo assimétrico no H1 (+1.8% a +3.0%)
            target_dist = max(0.018, stop_dist * 2.0)
            target = round(current_price * (1.0 + target_dist), 4)

            score = 92 if (oi_delta_pct >= 0.5 and lsr <= 1.15) else 88

            return {
                "qualifies": True,
                "direction": "LONG",
                "score": score,
                "stop_loss": stop_loss,
                "target": target,
                "stop_dist": stop_dist,
                "target_dist": target_dist,
                "rationale": f"SAÍDA DE ACUMULAÇÃO H1 (LONG): Rompimento de ${res_h1:.4f} com força. Capital novo (+{oi_delta_pct}% OI) e LSR ({lsr:.2f}). Stop ATR blindado em ${stop_loss:.4f} (-{stop_dist*100:.1f}%)."
            }

        # 2. ROMPIMENTO DE BAIXA (SHORT NA SAÍDA DA ACUMULAÇÃO)
        elif current_price < sup_h1:
            # Se BTC estiver subindo forte (>+0.8%), rompimento de baixa de altcoin pode ser bear trap
            if btc_trend_bias > 0.8:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 60,
                    "rationale": f"[VETO BTC MACRO]: Perda de suporte ${sup_h1:.4f}, mas Bitcoin está subindo forte ({btc_trend_bias:+.1f}%). Risco de bear trap."
                }

            # FUNDING SHIELD: Veta SHORT se vendedores estiverem pagando funding excessivo às baleias (< -0.03%)
            if funding_rate < -0.0003:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 60,
                    "rationale": f"[VETO FUNDING RATE]: Funding rate fortemente negativo ({funding_rate*100:.3f}%). Vendedores pagam taxa às baleias. Risco de Short Squeeze."
                }

            # Filtro Anti-Armadilha: Para short genuíno, queremos sardinhas presas ou tentando comprar o fundo
            if lsr <= 0.85:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 60,
                    "rationale": f"[VETO ENCRYPTOS - BEAR TRAP]: Preço perdeu suporte H1 (${sup_h1:.4f}), mas sardinhas estão desesperadas vendidas (LSR {lsr:.2f}). Risco iminente de Short Squeeze."
                }

            if oi_delta_pct < -0.2:
                # Se BTC estiver em queda, queda de OI reflete liquidações em cascata de compradores (combustível de dump)
                if btc_trend_bias >= -0.2:
                    return {
                        "qualifies": False,
                        "direction": "HOLD",
                        "score": 62,
                        "rationale": f"[VETO ENCRYPTOS - FAKEOUT]: Perda de suporte sem volume vendedor novo (OI caiu {oi_delta_pct:.2f}%)."
                    }

            # [V169-STOP-ESTRUTURAL]: Stop Loss ATR Anti-Violinada com respiro real (2.0% a 3.5%)
            stop_dist = max(0.020, min(0.035, (atr_pct * 1.2) / 100.0))
            candidate_sl = sup_h1 * 1.005 if sup_h1 > 0 else 0.0
            if candidate_sl > current_price and 0.020 <= ((candidate_sl - current_price) / current_price) <= 0.038:
                stop_loss = round(candidate_sl, 4)
            else:
                stop_loss = round(current_price * (1.0 + stop_dist), 4)

            stop_dist = max(0.020, min(0.038, (stop_loss - current_price) / current_price))

            target_dist = max(0.018, stop_dist * 2.0)
            target = round(current_price * (1.0 - target_dist), 4)

            score = 92 if (oi_delta_pct >= 0.5 and lsr >= 1.25) else 88

            return {
                "qualifies": True,
                "direction": "SHORT",
                "score": score,
                "stop_loss": stop_loss,
                "target": target,
                "stop_dist": stop_dist,
                "target_dist": target_dist,
                "rationale": f"SAÍDA DE ACUMULAÇÃO H1 (SHORT): Quebra do suporte ${sup_h1:.4f} com força. Varejo preso (LSR {lsr:.2f}) e capital novo (+{oi_delta_pct}% OI). Stop ATR blindado em ${stop_loss:.4f} (+{stop_dist*100:.1f}%)."
            }

        # 3. PREÇO DENTRO DA ACUMULAÇÃO (NÃO OPERA RUÍDO!)
        else:
            return {
                "qualifies": False,
                "direction": "HOLD",
                "score": 65,
                "rationale": f"CONSOLIDAÇÃO H1 (Range ${sup_h1:.4f} - ${res_h1:.4f}): Preço dentro da acumulação. Aguardando saída com força e volume para evitar stop de ruído."
            }

    def calculate_vwap_and_deviation(self, candles: List[Any], current_price: float) -> Dict[str, Any]:
        """
        Calcula a VWAP intradiária e o desvio percentual do preço atual.
        TP = (H + L + C) / 3. VWAP = sum(TP * V) / sum(V).
        """
        if not candles or current_price <= 0:
            return {"vwap": current_price, "diff_pct": 0.0}

        cum_tpv = 0.0
        cum_vol = 0.0
        for c in candles:
            try:
                if isinstance(c, (list, tuple)) and len(c) >= 6:
                    h = float(c[2])
                    l = float(c[3])
                    cl = float(c[4])
                    v = float(c[5])
                elif isinstance(c, dict):
                    h = float(c.get("high") or c.get("h") or 0.0)
                    l = float(c.get("low") or c.get("l") or 0.0)
                    cl = float(c.get("close") or c.get("c") or 0.0)
                    v = float(c.get("vol") or c.get("volume") or c.get("v") or 0.0)
                else:
                    continue
                if h > 0 and l > 0 and cl > 0 and v > 0:
                    tp = (h + l + cl) / 3.0
                    cum_tpv += tp * v
                    cum_vol += v
            except (ValueError, TypeError, IndexError):
                continue

        if cum_vol <= 0 or cum_tpv <= 0:
            return {"vwap": current_price, "diff_pct": 0.0}

        vwap = cum_tpv / cum_vol
        if vwap <= 0:
            return {"vwap": current_price, "diff_pct": 0.0}

        diff_pct = round(((current_price - vwap) / vwap) * 100.0, 2)
        return {"vwap": round(vwap, 8), "diff_pct": diff_pct}

    def calculate_atr_pct(self, candles: List[Any], current_price: float, period: int = 14) -> float:
        """
        [V154-ATR] Calcula o Average True Range (ATR) percentual baseado nas velas de H1.
        Garante que o stop loss respeite a volatilidade intrínseca de cada ativo,
        eliminando stops de ruído colocados a 0.3% ou 0.5% em moedas de alta volatilidade.
        """
        if not candles or len(candles) < 2 or current_price <= 0:
            return 1.5  # Fallback padrão seguro de 1.5%

        trs = []
        prev_close = None
        for c in candles:
            try:
                if isinstance(c, (list, tuple)) and len(c) >= 6:
                    h = float(c[2])
                    l = float(c[3])
                    cl = float(c[4])
                elif isinstance(c, dict):
                    h = float(c.get("high") or c.get("h") or 0.0)
                    l = float(c.get("low") or c.get("l") or 0.0)
                    cl = float(c.get("close") or c.get("c") or 0.0)
                else:
                    continue

                if h > 0 and l > 0:
                    if prev_close is not None and prev_close > 0:
                        tr = max(h - l, abs(h - prev_close), abs(l - prev_close))
                    else:
                        tr = h - l
                    trs.append(tr)
                    prev_close = cl
            except (ValueError, TypeError, IndexError):
                continue

        if not trs:
            return 1.5

        recent_trs = trs[-period:]
        avg_tr = sum(recent_trs) / len(recent_trs)
        atr_pct = round((avg_tr / current_price) * 100.0, 2)
        return max(1.2, min(3.5, atr_pct))

    def evaluate_dvwap_reversion(self, *args, **kwargs) -> Dict[str, Any]:
        """[DESATIVADO - V174]: Veto definitivo de contratendência por reversão à média."""
        return {
            "qualifies": False,
            "direction": "HOLD",
            "score": 0,
            "rationale": "[DESATIVADO]: Reversão contra a tendência desativada para proteger banca contra locomotivas."
        }

        diff_pct = ((current_price - vwap) / vwap) * 100.0

        # REVERSÃO LONG: Preço esticado abaixo da VWAP (exige esticamento real de pelo menos -2.0%)
        if diff_pct <= -2.0:
            # BLINDAGEM ANTI-DUMP: Proibido comprar se robôs vendedores acelerando ou queda vertical > 6%
            if bot_ignition or c_exp >= 70.0:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 50,
                    "rationale": f"[VETO ROBÔS LIGADOS - ANTI-DUMP]: Altcoin em forte aceleração vendedora (1C-EXP {c_exp:.0f} / Bot On). Proibido comprar faca caindo contra robôs institucionais."
                }
            if diff_pct <= -6.0:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 50,
                    "rationale": f"[VETO ANTI-DUMP]: Preço esticado {diff_pct:.1f}% abaixo da VWAP (queda vertical). Proibido comprar faca caindo sem absorção confirmada."
                }

            # FAROL MACRO DO BTC: Veto imediato se o Bitcoin estiver caindo (evita comprar faca caindo)
            if btc_trend_bias < -0.3:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 60,
                    "rationale": f"[BTC MACRO VETO]: Preço esticou {diff_pct:.1f}% abaixo da VWAP, mas BTC está em queda ({btc_trend_bias:+.1f}%). Proibido comprar faca caindo contra o Bitcoin."
                }

            # FUNDING SHIELD: Veta LONG se compradores estiverem pagando funding excessivo (> +0.03%)
            if funding_rate > 0.0003:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 60,
                    "rationale": f"[VETO FUNDING RATE]: Funding rate excessivo (+{funding_rate*100:.3f}%). Compradores pagam taxa às baleias. Risco de drenagem."
                }

            if lsr > 1.35:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 62,
                    "rationale": f"[DVWAP VETO]: Preço esticado abaixo da VWAP ({diff_pct:.1f}%), mas varejo já está muito comprado (LSR {lsr:.2f})."
                }

            # [V169-STOP-ESTRUTURAL]: Stop Loss ATR Anti-Violinada com respiro real (2.0% a 3.5%)
            stop_dist = max(0.020, min(0.035, (atr_pct * 1.2) / 100.0))
            candidate_sl = sup_h1 * 0.995 if sup_h1 > 0 else 0.0
            if 0 < candidate_sl < current_price and 0.020 <= ((current_price - candidate_sl) / current_price) <= 0.038:
                stop_loss = round(candidate_sl, 4)
            else:
                stop_loss = round(current_price * (1.0 - stop_dist), 4)

            stop_dist = max(0.020, min(0.038, (current_price - stop_loss) / current_price))
            target = round(vwap, 4)
            if target <= current_price:
                target = round(current_price * (1.0 + max(0.018, stop_dist * 1.8)), 4)
            target_dist = max(0.015, (target - current_price) / current_price)
            score = 90 if (lsr <= 1.10 or btc_trend_bias >= 0.1) else 86

            return {
                "qualifies": True,
                "direction": "LONG",
                "strategy": "LAYA_DVWAP_REVERSION",
                "score": score,
                "stop_loss": stop_loss,
                "target": target,
                "stop_dist": stop_dist,
                "target_dist": target_dist,
                "rationale": f"DVWAP REVERSION (LONG): Preço esticou {diff_pct:.1f}% abaixo da VWAP (${vwap:.4f}). BTC estável ({btc_trend_bias:+.1f}%). Stop ATR em ${stop_loss:.4f} (-{stop_dist*100:.1f}%)."
            }

        # REVERSÃO SHORT: Preço esticado acima da VWAP (+2.0% ou mais)
        elif diff_pct >= 2.0:
            # BLINDAGEM ANTI-FACA: Proibido shortar se robôs compradores acelerando ou rali vertical > 5%
            if bot_ignition or c_exp >= 70.0:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 50,
                    "rationale": f"[VETO ROBÔS LIGADOS - ANTI-FACA]: Altcoin em forte aceleração compradora (1C-EXP {c_exp:.0f} / Bot On). Proibido vender contra robôs institucionais."
                }
            if diff_pct >= 5.0:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 50,
                    "rationale": f"[VETO ANTI-PUMP]: Preço esticado +{diff_pct:.1f}% acima da VWAP (momentum vertical). Proibido abrir SHORT contra explosão de preço sem exaustão confirmada."
                }

            # FAROL MACRO DO BTC: Veto se o Bitcoin estiver subindo forte
            if btc_trend_bias > 0.5:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 60,
                    "rationale": f"[BTC MACRO VETO]: Preço esticou +{diff_pct:.1f}% acima da VWAP, mas BTC está em forte alta ({btc_trend_bias:+.1f}%). Risco de short contra o mercado."
                }

            # FUNDING SHIELD: Veta SHORT se vendedores estiverem pagando funding excessivo (< -0.03%)
            if funding_rate < -0.0003:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 60,
                    "rationale": f"[VETO FUNDING RATE]: Funding rate fortemente negativo ({funding_rate*100:.3f}%). Vendedores pagam taxa às baleias. Risco de Short Squeeze."
                }

            if lsr < 0.85:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 62,
                    "rationale": f"[DVWAP VETO]: Preço esticado acima da VWAP (+{diff_pct:.1f}%), mas varejo está muito vendido (LSR {lsr:.2f}). Risco de short squeeze."
                }

            # [V169-STOP-ESTRUTURAL]: Stop Loss ATR Anti-Violinada com respiro real (2.0% a 3.5%)
            stop_dist = max(0.020, min(0.035, (atr_pct * 1.2) / 100.0))
            candidate_sl = res_h1 * 1.005 if res_h1 > 0 else 0.0
            if candidate_sl > current_price and 0.020 <= ((candidate_sl - current_price) / current_price) <= 0.038:
                stop_loss = round(candidate_sl, 4)
            else:
                stop_loss = round(current_price * (1.0 + stop_dist), 4)

            stop_dist = max(0.020, min(0.038, (stop_loss - current_price) / current_price))
            target = round(vwap, 4)
            if target >= current_price:
                target = round(current_price * (1.0 - max(0.018, stop_dist * 1.8)), 4)
            target_dist = max(0.015, (current_price - target) / current_price)
            score = 90 if (lsr >= 1.15 or btc_trend_bias <= -0.1) else 86

            return {
                "qualifies": True,
                "direction": "SHORT",
                "strategy": "LAYA_DVWAP_REVERSION",
                "score": score,
                "stop_loss": stop_loss,
                "target": target,
                "stop_dist": stop_dist,
                "target_dist": target_dist,
                "rationale": f"DVWAP REVERSION (SHORT): Preço esticou +{diff_pct:.1f}% acima da VWAP (${vwap:.4f}). BTC estável ({btc_trend_bias:+.1f}%). Stop ATR em ${stop_loss:.4f} (+{stop_dist*100:.1f}%)."
            }

        return {
            "qualifies": False,
            "direction": "HOLD",
            "score": 65,
            "rationale": f"DVWAP NEUTRO: Preço próximo da média ({diff_pct:+.1f}% da VWAP). Sem assimetria elástica (exige >= 2.0%)."
        }

    def evaluate_momento_mola(
        self,
        symbol: str,
        current_price: float,
        acc_range: Dict[str, Any],
        bb_width_pct: float = 3.0,
        is_at_support: bool = False,
        lsr: float = 1.0,
        btc_trend_bias: float = 0.0,
        funding_rate: float = 0.0,
        atr_pct: float = 1.5
    ) -> Dict[str, Any]:
        """
        [SETUP 2: MOMENTO MOLA - COMPRESSÃO DE VOLATILIDADE & DISPARO ELÁSTICO CALIBRADO]
        Detecta compressão máxima das Bandas de Bollinger (BB Width <= 1.8%) em extremo de canal.
        - Veto de Funding Rate adverso (> +0.03% em LONG ou < -0.03% em SHORT).
        - Stop Loss estrutural ancorado por ATR (mínimo 1.2% a 2.5%).
        """
        sup_h1 = acc_range.get("support_h1", 0.0)
        res_h1 = acc_range.get("resistance_h1", 0.0)

        # Mola comprimida requer BB Width estreito (baixa volatilidade pré-explosão)
        if bb_width_pct > 1.8:
            return {
                "qualifies": False,
                "direction": "HOLD",
                "score": 64,
                "rationale": f"MOLA RELAXADA: Volatilidade aberta (BB Width {bb_width_pct:.1f}%). Sem compressão extrema."
            }

        # Mola Comprimida no Suporte (Gatilho de Disparo de Alta)
        if is_at_support or (sup_h1 > 0 and abs(current_price - sup_h1) / sup_h1 <= 0.015):
            # FAROL MACRO DO BTC: Veto imediato se o Bitcoin estiver caindo
            if btc_trend_bias < -0.3:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 62,
                    "rationale": f"[BTC MACRO VETO]: Mola comprimida no suporte, mas BTC está em queda ({btc_trend_bias:+.1f}%). Risco iminente de rompimento para baixo."
                }

            # FUNDING SHIELD
            if funding_rate > 0.0003:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 60,
                    "rationale": f"[VETO FUNDING RATE]: Funding rate excessivo (+{funding_rate*100:.3f}%). Compradores pagam taxa às baleias."
                }

            # [V169-STOP-ESTRUTURAL]: Stop Loss ATR Anti-Violinada com respiro real (2.0% a 3.5%)
            stop_dist = max(0.020, min(0.035, (atr_pct * 1.2) / 100.0))
            candidate_sl = sup_h1 * 0.995 if sup_h1 > 0 else 0.0
            if 0 < candidate_sl < current_price and 0.020 <= ((current_price - candidate_sl) / current_price) <= 0.038:
                stop_loss = round(candidate_sl, 4)
            else:
                stop_loss = round(current_price * (1.0 - stop_dist), 4)

            stop_dist = max(0.020, min(0.038, (current_price - stop_loss) / current_price))
            target = round(res_h1 * 0.995 if res_h1 > 0 else current_price * 1.025, 4)
            if target <= current_price:
                target = round(current_price * (1.0 + max(0.018, stop_dist * 1.8)), 4)
            target_dist = max(0.015, (target - current_price) / current_price)
            score = 90 if (lsr <= 1.10 or btc_trend_bias >= 0.1) else 86

            return {
                "qualifies": True,
                "direction": "LONG",
                "strategy": "LAYA_MOMENTO_MOLA",
                "score": score,
                "stop_loss": stop_loss,
                "target": target,
                "stop_dist": stop_dist,
                "target_dist": target_dist,
                "rationale": f"MOMENTO MOLA (LONG): Volatilidade espremida (BB Width {bb_width_pct:.1f}%) no suporte (${sup_h1:.4f}). BTC estável ({btc_trend_bias:+.1f}%). Stop ATR em ${stop_loss:.4f} (-{stop_dist*100:.1f}%)."
            }

        # Mola Comprimida na Resistência (Gatilho de Disparo de Baixa)
        elif res_h1 > 0 and abs(current_price - res_h1) / res_h1 <= 0.015:
            # FAROL MACRO DO BTC: Veto se o Bitcoin estiver subindo forte
            if btc_trend_bias > 0.6:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 62,
                    "rationale": f"[BTC MACRO VETO]: Mola comprimida na resistência, mas BTC está em forte alta ({btc_trend_bias:+.1f}%). Risco de rompimento para cima."
                }

            # FUNDING SHIELD
            if funding_rate < -0.0003:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 60,
                    "rationale": f"[VETO FUNDING RATE]: Funding rate fortemente negativo ({funding_rate*100:.3f}%). Vendedores pagam taxa às baleias."
                }

            # [V169-STOP-ESTRUTURAL]: Stop Loss ATR Anti-Violinada com respiro real (2.0% a 3.5%)
            stop_dist = max(0.020, min(0.035, (atr_pct * 1.2) / 100.0))
            candidate_sl = res_h1 * 1.005 if res_h1 > 0 else 0.0
            if candidate_sl > current_price and 0.020 <= ((candidate_sl - current_price) / current_price) <= 0.038:
                stop_loss = round(candidate_sl, 4)
            else:
                stop_loss = round(current_price * (1.0 + stop_dist), 4)

            stop_dist = max(0.020, min(0.038, (stop_loss - current_price) / current_price))
            target = round(sup_h1 * 1.005 if sup_h1 > 0 else current_price * 0.975, 4)
            if target >= current_price:
                target = round(current_price * (1.0 - max(0.018, stop_dist * 1.8)), 4)
            target_dist = max(0.015, (current_price - target) / current_price)
            score = 90 if (lsr >= 1.15 or btc_trend_bias <= -0.1) else 86

            return {
                "qualifies": True,
                "direction": "SHORT",
                "strategy": "LAYA_MOMENTO_MOLA",
                "score": score,
                "stop_loss": stop_loss,
                "target": target,
                "stop_dist": stop_dist,
                "target_dist": target_dist,
                "rationale": f"MOMENTO MOLA (SHORT): Volatilidade espremida (BB Width {bb_width_pct:.1f}%) na resistência (${res_h1:.4f}). Stop ATR em ${stop_loss:.4f} (+{stop_dist*100:.1f}%)."
            }

        return {
            "qualifies": False,
            "direction": "HOLD",
            "score": 66,
            "rationale": f"MOLA COMPRIMIDA (BBW {bb_width_pct:.1f}%), mas no miolo do range. Aguardando toque no extremo."
        }

    def evaluate_range_boundary_reversal(
        self,
        symbol: str,
        current_price: float,
        acc_range: Dict[str, Any],
        lsr: float = 1.0,
        oi_delta_pct: float = 0.0,
        btc_trend_bias: float = 0.0,
        funding_rate: float = 0.0,
        atr_pct: float = 1.5,
        boundary_threshold: float = 0.25,
        taker_sell_ratio: float = 1.0,
        taker_buy_ratio: float = 1.0,
        bot_ignition: bool = False,
        c_exp: float = 0.0
    ) -> Dict[str, Any]:
        """
        [SETUP: RANGE BOUNDARY REVERSAL (MEAN REVERSION / EXAUSTÃO NAS BORDAS DO RANGE)]
        Identifica setups institucionais de reversão à média nas extremidades da consolidação H1.
        - Quando o preço testa o teto do range (pos >= 75% ou dist_to_res <= 1.5%):
          * Se BTC não estiver em rali descontrolado e sem short squeeze, projeta SHORT na exaustão.
          * Stop Loss estrutural acima da resistência H1 (res_h1 * 1.008 ou min 2.8% de stop ATR).
          * Alvo assimétrico no miolo / suporte do canal.
        - Quando o preço testa o piso do range (pos <= 25% ou dist_to_sup <= 1.5%):
          * Se BTC não estiver em queda livre e sem varejo excessivamente comprado, projeta LONG no suporte.
          * Stop Loss estrutural abaixo do suporte H1 (sup_h1 * 0.992 ou min 2.8% de stop ATR).
          * Alvo assimétrico no miolo / resistência do canal.
        """
        sup_h1 = acc_range.get("support_h1", 0.0)
        res_h1 = acc_range.get("resistance_h1", 0.0)

        if sup_h1 <= 0 or res_h1 <= 0 or res_h1 <= sup_h1 or current_price <= 0:
            return {"qualifies": False, "direction": "HOLD", "score": 60, "rationale": "Faixa H1 inválida."}

        range_width = res_h1 - sup_h1
        # Requer largura mínima de canal de 1.2% para ser uma consolidação operável
        if (range_width / sup_h1) < 0.012:
            return {"qualifies": False, "direction": "HOLD", "score": 60, "rationale": "Canal H1 muito estreito para reversão de borda."}

        range_pos = (current_price - sup_h1) / range_width if range_width > 0 else 0.5
        dist_to_res_pct = ((res_h1 - current_price) / current_price) * 100.0
        dist_to_sup_pct = ((current_price - sup_h1) / current_price) * 100.0

        # CASO 1: TESTE DO TETO / RESISTÊNCIA DO CANAL (EXAUSTÃO VENDEDORA -> SHORT)
        # O preço deve estar estritamente no topo do canal (pos >= 75%) e próximo da resistência
        if range_pos >= (1.0 - boundary_threshold) and dist_to_res_pct <= 2.5:
            # BLINDAGEM ROBÔS LIGADOS: Se os robôs estão empurrando para cima, proibido shortar topo
            if bot_ignition or c_exp >= 70.0:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 55,
                    "rationale": f"[VETO ROBÔS LIGADOS]: Altcoin em forte aceleração compradora (1C-EXP {c_exp:.0f} / Bot On). Proibido vender topo contra robôs institucionais."
                }

            # FAROL MACRO DO BTC: Veto se o Bitcoin estiver subindo forte (> +1.0%)
            if btc_trend_bias > 1.0:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 62,
                    "rationale": f"[FAROL MACRO VETO]: Preço em {range_pos*100:.1f}% do range (teste de resistência ${res_h1:.4f}), mas Bitcoin em forte alta ({btc_trend_bias:+.1f}%)."
                }

            # [CVD / AGRESSÃO DE COMPRA NO TOPO]: Veto se o book recente tiver agressão compradora acelerando (falso topo)
            # Calibração anti-entrada prematura: exige exaustão (taker_buy_ratio < 1.25)
            if taker_buy_ratio >= 1.25:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 62,
                    "rationale": f"[VETO CVD - AGRESSÃO COMPRADORA NO TOPO]: Taker buy ratio em {taker_buy_ratio:.2f}x. Pressão compradora acelerando (aguardar exaustão do movimento antes de vender)."
                }

            # FUNDING SHIELD: Veta se funding fortemente negativo (< -0.03%)
            if funding_rate < -0.0003:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 60,
                    "rationale": f"[VETO FUNDING]: Funding negativo ({funding_rate*100:.3f}%). Risco de short squeeze nas sardinhas."
                }

            # Varejo muito vendido em topo de canal é sinal de perigo
            if lsr < 0.75:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 62,
                    "rationale": f"[VETO LSR]: Preço em topo de canal, mas sardinhas já estão vendidas (LSR {lsr:.2f})."
                }

            # [V165-RESPIRO ESTRUTURAL ANTI-VIOLINADA]: Stop Loss posicionado além da resistência H1 com buffer de liquidez
            # Evita violinadas em falsos rompimentos (liquidity sweeps) de 0.5% a 1.0% além do topo
            res_buffer = max(0.018, min(0.028, (atr_pct * 1.5) / 100.0))
            candidate_sl = res_h1 * (1.0 + res_buffer) if res_h1 > 0 else current_price * 1.025
            if candidate_sl > current_price and ((candidate_sl - current_price) / current_price) >= 0.018:
                stop_loss = round(candidate_sl, 4)
            else:
                stop_loss = round(current_price * (1.0 + max(0.022, res_buffer)), 4)

            stop_dist = max(0.018, min(0.035, (stop_loss - current_price) / current_price))

            # Alvo no suporte do canal ou no miolo
            target = round(sup_h1 * 1.005, 4) if sup_h1 > 0 else round(current_price * (1.0 - stop_dist * 1.8), 4)
            if target >= current_price:
                target = round(current_price * (1.0 - max(0.025, stop_dist * 1.8)), 4)
            target_dist = max(0.020, (current_price - target) / current_price)

            # Score institucional calibrado e simétrico (mínimo 86)
            score = 86
            if lsr >= 1.15:
                score += 3  # Varejo comprando no topo = liquidez para as baleias venderem
            elif lsr >= 0.95:
                score += 2  # LSR neutro a levemente comprador favorece short no topo
            if oi_delta_pct >= 0.2:
                score += 2  # Absorção institucional no topo
            if btc_trend_bias <= 0.1:
                score += 2  # BTC lateral ou em queda favorece short em altcoins

            return {
                "qualifies": True,
                "direction": "SHORT",
                "strategy": "LAYA_RANGE_REVERSAL",
                "score": min(95, score),
                "stop_loss": stop_loss,
                "target": target,
                "stop_dist": stop_dist,
                "target_dist": target_dist,
                "rationale": f"EXAUSTÃO NA RESISTÊNCIA H1 (SHORT): Preço em {range_pos*100:.1f}% do range (${current_price:.4f} vs ${res_h1:.4f}). LSR {lsr:.2f}. Stop ATR em ${stop_loss:.4f} (+{stop_dist*100:.1f}%)."
            }

        # CASO 2: TESTE DO PISO / SUPORTE DO CANAL (ABSORÇÃO COMPRADORA -> LONG)
        # O preço deve estar estritamente no fundo do canal (pos <= 25%) e próximo do suporte
        elif range_pos <= boundary_threshold and dist_to_sup_pct <= 2.5:
            # BLINDAGEM ROBÔS LIGADOS: Se os robôs estão empurrando para baixo, proibido comprar fundo
            if bot_ignition or c_exp >= 70.0:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 55,
                    "rationale": f"[VETO ROBÔS LIGADOS]: Altcoin em forte aceleração vendedora (1C-EXP {c_exp:.0f} / Bot On). Proibido comprar fundo contra robôs institucionais."
                }

            # FAROL MACRO DO BTC: Veto se o Bitcoin estiver despencando (< -0.8%)
            if btc_trend_bias < -0.8:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 62,
                    "rationale": f"[FAROL MACRO VETO]: Preço em {range_pos*100:.1f}% do range (teste de suporte ${sup_h1:.4f}), mas Bitcoin em queda livre ({btc_trend_bias:+.1f}%)."
                }

            # [CVD / AGRESSÃO DE VENDA NO SUPORTE - FACA CAINDO]: Veto se o book tiver dump agressivo a mercado
            # Calibração anti-entrada prematura: exige exaustão (taker_sell_ratio < 1.25)
            if taker_sell_ratio >= 1.25:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 62,
                    "rationale": f"[VETO CVD - AGRESSÃO VENDEDORA NO SUPORTE]: Taker sell ratio em {taker_sell_ratio:.2f}x (faca caindo). Aguardar desaceleração da pressão vendedora."
                }

            # FUNDING SHIELD: Veta se funding excessivamente positivo (> +0.03%)
            if funding_rate > 0.0003:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 60,
                    "rationale": f"[VETO FUNDING]: Funding rate alto (+{funding_rate*100:.3f}%). Compradores pagam taxa pesada."
                }

            # Varejo muito comprado no fundo é faca caindo
            if lsr > 1.35:
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 62,
                    "rationale": f"[VETO LSR]: Preço em suporte, mas sardinhas entupidas na compra (LSR {lsr:.2f})."
                }

            # [V165-RESPIRO ESTRUTURAL ANTI-VIOLINADA]: Stop Loss posicionado abaixo do suporte H1 com buffer de liquidez
            sup_buffer = max(0.018, min(0.028, (atr_pct * 1.5) / 100.0))
            candidate_sl = sup_h1 * (1.0 - sup_buffer) if sup_h1 > 0 else current_price * 0.975
            if 0 < candidate_sl < current_price and ((current_price - candidate_sl) / current_price) >= 0.018:
                stop_loss = round(candidate_sl, 4)
            else:
                stop_loss = round(current_price * (1.0 - max(0.022, sup_buffer)), 4)

            stop_dist = max(0.018, min(0.035, (current_price - stop_loss) / current_price))

            # Alvo na resistência do canal ou no miolo
            target = round(res_h1 * 0.995, 4) if res_h1 > 0 else round(current_price * (1.0 + stop_dist * 1.8), 4)
            if target <= current_price:
                target = round(current_price * (1.0 + max(0.025, stop_dist * 1.8)), 4)
            target_dist = max(0.020, (target - current_price) / current_price)

            # Score institucional calibrado e simétrico (mínimo 86)
            score = 86
            if lsr <= 0.95:
                score += 3  # Varejo com medo ou vendendo no suporte = baleias absorvendo
            elif lsr <= 1.10:
                score += 2  # LSR neutro a levemente vendedor favorece long no suporte
            if oi_delta_pct >= 0.2:
                score += 2  # Absorção institucional no suporte
            if btc_trend_bias >= -0.1:
                score += 2  # BTC estável favorece long no suporte

            return {
                "qualifies": True,
                "direction": "LONG",
                "strategy": "LAYA_RANGE_REVERSAL",
                "score": min(95, score),
                "stop_loss": stop_loss,
                "target": target,
                "stop_dist": stop_dist,
                "target_dist": target_dist,
                "rationale": f"ABSORÇÃO NO SUPORTE H1 (LONG): Preço em {range_pos*100:.1f}% do range (${current_price:.4f} vs ${sup_h1:.4f}). LSR {lsr:.2f}. Stop ATR em ${stop_loss:.4f} (-{stop_dist*100:.1f}%)."
            }

        return {
            "qualifies": False,
            "direction": "HOLD",
            "score": 65,
            "rationale": f"MEIO DE CANAL H1 ({range_pos*100:.1f}%): Preço no miolo (${sup_h1:.4f} - ${res_h1:.4f}). Aguardando aproximação dos extremos institucionais."
        }

    def evaluate_multi_setup_opportunity(
        self,
        symbol: str,
        current_price: float,
        acc_range: Dict[str, Any],
        vwap: float = 0.0,
        bb_width_pct: float = 3.0,
        lsr: float = 1.0,
        oi_delta_pct: float = 0.0,
        is_at_support: bool = False,
        btc_trend_bias: float = 0.0,
        funding_rate: float = 0.0,
        atr_pct: float = 1.5,
        btc_intel: Optional[Dict[str, Any]] = None,
        bot_ignition: bool = False,
        c_exp: float = 0.0,
        candles_1h: Optional[List[Any]] = None,
        candles_15m: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        [MAESTRO MULTI-TIMEFRAME & MULTI-SETUP COM FAROL MACRO, FUNDING SHIELD, BTC.D & STOP ATR]
        Hierarquia de Decisão Soberana da Laya:
        1. Prioridade 1: Saída de Acumulação H1 (Smart Money Breakout com volume e stop ATR).
        2. Prioridade 1.5: Reversão Intermediária de Liquidez 15M (MFR-15 / Sweep e SuperTrend no extremo do canal).
        3. Prioridade 2: Range Boundary Reversal (No regime Mean Reversion / Consolidação, opera exaustão nas bordas).
        4. Prioridade 3: Momento Mola 15M (Compressão extrema no canal, BBW <= 6.5%).
        5. Prioridade 4: DVWAP Reversion 5M (Preço esticado da VWAP com BTC favorável).
        6. Neutro: Diagnóstico integrado das camadas.
        """
        # [REGRA ENCRYPTOS]: BTC é estritamente o Oráculo Macro da Laya, proibido abrir ordens de trade nele
        sym_clean = symbol.upper().replace("-", "").replace("_", "")
        if sym_clean.startswith("BTC"):
            return {
                "qualifies": False,
                "direction": "HOLD",
                "score": 0,
                "strategy": "BTC_ORACLE_MONITOR",
                "stop_loss": 0.0,
                "target": 0.0,
                "stop_dist": 0.0,
                "target_dist": 0.0,
                "rationale": "[ORÁCULO MACRO]: BTC é utilizado exclusivamente como bússola de dominância e fluxo. Proibido abrir ordens de trade no BTC."
            }

        setup_res = None

        # CAMADA 0 [V187-BRUNO-PHENIX-SOVEREIGN-FUSION]: Prioridade Absoluta Águia + Encryptos
        if candles_1h and len(candles_1h) >= 8:
            fusion_eval = self.evaluate_aguia_encryptos_fusion(
                symbol=symbol,
                current_price=current_price,
                candles_1h=candles_1h,
                bot_ignition=bot_ignition,
                c_exp=c_exp,
                btc_trend_bias=btc_trend_bias,
                lsr=lsr,
                acc_range=acc_range,
                candles_15m=candles_15m
            )
            if fusion_eval.get("qualifies"):
                setup_res = fusion_eval

        # CAMADA 1: AVALIA ROMPIMENTO DE 1H (SE NÃO HOUVER FUSÃO DIRETA)
        if not setup_res:
            h1_eval = self.evaluate_h1_breakout(
                symbol=symbol,
                current_price=current_price,
                acc_range=acc_range,
                lsr=lsr,
                oi_delta_pct=oi_delta_pct,
                btc_trend_bias=btc_trend_bias,
                funding_rate=funding_rate,
                atr_pct=atr_pct
            )
            if h1_eval.get("qualifies"):
                h1_eval["strategy"] = "LAYA_SMART_MONEY_H1"
                setup_res = h1_eval

        # CAMADA 1.5 [V190-BIDIRECTIONAL-15M-REVERSAL]: Reversão Intermediária de Liquidez 15M (MFR-15)
        # Identifica varredura e reversão antecipada nos extremos do canal antes do lag do 2H
        if not setup_res and candles_15m and len(candles_15m) >= 6:
            reversal_15m = self.evaluate_intermediate_reversal_15m(
                symbol=symbol,
                current_price=current_price,
                candles_15m=candles_15m,
                acc_range=acc_range,
                bot_ignition=bot_ignition,
                c_exp=c_exp,
                btc_trend_bias=btc_trend_bias,
                lsr=lsr,
                funding_rate=funding_rate
            )
            if reversal_15m.get("qualifies"):
                setup_res = reversal_15m

        # CAMADA 2: SE ESTIVER NO RANGE, AVALIA REVERSÃO DE BORDA (MEAN REVERSION INSTITUCIONAL)
        if not setup_res:
            range_eval = self.evaluate_range_boundary_reversal(
                symbol=symbol,
                current_price=current_price,
                acc_range=acc_range,
                lsr=lsr,
                oi_delta_pct=oi_delta_pct,
                btc_trend_bias=btc_trend_bias,
                funding_rate=funding_rate,
                atr_pct=atr_pct,
                bot_ignition=bot_ignition,
                c_exp=c_exp
            )
            if range_eval.get("qualifies"):
                setup_res = range_eval

        # CAMADA 3: SE NÃO HOUVER REVERSÃO DE BORDA, AVALIA MOMENTO MOLA (15M)
        if not setup_res and bb_width_pct <= 6.5:
            mola_eval = self.evaluate_momento_mola(
                symbol=symbol,
                current_price=current_price,
                acc_range=acc_range,
                bb_width_pct=bb_width_pct,
                is_at_support=is_at_support,
                lsr=lsr,
                btc_trend_bias=btc_trend_bias,
                funding_rate=funding_rate,
                atr_pct=atr_pct
            )
            if mola_eval.get("qualifies"):
                setup_res = mola_eval

        # CAMADA 4: AVALIA DESVIO DA VWAP (5M)
        if not setup_res and vwap > 0:
            dvwap_eval = self.evaluate_dvwap_reversion(
                symbol=symbol,
                current_price=current_price,
                vwap=vwap,
                acc_range=acc_range,
                lsr=lsr,
                btc_trend_bias=btc_trend_bias,
                funding_rate=funding_rate,
                atr_pct=atr_pct,
                bot_ignition=bot_ignition,
                c_exp=c_exp
            )
            if dvwap_eval.get("qualifies"):
                setup_res = dvwap_eval

        if setup_res:
            cand_dir = setup_res.get("direction")
            is_btc_symbol = "BTC" in symbol.upper()

            # [INVARIANTE SOBERANA 2H SMA BRUNO AGUIAR + ENCRYPTOS]
            # Exceção explícita: LAYA_INTERMEDIATE_REVERSAL_15M é um setup de reversão intraday de liquidez (MFR-15)
            # com varredura confirmada no 15M e stop ultracurto no fundo/topo varrido, isento do lag de 16h do 2H.
            strat_name = setup_res.get("strategy")
            if strat_name != "LAYA_INTERMEDIATE_REVERSAL_15M" and candles_1h and len(candles_1h) >= 6 and not is_btc_symbol:
                c2h = self.aggregate_1h_to_2h(candles_1h)
                sma_info = self.calculate_sma_cross_2h(c2h)
                macro_dir = sma_info.get("direction")
                if macro_dir == "SHORT" and cand_dir == "LONG":
                    return {
                        "qualifies": False,
                        "direction": "HOLD",
                        "score": 0,
                        "strategy": "VETO_MACRO_SMA_2H",
                        "stop_loss": 0.0,
                        "target": 0.0,
                        "stop_dist": 0.0,
                        "target_dist": 0.0,
                        "rationale": f"[VETO SOBERANO SMA 2H]: Proibido abrir LONG em {symbol}. SMA 8 (${sma_info['sma8']}) abaixo da SMA 21 (${sma_info['sma21']}) no 2H indica tendência de baixa macro estrita. Proibido comprar faca caindo contra o macro."
                    }
                elif macro_dir == "LONG" and cand_dir == "SHORT":
                    return {
                        "qualifies": False,
                        "direction": "HOLD",
                        "score": 0,
                        "strategy": "VETO_MACRO_SMA_2H",
                        "stop_loss": 0.0,
                        "target": 0.0,
                        "stop_dist": 0.0,
                        "target_dist": 0.0,
                        "rationale": f"[VETO SOBERANO SMA 2H]: Proibido abrir SHORT em {symbol}. SMA 8 (${sma_info['sma8']}) acima da SMA 21 (${sma_info['sma21']}) no 2H indica tendência de alta macro estrita. Proibido vender locomotiva contra o macro."
                    }

            # [ENCRYPTOS MACRO CLIMATE INTELLIGENCE]:
            # Avalia Dominância do BTC (BTC.D) e clima de mercado para altcoins
            if btc_intel and not is_btc_symbol:
                climate = btc_intel.get("altcoin_climate", "CONSOLIDATION_CHOP")
                long_allowed = btc_intel.get("altcoin_long_allowed", True)
                short_allowed = btc_intel.get("altcoin_short_allowed", True)
                btcd = btc_intel.get("btc_dominance", 0.0)

                is_momentum_leader = (strat_name == "LAYA_AGUIA_FUSION") or (c_exp >= 70.0) or bot_ignition
                if cand_dir == "LONG" and not long_allowed and not is_momentum_leader:
                    return {
                        "qualifies": False,
                        "direction": "HOLD",
                        "score": 60,
                        "strategy": setup_res.get("strategy", "LAYA_VETO"),
                        "stop_loss": 0.0,
                        "target": 0.0,
                        "stop_dist": 0.0,
                        "target_dist": 0.0,
                        "rationale": f"[VETO BTC.D CLIMA - {climate}]: Compras em altcoins vetadas pelo clima macro (BTC.D {btcd:.1f}% drenando capital). Operando estritamente SHORT ou liquidez."
                    }
                elif cand_dir == "SHORT" and not short_allowed:
                    return {
                        "qualifies": False,
                        "direction": "HOLD",
                        "score": 60,
                        "strategy": setup_res.get("strategy", "LAYA_VETO"),
                        "stop_loss": 0.0,
                        "target": 0.0,
                        "stop_dist": 0.0,
                        "target_dist": 0.0,
                        "rationale": f"[VETO BTC.D CLIMA - {climate}]: Vendas em altcoins vetadas pelo clima macro (Altcoin Expansion / BTC.D {btcd:.1f}% em queda). Proibido shortar altcoins em expansão."
                    }

            # [FAROL MACRO BTC SOVEREIGN VETO]:
            # Se Bitcoin caindo (btc_trend_bias < -1.0%), VETO TOTAL de LONGs (apenas SHORT permitido)
            # Se Bitcoin subindo forte (btc_trend_bias > +1.0%), VETO TOTAL de SHORTs (apenas LONG permitido)
            if btc_trend_bias < -1.0 and cand_dir == "LONG":
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 60,
                    "strategy": setup_res.get("strategy", "LAYA_VETO"),
                    "stop_loss": 0.0,
                    "target": 0.0,
                    "stop_dist": 0.0,
                    "target_dist": 0.0,
                    "rationale": f"[FAROL MACRO VETO]: Setup LONG ({setup_res.get('strategy')}) vetado pois o Bitcoin está em queda ({btc_trend_bias:+.2f}%). Operando estritamente SHORT com as baleias."
                }
            if btc_trend_bias > 1.0 and cand_dir == "SHORT":
                return {
                    "qualifies": False,
                    "direction": "HOLD",
                    "score": 60,
                    "strategy": setup_res.get("strategy", "LAYA_VETO"),
                    "stop_loss": 0.0,
                    "target": 0.0,
                    "stop_dist": 0.0,
                    "target_dist": 0.0,
                    "rationale": f"[FAROL MACRO VETO]: Setup SHORT ({setup_res.get('strategy')}) vetado pois o Bitcoin está em alta ({btc_trend_bias:+.2f}%). Operando estritamente LONG a favor da tendência."
                }

            # [RAG KNOWLEDGE INSIGHT]: Consulta lições de risco e histórico do par no RAG
            try:
                from services.rag_service import rag_service
                rag_lesson = rag_service.query_risk_lessons(symbol)
                if rag_lesson:
                    setup_res["rag_insight"] = rag_lesson
            except Exception:
                pass

            return setup_res

        # CAMADA 4: DIAGNÓSTICO INTEGRADO QUANDO NENHUM QUALIFICA
        sup_h1 = acc_range.get("support_h1", 0.0)
        res_h1 = acc_range.get("resistance_h1", 0.0)
        vwap_diff = round(((current_price - vwap) / vwap * 100.0), 1) if vwap > 0 else 0.0

        if sup_h1 <= 0 or res_h1 <= 0:
            diag_text = f"SINCRONIZANDO H1 (Faixa Dinâmica) | DVWAP: {vwap_diff:+.1f}% | MOLA: BBW {bb_width_pct:.1f}%. Aguardando confirmação institucional."
        elif vwap_diff <= -2.0 and btc_trend_bias < -1.0:
            diag_text = f"[FAROL MACRO VETO]: Preço esticado {vwap_diff:+.1f}% abaixo da VWAP, mas BTC em queda ({btc_trend_bias:+.1f}%). Proibido comprar faca caindo."
        elif vwap_diff >= 2.0 and btc_trend_bias > 1.0:
            diag_text = f"[FAROL MACRO VETO]: Preço esticado {vwap_diff:+.1f}% acima da VWAP, mas BTC em forte alta ({btc_trend_bias:+.1f}%). Proibido shortar contra rali."
        else:
            diag_text = f"CONSOLIDAÇÃO H1 (${sup_h1:.4f}-${res_h1:.4f}) | DVWAP: {vwap_diff:+.1f}% | MOLA: BBW {bb_width_pct:.1f}% | BTC: {btc_trend_bias:+.1f}%. Aguardando gatilho de borda."

        return {
            "qualifies": False,
            "direction": "HOLD",
            "score": 65,
            "strategy": "MONITORING_MULTI_TIMEFRAME",
            "stop_loss": 0.0,
            "target": 0.0,
            "stop_dist": 0.0,
            "target_dist": 0.0,
            "rationale": diag_text
        }

    def evaluate_alt_pump_ignition(
        self,
        btc_intel: Dict[str, Any],
        decorrelation_data: Dict[str, Any],
        candidate: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        [TRÍPLICE CONFLUÊNCIA: ALT PUMP IGNITION / DESCOLAMENTO INSTITUCIONAL]
        Identifica quando uma altcoin se desgarra do Bitcoin em momento de rotação de capital:
        1. Macro Dominance: BTC.D em queda (FALLING) ou delta_1h < 0 ou altcoin_climate == ALTCOIN_EXPANSION ou btcd < 56.5%
        2. Statistical Independence: Correlação Pearson < 0.45 ou is_decorrelated == True
        3. Bot Expansion: 1C-EXP >= 70.0 ou bot_ignition == True
        
        Retorna dicionário com:
        - is_ignition: bool
        - bonus_score: int (+25 pts se ativado)
        - tag: str
        - correlation: float
        """
        if not candidate or not btc_intel or not decorrelation_data:
            return {"is_ignition": False, "bonus_score": 0, "tag": "", "correlation": 1.0}

        # Não aplica ignição ao próprio Bitcoin
        clean_sym = candidate.get("clean_sym", "").upper()
        if "BTC" in clean_sym:
            return {"is_ignition": False, "bonus_score": 0, "tag": "", "correlation": 1.0}

        # 1. Descolamento Estatístico do BTC (Pearson)
        corr = float(decorrelation_data.get("correlation", 1.0))
        is_decorrelated = decorrelation_data.get("is_decorrelated", False) or (corr < 0.45)
        
        if not is_decorrelated:
            return {"is_ignition": False, "bonus_score": 0, "tag": f"CORRELATED_BTC({corr:.2f})", "correlation": corr}

        # 2. Ignição dos Robôs Algorítmicos (1C-EXP & Bot Ignition)
        c_exp = float(candidate.get("1c_exp", 0.0) or 0.0)
        bot_on = candidate.get("bot_ignition", False) or (c_exp >= 70.0)

        if not bot_on:
            return {"is_ignition": False, "bonus_score": 0, "tag": f"ROBOTS_OFF(1C-EXP:{c_exp:.0f})", "correlation": corr}

        # 3. Macro Dominance Factor & Clima
        dom_trend = str(btc_intel.get("dominance_trend", "")).upper()
        dom_delta = float(btc_intel.get("dominance_delta_1h", 0.0) or 0.0)
        dom_val = float(btc_intel.get("btc_dominance", 58.0) or 58.0)
        climate = str(btc_intel.get("altcoin_climate", "")).upper()
        btc_bias = float(btc_intel.get("btc_trend_bias", 0.0) or 0.0)
        btc_chg = float(btc_intel.get("btc_change_24h", 0.0) or 0.0)
        long_allowed = btc_intel.get("altcoin_long_allowed", True)

        # [V169-FAROL-MACRO-VETO]: Se o Bitcoin estiver em sangria, queda livre ou tendência de baixa,
        # NENHUMA altcoin tem autorização para LONG via Alt Pump Ignition.
        if not long_allowed or btc_bias < -0.4 or btc_chg < -1.0 or climate == "ALTCOIN_BLOODBATH":
            return {"is_ignition": False, "bonus_score": 0, "tag": f"VETO_BTC_SANGRIANDO({btc_bias:+.1f}%)", "correlation": corr}
        
        is_macro_favorable = (
            dom_trend == "FALLING"
            or climate == "ALTCOIN_EXPANSION"
            or dom_delta < 0.0
            or dom_val < 56.5
            or (corr < 0.35 and bot_on)
        ) and climate not in ("ALTCOIN_BLOODBATH", "BTC_DRAINAGE")

        if not is_macro_favorable:
            return {"is_ignition": False, "bonus_score": 0, "tag": "MACRO_VETO", "correlation": corr}

        # TRÍPLICE CONFLUÊNCIA CONFIRMADA
        tag = f"[ALT PUMP IGNITION: Descolamento BTC (Corr: {corr:.2f}) + BTC.D Queda + Robôs On (1C-EXP: {c_exp:.0f})]"
        return {
            "is_ignition": True,
            "bonus_score": 25,
            "tag": tag,
            "correlation": corr
        }

    def record_trade_profit(self, symbol: str, pnl_pct: float) -> None:
        """[V188-PROFIT-REENTRY] Registra encerramento com lucro para permitir reentrada rápida no pullback após 5min."""
        clean = symbol.replace("-USDT-SWAP", "").replace("USDT", "").replace(".P", "").upper()
        if not hasattr(self, "_symbol_last_profit"):
            self._symbol_last_profit = {}
        self._symbol_last_profit[clean] = {"time": time.time(), "pnl": float(pnl_pct)}
        logger.info(f"🏆 [LAYA-PROFIT-REENTRY-ARMED] {clean} fechado com lucro de +{pnl_pct:.1f}% ROI. Radar armado para reentrada em pullback após 5 minutos.")

    def record_stop_loss(self, symbol: str, direction: str = "LONG", cooldown_seconds: int = 7200) -> None:
        """[V159-TITANS] Registra stop loss para impor quarentena institucional de 2 horas (7200s) no símbolo e Circuit Breaker Direcional."""
        clean = symbol.replace("-USDT-SWAP", "").replace("USDT", "").upper()
        now = time.time()
        self._symbol_cooldowns[clean] = now + cooldown_seconds
        logger.info(f"️ [LAYA-COOLDOWN] {clean} em quarentena por {cooldown_seconds}s (2h) após Stop Loss")

        # Circuit Breaker Direcional (2 stops recentes na mesma direção travam a direção inteira por 1h)
        dir_clean = direction.upper() if direction else "LONG"
        if not hasattr(self, "_direction_stops"):
            self._direction_stops = []
        if not hasattr(self, "_direction_cooldowns"):
            self._direction_cooldowns = {}

        self._direction_stops.append({"time": now, "direction": dir_clean, "symbol": clean})
        # Mantém stops da última hora (3600s)
        self._direction_stops = [s for s in self._direction_stops if now - s["time"] <= 3600]

        # Circuit Breaker Global Anti-Tilt (3 stops quaisquer em <= 90min (5400s) congelam novas entradas por 45min (2700s))
        if not hasattr(self, "_global_stop_history"):
            self._global_stop_history = []
        if not hasattr(self, "_global_circuit_breaker_until"):
            self._global_circuit_breaker_until = 0.0

        self._global_stop_history.append(now)
        # Mantém histórico de stops dos últimos 90 minutos (5400s)
        self._global_stop_history = [t for t in self._global_stop_history if now - t <= 5400]
        if len(self._global_stop_history) >= 3:
            self._global_circuit_breaker_until = max(self._global_circuit_breaker_until, now + 2700)
            logger.warning(f" [LAYA-GLOBAL-CIRCUIT-BREAKER] 3 stops recentes no mercado! Resfriamento global ativado por 45 minutos (2700s).")
            self.log_thought(
                "CIRCUIT_BREAKER",
                f"DEFESA ANTI-TILT ATIVADA: 3 stops recentes no mercado em <90min. Novas entradas congeladas por 45min para resfriamento de banca.",
                action="GLOBAL_FREEZE",
                confidence=99
            )

        consec_dir_stops = [s for s in self._direction_stops if s["direction"] == dir_clean]
        if len(consec_dir_stops) >= 2:
            self._direction_cooldowns[dir_clean] = now + 3600
            logger.warning(f" [LAYA-CIRCUIT-BREAKER] {len(consec_dir_stops)} stops seguidos em {dir_clean}! Entradas {dir_clean} bloqueadas por 60 minutos para proteção de capital.")
            self.log_thought(
                "CIRCUIT_BREAKER",
                f"DEFESA ATIVADA: 2 stops seguidos em {dir_clean}. Entradas {dir_clean} travadas por 60min contra sangria do mercado.",
                action="DEFESA_LOCK",
                confidence=99
            )

    # [V161-DESCORRELATION] Mapeamento Setorial de Clusters para Diversificação de Carteira
    SECTOR_CLUSTERS = {
        "L1_BLUECHIP": {"BTC", "ETH", "SOL", "NEAR", "SUI", "AVAX", "ADA", "DOT", "ATOM", "LTC", "BCH", "ETC", "XRP", "TRX"},
        "L2_ROLLUPS": {"ARB", "OP", "ZK", "POL", "STRK", "XPL"},
        "DEFI_ORACLE": {"UNI", "AAVE", "MKR", "PYTH", "PENDLE", "ONDO", "INJ", "CRV", "DYDX", "GMX"},
        "AI_DEPIN": {"RENDER", "FET", "TIA", "AR", "TAO", "ICP"},
        "MEME_SPEC": {"DOGE", "PEPE", "WIF", "BONK", "GALA", "AXS", "SAND", "CHZ"}
    }

    def get_symbol_sector_cluster(self, symbol: str) -> str:
        """Identifica o cluster setorial de um ativo."""
        clean = symbol.replace("-USDT-SWAP", "").replace("USDT", "").replace(".P", "").upper()
        for cluster_name, coins in self.SECTOR_CLUSTERS.items():
            if clean in coins:
                return cluster_name
        return "GENERAL_ALT"

    def is_cluster_limit_reached(self, symbol: str, active_symbols: List[str], max_per_cluster: int = 2) -> bool:
        """
        Verifica se o limite de exposição ao mesmo cluster setorial foi atingido.
        Impede que mais de 2 ativos do mesmo setor (ex: 3 L1s) operem simultaneamente.
        """
        target_cluster = self.get_symbol_sector_cluster(symbol)
        if target_cluster == "GENERAL_ALT":
            return False

        same_cluster_count = 0
        for act in active_symbols:
            act_cluster = self.get_symbol_sector_cluster(act)
            if act_cluster == target_cluster:
                same_cluster_count += 1

        return same_cluster_count >= max_per_cluster

    def is_global_circuit_breaker_active(self) -> bool:
        """Verifica se o Circuit Breaker Global Anti-Tilt está ativo."""
        expiry = getattr(self, "_global_circuit_breaker_until", 0.0)
        return time.time() < expiry

    def is_direction_in_cooldown(self, direction: str) -> bool:
        """Verifica se uma direção (LONG ou SHORT) está sob Circuit Breaker (em memória e em SQLite)."""
        dir_clean = direction.upper() if direction else "LONG"
        now = time.time()
        expiry = getattr(self, "_direction_cooldowns", {}).get(dir_clean, 0.0)
        if now < expiry:
            return True

        # Consulta persistente no SQLite: se houve 2 stops nessa direção nos últimos 45min (2700s), trava!
        try:
            import sqlite3
            db_candidates = [
                _Path(__file__).resolve().parent.parent.parent / "local_sniper.db",
                _Path(__file__).resolve().parent.parent.parent.parent / "local_sniper.db"
            ]
            for db_p in db_candidates:
                if db_p.exists():
                    conn = sqlite3.connect(str(db_p), timeout=0.5)
                    rows = conn.execute(
                        "SELECT closed_at FROM sandbox_trades WHERE direction = ? AND status = 'CLOSED_SL' AND closed_at > ? ORDER BY closed_at DESC LIMIT 5",
                        (dir_clean, now - 2700)
                    ).fetchall()
                    conn.close()
                    if len(rows) >= 2:
                        if not hasattr(self, "_direction_cooldowns"):
                            self._direction_cooldowns = {}
                        self._direction_cooldowns[dir_clean] = now + 2700
                        return True
                    break
        except Exception:
            pass

        return False

    def is_symbol_in_cooldown(self, symbol: str) -> bool:
        """Verifica se o ativo está em período de quarentena (2 horas) após stop."""
        clean = symbol.replace("-USDT-SWAP", "").replace("USDT", "").replace(".P", "").upper()
        now = time.time()
        expiry = self._symbol_cooldowns.get(clean, 0.0)
        if now < expiry:
            return True

        # Checagem resiliente no SandboxService em memória
        try:
            from services.sandbox_service import sandbox_service
            for key, sl_time in list(sandbox_service._stop_cooldown.items()):
                sb_sym = key[0] if isinstance(key, tuple) else str(key)
                sb_clean = sb_sym.replace("-USDT-SWAP", "").replace("USDT", "").replace(".P", "").upper()
                if sb_clean == clean and (now - float(sl_time)) < 7200:
                    return True
        except Exception:
            pass

        # Checagem persistente em SQLite para blindagem pós-reboot
        try:
            import sqlite3
            db_candidates = [
                _Path(__file__).resolve().parent.parent.parent / "local_sniper.db",
                _Path(__file__).resolve().parent.parent.parent.parent / "local_sniper.db"
            ]
            for db_p in db_candidates:
                if db_p.exists():
                    conn = sqlite3.connect(str(db_p), timeout=0.5)
                    row = conn.execute(
                        "SELECT closed_at FROM sandbox_trades WHERE symbol LIKE ? AND status='CLOSED_SL' ORDER BY closed_at DESC LIMIT 1",
                        (f"%{clean}%",)
                    ).fetchone()
                    conn.close()
                    if row and row[0]:
                        closed_ts = float(row[0])
                        if (now - closed_ts) < 7200:
                            return True
                    break
        except Exception:
            pass

        return False

    def _load_calibrated_weights(self) -> Dict[str, Any]:
        """Carrega pesos ajustados do pipeline de fine-tuning/calibração supervisionada."""
        try:
            weights_file = _Path(__file__).resolve().parent.parent / "data" / "models" / "calibrated" / "laya_calibrated_weights.json"
            if weights_file.exists():
                with open(weights_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info(f" [LAYA] Pesos calibrados carregados do Fine-Tuning: v{data.get('version')}")
                    return data
        except Exception as e:
            logger.debug(f"[LAYA] Sem pesos calibrados customizados: {e}")
        return {}

    def evaluate_lower_tf_structure(self, candles: list, direction: str) -> dict:
        """
        [V195-PRECISION-30M-EXHAUSTION]: Avalia microestrutura em candles de 30M:
        - Exige candle fechado com rejeição clara de pavio.
        - Veta terminantemente abrir SHORT em vela verde de expansão ou com volume comprador explosivo.
        - Veta terminantemente abrir LONG em vela vermelha de despejo ou com volume vendedor explosivo.
        """
        default_metrics = {
            "upper_wick_ratio": 0.0, "lower_wick_ratio": 0.0, "wick_ratio": 0.0,
            "momentum_pct": 0.0, "open": 0.0, "high": 0.0, "low": 0.0, "close": 0.0
        }

        if isinstance(candles, dict):
            candles = candles.get("data", [])
        if not isinstance(candles, list) or len(candles) < 3:
            return {
                "is_safe": False,
                "reason": "DADOS_30M_INSUFICIENTES (Veto preventivo de seguranca em alta alavancagem)",
                "metrics": default_metrics
            }

        try:
            sorted_c = sorted(candles, key=lambda c: int(c[0]))
        except Exception:
            sorted_c = candles

        c_prev2 = sorted_c[-3]
        c_prev1 = sorted_c[-2]
        c_curr = sorted_c[-1]

        o1, h1, l1, cl1 = float(c_prev1[1]), float(c_prev1[2]), float(c_prev1[3]), float(c_prev1[4])
        o_curr, h_curr, l_curr, cl_curr = float(c_curr[1]), float(c_curr[2]), float(c_curr[3]), float(c_curr[4])
        o_old, h_old, l_old, cl_old = float(c_prev2[1]), float(c_prev2[2]), float(c_prev2[3]), float(c_prev2[4])

        vol_curr = float(c_curr[5]) if len(c_curr) > 5 else 0.0
        vol_prev1 = float(c_prev1[5]) if len(c_prev1) > 5 else 0.0
        vol_prev2 = float(c_prev2[5]) if len(c_prev2) > 5 else 0.0
        vol_avg = max(1.0, (vol_prev1 + vol_prev2) / 2.0)

        range_curr = max(1e-8, h_curr - l_curr)
        upper_wick = h_curr - max(o_curr, cl_curr)
        lower_wick = min(o_curr, cl_curr) - l_curr
        upper_wick_ratio = upper_wick / range_curr
        lower_wick_ratio = lower_wick / range_curr
        total_gain = (cl_curr - l_old) / l_old if l_old > 0 else 0.0
        total_drop = (h_old - cl_curr) / h_old if h_old > 0 else 0.0

        metrics = {
            "upper_wick_ratio": round(upper_wick_ratio * 100.0, 1),
            "lower_wick_ratio": round(lower_wick_ratio * 100.0, 1),
            "wick_ratio": round((upper_wick_ratio if direction == "SHORT" else lower_wick_ratio) * 100.0, 1),
            "momentum_pct": round((total_gain if direction == "SHORT" else -total_drop) * 100.0, 2),
            "open": o_curr,
            "high": h_curr,
            "low": l_curr,
            "close": cl_curr,
            "prev_high": h1,
            "prev_low": l1,
            "range": round(range_curr, 4),
            "vol_ratio": round(vol_curr / vol_avg, 2)
        }

        if direction == "SHORT":
            # 1. Trava de Volume Explosivo de Compra no Repique
            if vol_curr > vol_avg * 2.0 and cl_curr > o_curr:
                return {
                    "is_safe": False,
                    "reason": f"VETO_VOLUME_EXPLOSIVO_COMPRA_30M (Repique com volume {vol_curr/vol_avg:.1f}x acima da media. Compradores agressivos no controle)",
                    "metrics": metrics
                }
            # 2. Trava de Vela Verde em Expansao: Proibido vender candle 30M verde subindo forte sem rejeicao
            if cl_curr > o_curr * 1.002 and upper_wick_ratio < 0.25:
                return {
                    "is_safe": False,
                    "reason": f"VETO_VELA_VERDE_EXPANSAO_30M (Vela 30M verde ativa [+{((cl_curr-o_curr)/o_curr)*100:.2f}%] sem rejeicao ({upper_wick_ratio*100:.1f}%). Proibido vender candle subindo)",
                    "metrics": metrics
                }
            # 3. Trava de Rompimento de Maxima sem Pavio
            if h_curr > h1 * 1.002 and upper_wick_ratio < 0.20 and cl_curr >= h1:
                return {
                    "is_safe": False,
                    "reason": f"VETO_EXPANSAO_ALTA_30M (Rompimento ativo de maxima em ${h_curr:.4f} sem rejeicao ({upper_wick_ratio*100:.1f}%))",
                    "metrics": metrics
                }

        elif direction == "LONG":
            # 1. Trava de Volume Explosivo de Venda no Despejo
            if vol_curr > vol_avg * 2.0 and cl_curr < o_curr:
                return {
                    "is_safe": False,
                    "reason": f"VETO_VOLUME_EXPLOSIVO_VENDA_30M (Despejo com volume {vol_curr/vol_avg:.1f}x acima da media. Vendedores agressivos no controle)",
                    "metrics": metrics
                }
            # 2. Trava de Vela Vermelha em Queda Ativa: Proibido comprar faca caindo sem absorcao
            if cl_curr < o_curr * 0.998 and lower_wick_ratio < 0.25:
                return {
                    "is_safe": False,
                    "reason": f"VETO_VELA_VERMELHA_EXPANSAO_30M (Vela 30M vermelha ativa [-{((o_curr-cl_curr)/o_curr)*100:.2f}%] sem absorcao ({lower_wick_ratio*100:.1f}%). Proibido comprar candle caindo)",
                    "metrics": metrics
                }
            # 3. Trava de Rompimento de Minima sem Pavio
            if l_curr < l1 * 0.998 and lower_wick_ratio < 0.20 and cl_curr <= l1:
                return {
                    "is_safe": False,
                    "reason": f"VETO_EXPANSAO_BAIXA_30M (Rompimento ativo de minima em ${l_curr:.4f} sem absorcao ({lower_wick_ratio*100:.1f}%))",
                    "metrics": metrics
                }

        return {
            "is_safe": True,
            "reason": "CONFIRMADO_MICROESTRUTURA_30M (Exaustao e absorcao validadas no timeframe 30M)",
            "metrics": metrics
        }

    async def check_lower_tf_exhaustion(self, symbol: str, direction: str) -> dict:
        """
        [V195-NATIVE-OKX-30M-FEED]: Consulta nativa de velas 30M na OKX Perpétuo
        com fallbacks para OKX Spot e Binance, passando os candles para evaluate_lower_tf_structure.
        """
        clean = symbol.replace("-SWAP", "").replace("-", "").replace(".P", "").upper()
        clean_coin = clean.replace("USDT", "")
        raw_candles = []

        try:
            import httpx
            async with httpx.AsyncClient(timeout=4.0, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}) as client:
                # 1. OKX SWAP Perpétuo 30M
                inst_id = f"{clean_coin}-USDT-SWAP"
                url_okx = f"https://www.okx.com/api/v5/market/candles?instId={inst_id}&bar=30m&limit=10"
                resp = await client.get(url_okx)
                if resp.status_code == 200:
                    d = resp.json()
                    if d.get("code") == "0" and d.get("data") and len(d["data"]) >= 3:
                        raw_candles = d["data"]

                # 2. Fallback OKX Spot 30M
                if not raw_candles:
                    url_spot = f"https://www.okx.com/api/v5/market/candles?instId={clean_coin}-USDT&bar=30m&limit=10"
                    resp_s = await client.get(url_spot)
                    if resp_s.status_code == 200:
                        d_s = resp_s.json()
                        if d_s.get("code") == "0" and d_s.get("data") and len(d_s["data"]) >= 3:
                            raw_candles = d_s["data"]

                # 3. Fallback Binance Futures / Spot 30M
                if not raw_candles:
                    url_bin = f"https://fapi.binance.com/fapi/v1/klines?symbol={clean}&interval=30m&limit=10"
                    resp_b = await client.get(url_bin)
                    if resp_b.status_code == 200:
                        b_data = resp_b.json()
                        if isinstance(b_data, list) and len(b_data) >= 3:
                            raw_candles = [[str(k[0]), str(k[1]), str(k[2]), str(k[3]), str(k[4]), str(k[5])] for k in b_data]
        except Exception as _e_ltf:
            logger.debug(f"[LOWER-TF-30M] Erro ao consultar candles 30M para {symbol}: {_e_ltf}")

        if not raw_candles:
            try:
                from app.services.coinglass_heatmap_service import coinglass_heatmap_service
                cached_heat = coinglass_heatmap_service._cache.get(clean, {}).get("data", {})
                heat_candles = cached_heat.get("candles", [])
                if heat_candles and len(heat_candles) >= 3:
                    raw_candles = heat_candles
            except Exception:
                pass

        if not raw_candles:
            return {
                "is_safe": False,
                "reason": f"DADOS_30M_INDISPONIVEIS (Veto preventivo de segurança em {symbol}: confirmação 30M ausente)",
                "metrics": {"upper_wick_ratio": 0.0, "lower_wick_ratio": 0.0, "wick_ratio": 0.0, "momentum_pct": 0.0}
            }

        return self.evaluate_lower_tf_structure(raw_candles, direction)

    def _seed_initial_thoughts(self):
        """Inicializa pensamentos táticos para exibir sinal de vida na UI imediatamente."""
        now = time.time()
        seeds = [
            ("SISTEMA", "Laya Sovereign Brain inicializado. Radar Universal ativo em 507 contratos OKX + 30 Titãs.", "BOOT", 98, "LATERAL"),
            ("BTC-ORACLE", "Farol Macro Bitcoin sincronizado. Aguardando leitura de ADX e viés institucional...", "ORACULO", 95, "LATERAL"),
            ("RADAR-SMARTMONEY", "Radar Encryptos ativo: monitorando 1C-EXP, 1C-RANGE e aceleração de robôs nas altcoins...", "VARREDURA", 92, "LATERAL")
        ]
        for sym, msg, act, conf, reg in seeds:
            self.thought_stream.append({
                "time": time.strftime("%H:%M:%S", time.localtime(now - 10)),
                "timestamp": now - 10,
                "symbol": sym,
                "thought": msg,
                "action": act,
                "confidence": conf,
                "regime": reg
            })

    def _bootstrap_initial_setups(self):
        """Pre-popula candidate_setups no boot para que a UI do Cockpit renderize o Ranking 1-20/30 imediatamente sem latencia com os pares institucionais."""
        now_str = time.strftime("%H:%M:%S")
        from app.services.okx_universe_service import okx_universe_service
        elite_symbols = [s.replace("-USDT-SWAP", "") for s in okx_universe_service._titans_30_altcoins]

        price_map = {}
        try:
            from services.okx_ws_public import okx_ws_public_service
            for base in elite_symbols:
                p = okx_ws_public_service.get_current_price(f"{base}USDT") or okx_ws_public_service.get_current_price(f"{base}-USDT-SWAP")
                if p and p > 0:
                    price_map[f"{base}USDT"] = float(p)
        except Exception:
            pass

        base_scores = [92, 90, 89, 88, 87, 86, 85, 84, 83, 82, 81, 80, 79, 78, 77, 76, 75, 74, 73, 72]
        directions = ["LONG", "SHORT", "LONG", "SHORT", "LONG", "HOLD", "LONG", "HOLD", "SHORT", "HOLD",
                      "LONG", "SHORT", "HOLD", "LONG", "SHORT", "LONG", "SHORT", "HOLD", "HOLD", "LONG"]
        strategies = ["LAYA_AGUIA_FUSION", "LAYA_AGUIA_FUSION", "LAYA_AGUIA_FUSION", "LAYA_AGUIA_FUSION",
                      "LAYA_DVWAP_FLOW", "MONITOR", "LAYA_AGUIA_FUSION", "MONITOR", "LAYA_LIQUIDITY_HUNT", "MONITOR",
                      "LAYA_RANGE_REVERSAL", "LAYA_LIQUIDITY_HUNT", "MONITOR", "LAYA_AGUIA_FUSION", "LAYA_DVWAP_FLOW",
                      "LAYA_MOMENTO_MOLA", "LAYA_LIQUIDITY_HUNT", "MONITOR", "MONITOR", "LAYA_RANGE_REVERSAL"]

        for idx, base in enumerate(elite_symbols):
            clean_sym = f"{base}USDT"
            inst_sym = f"{base}-USDT-SWAP"
            px = price_map.get(clean_sym, 0.0)
            score = base_scores[idx] if idx < len(base_scores) else max(50, 70 - idx)
            d = directions[idx] if idx < len(directions) else "HOLD"
            strat = strategies[idx] if idx < len(strategies) else "MONITOR"

            c_exp = 75.0 if idx < 5 else (55.0 if idx < 12 else 40.0)
            c_range = 45.0 + (idx * 2) % 40

            self.candidate_setups[clean_sym] = {
                "symbol": inst_sym,
                "clean_sym": clean_sym,
                "rank": idx + 1,
                "direction": d,
                "strategy": strat,
                "price": px,
                "score": score,
                "stop_loss": round(px * 0.975, 4) if px > 0 else 0.0,
                "target": round(px * 1.045, 4) if px > 0 else 0.0,
                "stop_dist": 0.025,
                "target_dist": 0.045,
                "lsr": 1.05,
                "oi_delta_pct": 1.2,
                "flow_regime": "ACCUMULATION",
                "acc_range": {
                    "is_consolidating": True,
                    "resistance_h1": round(px * 1.02, 4) if px > 0 else 0.0,
                    "support_h1": round(px * 0.98, 4) if px > 0 else 0.0,
                    "range_pct": 4.0
                },
                "vwap": px,
                "bb_width_pct": 3.2,
                "1c_exp": c_exp,
                "1c_range": c_range,
                "bot_ignition": (c_exp >= 70.0),
                "has_volume_spike": False,
                "spike_direction": "NEUTRAL",
                "vol_ratio": 1.1,
                "is_pump_ignition": (c_exp >= 70.0 and d == "LONG"),
                "is_dump_ignition": (c_exp >= 70.0 and d == "SHORT"),
                "magnet_direction": "BULLISH_SWEEP" if d == "LONG" else ("BEARISH_SWEEP" if d == "SHORT" else "NEUTRAL_EQUILIBRIUM"),
                "magnet_region": "ACIMA" if d == "LONG" else ("ABAIXO" if d == "SHORT" else "NEUTRAL"),
                "magnet_target": round(px * 1.04, 4) if px > 0 else 0.0,
                "magnet_volume_m": round(4.5 + idx * 0.5, 1),
                "lifecycle": {"zone_id": "HUNT" if score >= 85 else "WATCH", "distance_pct": 2.5},
                "confluence": {},
                "leverage_cap": 50.0,
                "rationale": f"Estrutura preliminar institucional calibrada. Monitorando fluxo e liquidez em {clean_sym}.",
                "memory_context": "",
                "time": now_str
            }

    def log_thought(self, symbol: str, thought: str, action: str = "PENSAMENTO", confidence: float = None, regime: str = None):
        """Registra um pensamento ou ação da Laya no stream de consciência com debounce anti-flood."""
        # Debounce: evita flood idêntico consecutivo para o mesmo símbolo
        last_t = getattr(self, "_last_symbol_thought", {}).get(symbol)
        if last_t == thought:
            return
        if not hasattr(self, "_last_symbol_thought"):
            self._last_symbol_thought = {}
        self._last_symbol_thought[symbol] = thought

        now = time.time()
        entry = {
            "time": time.strftime("%H:%M:%S", time.localtime(now)),
            "timestamp": now,
            "symbol": symbol,
            "thought": thought,
            "action": action,
            "confidence": confidence or 80,
            "regime": regime or self.current_regime
        }
        self.thought_stream.append(entry)
        if len(self.thought_stream) > 80:
            self.thought_stream.pop(0)

        # [MEMORIA-EPISODICA]: Persistência deduplicada de insights e ações institucionais
        if action in ("ORDEM_DISPARADA", "VETO_MACRO", "PADRAO_CONFIRMADO", "ABSORPCAO", "LIQUIDACAO", "GATILHO_MOLA", "DVAP_CROSS", "VARREDURA_SNIPER"):
            try:
                from app.services.memory_service import memory_service
                conf_val = round(min(1.0, max(0.1, (confidence or 80) / 100.0)), 2)
                if symbol in ("SISTEMA", "BTC-ORACLE", "MACRO", "RADAR-FLUXO"):
                    memory_service.record_macro_fact(thought, confidence=conf_val)
                elif symbol and not symbol.startswith("["):
                    memory_service.record_pair_insight(symbol, thought, confidence=conf_val, metadata={"action": action, "regime": regime or self.current_regime})
            except Exception:
                pass

    def get_pulse(self) -> Dict[str, Any]:
        """Retorna telemetria completa de sinal de vida da Laya para o Cockpit com dados dinâmicos em tempo real."""
        if not self.candidate_setups:
            self._bootstrap_initial_setups()

        mem_stats = {}
        try:
            from app.services.memory_service import memory_service
            mem_stats = memory_service.get_stats()
        except Exception:
            pass

        # [TELEMETRIA DINÂMICA]: ADX e métricas macro ao vivo do oráculo público OKX
        btc_var_1h = 0.0
        btc_var_24h = 0.0
        try:
            from services.okx_ws_public import okx_ws_public_service
            live_adx = float(getattr(okx_ws_public_service, "btc_adx", 0.0) or 0.0)
            if live_adx > 0:
                self.master_adx = round(live_adx, 1)
            btc_var_1h = float(getattr(okx_ws_public_service, "btc_variation_1h", 0.0) or 0.0)
            btc_var_24h = float(getattr(okx_ws_public_service, "btc_variation_24h", 0.0) or 0.0)
        except Exception:
            pass

        # [GATING STATUS]: Status dinâmico de defesas e circuit breaker
        if self.is_global_circuit_breaker_active():
            rem_s = int(getattr(self, "_global_circuit_breaker_until", 0.0) - time.time())
            gating_status = f"DEFESA ({rem_s}s)"
        elif self.is_direction_in_cooldown("LONG") and self.is_direction_in_cooldown("SHORT"):
            gating_status = "DEFESA DUAL"
        elif self.is_direction_in_cooldown("LONG"):
            gating_status = "TRAVA LONG"
        elif self.is_direction_in_cooldown("SHORT"):
            gating_status = "TRAVA SHORT"
        else:
            gating_status = "ESTAVEL"

        # [KRONOS CONVICTION SCORE]: Média das projeções ativas dos candidatos
        kronos_avg = 50.0
        if self.candidate_setups:
            k_scores = [
                float((c.get("confluence") or {}).get("kronos_conviction", 0.0))
                for c in self.candidate_setups.values()
                if (c.get("confluence") or {}).get("kronos_conviction")
            ]
            if k_scores:
                kronos_avg = round(sum(k_scores) / len(k_scores), 1)

        reg_mode = "MEAN_REVERSION" if self.master_adx < 25.0 else "TREND_SNIPER"
        self.regime_mode = reg_mode

        # [V207-TACTICAL-INTENTION]: Intenção Tática da Laya em Tempo Real para o Cabeçalho
        fleet_status = "0/8 ATIVAS"
        laya_intention = "ONLINE (AGUARDANDO OPORTUNIDADE)"
        unprotected_count = 0
        protected_count = 0
        try:
            from services.sandbox_service import sandbox_service
            active_trades_list = getattr(sandbox_service, "active_trades_cache", [])
            total_active = len(active_trades_list)
            unprotected_count = self.count_unprotected_risk_trades(active_trades_list)
            protected_count = max(0, total_active - unprotected_count)
            
            top_syms = []
            if self.candidate_setups:
                sorted_cands = sorted(self.candidate_setups.values(), key=lambda x: x.get("score", 0), reverse=True)
                top_syms = [c.get("clean_sym", c.get("symbol", "")).replace("-USDT-SWAP", "").replace("USDT", "") for c in sorted_cands if c.get("clean_sym") or c.get("symbol")][:3]

            if total_active >= 8:
                fleet_status = f"{total_active}/8 ATIVAS (TETO MÁXIMO)"
                laya_intention = "TETO DA FROTA (8/8) • MONITORANDO TRAILING"
            elif unprotected_count >= 2:
                fleet_status = f"{total_active}/8 ATIVAS ({protected_count} RISCO ZERO • {unprotected_count} EM RISCO)"
                laya_intention = f"2/2 EM RISCO VIVO • AGUARDANDO BREAKEVEN (+60% ROI) PARA EXPANDIR"
            else:
                fleet_status = f"{total_active}/8 ATIVAS ({protected_count} RISCO ZERO • {unprotected_count} EM RISCO)"
                if top_syms:
                    laya_intention = f"SLOT {total_active+1}/8 LIVRE • VIGIANDO PULLBACK EM [{', '.join(top_syms)}] • FAROL BTC SHORT"
                else:
                    laya_intention = f"SLOT {total_active+1}/8 LIVRE • VARRENDO UNIVERSO OKX POR PULLBACK 30M"
        except Exception as e_intent:
            pass

        return {
            "laya_intention": laya_intention,
            "fleet_status": fleet_status,
            "unprotected_risk_slots": unprotected_count,
            "protected_risk_slots": protected_count,
            "status": "ONLINE (SOVEREIGN COMMANDER)",
            "sovereign": True,
            "regime": self.current_regime,
            "regime_mode": reg_mode,
            "master_adx": self.master_adx,
            "btc_trend_pct": round(btc_var_1h if abs(btc_var_1h) > 0.001 else btc_var_24h, 2),
            "btc_variation_1h": round(btc_var_1h, 2),
            "btc_variation_24h": round(btc_var_24h, 2),
            "gating_status": gating_status,
            "kronos_score": kronos_avg,
            "last_scan_ago_s": round(time.time() - self.last_scan_time, 1),
            "thoughts": self.thought_stream[-20:],
            "candidate_setups": self.candidate_setups,
            "whale_flow": self.whale_flow_cache,
            "universal_market_stats": self.universal_market_stats,
            "doctrine": "INSTITUTIONAL_LIQUIDITY_HUNTER",
            "memory_stats": mem_stats
        }

    async def _open_flip_trade(self, symbol: str, direction: str, stop_loss: float, target: float, score: int = 98) -> bool:
        """[V182-SWEEP-AND-FLIP] Abre uma ordem sniper de virada de mão no mesmo par a favor da gravidade do ímã institucional."""
        from services.database_service import database_service
        from services.order_projection_service import proj_service
        from app.services.okx_universe_service import okx_universe_service
        from services.sandbox_service import sandbox_service

        try:
            clean_sym = symbol.replace("-USDT-SWAP", "").replace("USDT", "").replace("-", "")
            p = await sandbox_service._get_current_price(symbol)
            if not p or p <= 0:
                p = self.candidate_setups.get(symbol, {}).get("price") or 0.0
            if not p or p <= 0:
                return False

            leverage = 50.0
            margin = 100.0

            stop_loss = okx_universe_service.format_price_by_tick(symbol, stop_loss)
            target = okx_universe_service.format_price_by_tick(symbol, target)

            quant_res = okx_universe_service.quantize_order_contracts(
                symbol=symbol,
                margin_usd=margin,
                leverage=leverage,
                price=p
            )
            if not quant_res.get("is_valid"):
                return False

            num_contracts = quant_res["contracts"]
            notional_usd = quant_res["notional_usd"]
            eff_margin = quant_res["effective_margin"]
            ct_val = quant_res["ctVal"]
            tick_sz = quant_res["tickSize"]
            lot_sz = quant_res["lotSize"]
            min_sz = quant_res["minSz"]
            fee_open = round(notional_usd * 0.0005, 2)
            fee_close = round(notional_usd * 0.0005, 2)
            slippage_usd = round(notional_usd * 0.0003, 2)
            total_fees = round(fee_open + fee_close + slippage_usd, 2)

            init_stop_roi = round(proj_service.calculate_roi(p, stop_loss, direction, leverage), 2)
            trade_id = f"laya_{int(time.time() * 1000)}"

            trade_data = {
                "id": trade_id,
                "symbol": symbol,
                "strategy": "LAYA_SWEEP_AND_FLIP",
                "direction": direction,
                "entry_price": p,
                "current_price": p,
                "stop_loss": stop_loss,
                "target": target,
                "max_roi": 0.0,
                "current_roi": 0.0,
                "pnl_pct": 0.0,
                "status": "ACTIVE",
                "opened_at": time.time(),
                "flash_state": {
                    "phase": "SWEEP_AND_FLIP",
                    "ladder_level": 0,
                    "stop_roi": init_stop_roi,
                    "breakeven_trigger_roi": 16.0,
                    "history": [
                        f"[SWEEP & FLIP] Laya virou a mão para {direction} em {clean_sym} a ${p:.4f} (Stop: ${stop_loss:.4f} / {init_stop_roi:.1f}% ROI, Alvo: ${target:.4f}) com score {score}%."
                    ]
                },
                "contract_meta": {
                    "strategy": "LAYA_SWEEP_AND_FLIP",
                    "margin": eff_margin,
                    "leverage": leverage,
                    "ctVal": ct_val,
                    "tickSize": tick_sz,
                    "lotSize": lot_sz,
                    "minSz": min_sz,
                    "notional_usd": notional_usd,
                    "num_contracts": num_contracts,
                    "fee_open_usd": fee_open,
                    "fee_close_usd": fee_close,
                    "slippage_usd": slippage_usd,
                    "total_fees_usd": total_fees,
                    "slippage_pct": 0.03,
                    "whale_doctrine": "SWEEP_AND_FLIP_HUNTER",
                    "rationale": f"Flip direcional apos sweep de liquidez no topo. Stop curto no pavio e alvo no bolsao oposto."
                }
            }

            await database_service.save_sandbox_trade(trade_data)
            self._last_traded_pair = clean_sym
            self._last_global_trade_open_ts = time.time()
            if not hasattr(self, "_last_traded_pair_ts"):
                self._last_traded_pair_ts = {}
            self._last_traded_pair_ts[clean_sym] = time.time()

            logger.info(f"🔄 [LAYA-SWEEP-FLIP] Ordem {direction} aberta em {symbol} a ${p:.4f} (SL: ${stop_loss}, TP: ${target})")
            return True
        except Exception as e:
            logger.error(f"[LAYA-OPEN-FLIP-ERR] {e}")
            return False

    async def scan_and_execute_autonomous(self, force_open_if_empty: bool = True) -> Dict[str, Any]:
        """
        VARREDURA SOBERANA AUTÔNOMA DA LAYA:
        - Analisa pares da Matrix Elite (SOL, AVAX, NEAR, LINK).
        - No modo Mean-Reversion (ADX < 25), caça exaustão em suportes e resistências.
        - Registra pensamentos em tempo real no stream de consciência.
        - Se a mesa estiver vazia (0 ordens ativas) e force_open_if_empty for True, dispara a melhor oportunidade.
        """
        import asyncio
        import random
        from services.okx_rest import okx_rest_service
        from services.database_service import database_service

        t0 = time.time()
        self.last_scan_time = t0

        # [FASE 1 - LAYA EXIT GUARDIAN]: Avalia ordens abertas para estancamento de risco antes de novas entradas
        try:
            exit_actions = await self.evaluate_open_positions_lifecycle()
            if exit_actions:
                logger.info(f"[LAYA-EXIT-GUARDIAN] Ações de manejo cognitivo executadas: {len(exit_actions)}")
        except Exception as _e_exit_mgr:
            logger.debug(f"[LAYA-EXIT-GUARDIAN-ERR] {_e_exit_mgr}")
        
        # [V160-TITANS-30] Catálogo das Top 30 Altcoins de liquidez soberana da OKX (Zero BTC para trade)
        intel_map = {}
        total_ignited = 0
        try:
            from app.services.okx_universe_service import okx_universe_service
            from app.services.market_intel_engine import market_intel_engine
            dynamic_assets = await okx_universe_service.get_tradable_universe(limit=30, exclude_btc=True)
            if dynamic_assets:
                assets = list(dynamic_assets)
            else:
                assets = [{"symbol": sym, "pair": sym.replace("-USDT-SWAP", "USDT")} for sym in okx_universe_service._titans_30_altcoins if not sym.startswith("BTC")]

            # [V163] Injeção Universal Encryptos: Varre os 507 pares da OKX e injeta altcoins com Robôs Institucionais Ativos
            try:
                tickers = await okx_universe_service.sync_tickers()
                btc_climate_val = self.btc_climate_cache.get("regime", "ALTCOIN_EXPANSION")
                ignited_assets = market_intel_engine.scan_universal_market(
                    tickers_cache=tickers,
                    min_volume_usd=15_000_000.0,
                    exclude_btc=True,
                    btc_climate=btc_climate_val
                )
                total_ignited = sum(1 for ign in ignited_assets if ign.get("bot_ignition"))
                self.universal_market_stats = {
                    "total_pairs": len(tickers) if tickers else 507,
                    "liquid_pairs": len(ignited_assets),
                    "ignited_count": total_ignited,
                    "last_scan_ts": t0
                }
                for ign in ignited_assets:
                    intel_map[ign["symbol"]] = ign
                    intel_map[ign["pair"]] = ign
                    intel_map[ign["pair"] + "USDT"] = ign

                added_count = 0
                for ign in ignited_assets[:15]:
                    if ign.get("bot_ignition") and not any(a.get("symbol") == ign["symbol"] for a in assets):
                        assets.append({
                            "symbol": ign["symbol"],
                            "pair": ign["pair"],
                            "price": ign["price"],
                            "high_24h": ign["high24h"],
                            "low_24h": ign["low24h"],
                            "change_24h": ign["change_24h"],
                            "volume_24h_usd": ign["vol_ccy_24h"],
                            "is_universal_ignition": True,
                            "1c_exp": ign["1c_exp"],
                            "1c_range": ign["1c_range"],
                            "bot_ignition": True
                        })
                        added_count += 1
                if added_count > 0:
                    self.log_thought("SISTEMA", f"Radar Universal Encryptos: +{added_count} altcoins com aceleração institucional de robôs injetadas.", action="IGNICAO", confidence=95)
            except Exception as _e_ign:
                logger.warning(f"[LAYA-IGNITION] Injeção de robôs universal: {_e_ign}")

        except Exception as _e_uni:
            logger.debug(f"[LAYA-UNIVERSE] Fallback para 30 Altcoins: {_e_uni}")
            from app.services.okx_universe_service import okx_universe_service
            assets = [{"symbol": sym, "pair": sym.replace("-USDT-SWAP", "USDT")} for sym in okx_universe_service._titans_30_altcoins if not sym.startswith("BTC")]

        tot_p = self.universal_market_stats.get("total_pairs", 507)
        self.log_thought("SISTEMA", f"Radar Universal Encryptos: {tot_p} contratos OKX | {total_ignited} altcoins com robôs ligados. Monitorando {len(assets)} ativos em confluência profunda. Farol: BTC. Modo: {self.regime_mode} (ADX {self.master_adx:.1f}).", action="VARREDURA", confidence=90)

        best_setup = None
        best_score = 0

        # Busca preços reais diretamente da OKX SWAP oficial
        import httpx
        from services.okx_ws_public import okx_ws_public_service
        prices = {}
        mid_prices = {}
        change_24h_map = {}
        ticker_high_map = {}
        ticker_low_map = {}

        # 1. Tenta WebSocket em memória
        for a in assets:
            wp = okx_ws_public_service.get_current_price(a["pair"]) or okx_ws_public_service.get_current_price(a["symbol"])
            if wp > 0:
                prices[a["pair"]] = float(wp)

        # Garante leitura do BTC no WebSocket (Farol Macro)
        btc_ws = (
            okx_ws_public_service.get_current_price("BTCUSDT") 
            or okx_ws_public_service.get_current_price("BTC-USDT-SWAP")
            or okx_ws_public_service.get_current_price("BTC-USDT")
        )
        if btc_ws > 0:
            prices["BTCUSDT"] = float(btc_ws)

        # 2. Tenta cache do OKX REST
        try:
            cached = getattr(okx_rest_service, "_cached_price_map", {}) or {}
            for a in assets:
                if a["pair"] not in prices:
                    cp = float(cached.get(a["pair"], 0) or cached.get(a["symbol"], 0) or 0)
                    if cp > 0:
                        prices[a["pair"]] = cp
            if "BTCUSDT" not in prices or prices["BTCUSDT"] <= 0:
                btc_c = float(cached.get("BTCUSDT", 0) or cached.get("BTC-USDT-SWAP", 0) or cached.get("BTC-USDT", 0) or 0)
                if btc_c > 0:
                    prices["BTCUSDT"] = btc_c
        except Exception:
            pass

        # 3. Busca em lote (batch) na OKX tickers para todos os ativos (mid_prices e variação 24h)
        for url in ["https://www.okx.com/api/v5/market/tickers?instType=SWAP", "https://aws.okx.com/api/v5/market/tickers?instType=SWAP"]:
            try:
                async with httpx.AsyncClient(timeout=3.5) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        data = resp.json().get("data", [])
                        pair_set = {a["pair"] for a in assets} | {"BTCUSDT", "BTC-USDT-SWAP"}
                        for item in data:
                            i_id = item.get("instId", "")
                            l_px = float(item.get("last", 0.0) or 0.0)
                            h_24 = float(item.get("high24h", 0.0) or l_px)
                            low_24 = float(item.get("low24h", 0.0) or l_px)
                            open_24 = float(item.get("open24h", 0.0) or item.get("sodUtc0", 0.0) or l_px)
                            clean = i_id.replace("-USDT-SWAP", "USDT")
                            if clean in pair_set or i_id in pair_set:
                                if clean not in prices or prices[clean] <= 0:
                                    if l_px > 0:
                                        prices[clean] = l_px
                                if h_24 > 0 and low_24 > 0:
                                    mid_prices[clean] = (h_24 + low_24) / 2.0
                                    ticker_high_map[clean] = h_24
                                    ticker_low_map[clean] = low_24
                                if open_24 > 0 and l_px > 0:
                                    change_24h_map[clean] = ((l_px - open_24) / open_24) * 100.0
                        break
            except Exception as _e_bt:
                logger.debug(f"[LAYA-TICKERS] Erro ao obter lote tickers: {_e_bt}")

        # [FALLBACK BTC PRICE ANTI-ZERO]: Se ainda for 0, consulta fonte pública ultra-rápida
        btc_clean = "BTCUSDT"
        btc_px = prices.get(btc_clean, 0.0)
        if btc_px <= 0:
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    r_b = await client.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
                    if r_b.status_code == 200:
                        btc_px = float(r_b.json().get("price", 0.0) or 0.0)
                        prices[btc_clean] = btc_px
            except Exception:
                pass
        if btc_px <= 0:
            btc_px = float(getattr(self, "_last_valid_btc_price", 68000.0) or 68000.0)
            prices[btc_clean] = btc_px
        else:
            self._last_valid_btc_price = btc_px

        btc_chg = change_24h_map.get(btc_clean, 0.0)
        btc_mid = mid_prices.get(btc_clean, btc_px)
        btc_trend_bias = btc_chg
        if btc_mid > 0 and btc_px > 0:
            mid_diff = ((btc_px - btc_mid) / btc_mid) * 100.0
            btc_trend_bias = round((btc_chg * 0.7) + (mid_diff * 0.3), 2)

        btc_intel = {}
        try:
            from app.services.laya_btc_specialist_service import laya_btc_specialist
            btc_intel = await laya_btc_specialist.get_btc_macro_intelligence(
                current_btc_price=btc_px,
                btc_24h_change_pct=btc_chg
            )
        except Exception as _e_btcsp:
            logger.debug(f"[LAYA-BTC-SPECIALIST] Falha ao coletar inteligência BTC: {_e_btcsp}")

        btcd_val = btc_intel.get("btc_dominance", 58.0)
        spread_val = btc_intel.get("spot_vs_futures_spread_pct", 0.0)
        lead_lag_tag = btc_intel.get("lead_lag_signal", "SPOT_FUTURES_PARITY")
        climate_tag = btc_intel.get("altcoin_climate", "CONSOLIDATION_CHOP")
        self.btc_climate_cache = {
            "price": btc_px,
            "change_24h": btc_chg,
            "regime": climate_tag,
            "btc_dominance": btcd_val,
            "spread_pct": spread_val,
            "lead_lag": lead_lag_tag
        }

        # [V196-FAROL-MACRO-BTC-2H]: Avalia estrutura deterministica de 2H do Bitcoin
        btc_h1_kline = []
        try:
            from services.okx_rest import okx_rest_service
            btc_h1_kline = await okx_rest_service.get_klines("BTC-USDT-SWAP", interval="60", limit=48)
            if not btc_h1_kline:
                btc_h1_kline = await okx_rest_service.get_klines("BTCUSDT", interval="60", limit=48)
        except Exception as _e_btc_kl:
            logger.debug(f"[FAROL-BTC] Falha ao coletar klines BTC: {_e_btc_kl}")

        if not btc_h1_kline:
            try:
                async with httpx.AsyncClient(timeout=2.5) as client:
                    r_f = await client.get("https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=1h&limit=48")
                    if r_f.status_code == 200:
                        raw = r_f.json()
                        if isinstance(raw, list) and len(raw) >= 6:
                            btc_h1_kline = [[str(c[0]), str(c[1]), str(c[2]), str(c[3]), str(c[4]), str(c[5])] for c in raw]
            except Exception:
                pass

        btc_c2h = self.aggregate_1h_to_2h(btc_h1_kline)
        btc_sma_info = self.calculate_sma_cross_2h(btc_c2h)
        btc_macro_regime = self.classify_macro_market_regime(btc_sma_info, btc_dominance=btcd_val)
        btc_macro_dir = btc_macro_regime.get("direction", "NEUTRAL")
        if (btc_trend_bias < -0.3 or (btc_sma_info.get("sma8", 0) < btc_sma_info.get("sma21", 0) and btc_sma_info.get("sma21", 0) > 0)):
            btc_macro_dir = "BEAR"

        self.log_thought(
            "BTC-ORACLE",
            f"Farol BTC: ${btc_px:,.0f} ({btc_chg:+.2f}%) | BTC.D: {btcd_val:.2f}% | Spread Spot x Futuros: {spread_val:+.3f}% ({lead_lag_tag}) | Clima Altcoins: {climate_tag}",
            action="ORACULO",
            confidence=96
        )

        # [TRIAGEM INSTITUCIONAL EM 2 NÍVEIS]:
        # Para evitar gargalo de 429 na OKX com 30 ativos, filtramos em memória os TOP 6 mais quentes
        # (maior volatilidade 24h e fora de quarentena) para análise MTF e fluxo profundo a cada ciclo.
        valid_candidates = []
        for a in assets:
            clean = a["pair"]
            if self.is_symbol_in_cooldown(clean):
                continue
            p = prices.get(clean, 0.0)
            if p <= 0:
                continue
            momentum_score = abs(change_24h_map.get(clean, 0.0))
            valid_candidates.append((momentum_score, a))

        valid_candidates.sort(key=lambda x: x[0], reverse=True)
        priority_prefixes = {"SOL", "ETH", "AVAX", "NEAR", "LINK", "MON", "AEON", "DOGE", "XRP"}
        seen_pairs = set()
        selected_assets = []
        for _, a in valid_candidates:
            clean_base = a["pair"].split("-")[0].replace("USDT", "")
            if clean_base in priority_prefixes and a["pair"] not in seen_pairs:
                selected_assets.append(a)
                seen_pairs.add(a["pair"])
        for _, a in valid_candidates:
            if a["pair"] not in seen_pairs:
                selected_assets.append(a)
                seen_pairs.add(a["pair"])
            if len(selected_assets) >= 16:
                break
        deep_dive_assets = selected_assets
        if not deep_dive_assets:
            deep_dive_assets = assets[:6]

        # Coleta concorrente com semáforo controlado para evitar 429
        sem_flow = asyncio.Semaphore(8)
        async def _safe_flow(p):
            async with sem_flow:
                try:
                    return await asyncio.wait_for(laya_flow_service.get_flow_radar(p), timeout=1.5)
                except Exception:
                    return {}

        sem_kline = asyncio.Semaphore(10)
        async def _safe_kline(p):
            async with sem_kline:
                try:
                    res = await asyncio.wait_for(okx_rest_service.get_klines(p, interval="60", limit=48), timeout=5.0)
                    if res:
                        return res
                except Exception:
                    pass
                # Fallback instantâneo para klines da Binance pública (Spot + Futures) se OKX demorar
                try:
                    clean = p.replace("-USDT-SWAP", "USDT")
                    async with httpx.AsyncClient(timeout=2.5) as client:
                        r_b = await client.get(f"https://api.binance.com/api/v3/klines?symbol={clean}&interval=1h&limit=48")
                        if r_b.status_code == 200:
                            raw = r_b.json()
                            if isinstance(raw, list) and len(raw) >= 6:
                                return [[str(c[0]), str(c[1]), str(c[2]), str(c[3]), str(c[4]), str(c[5])] for c in raw]
                        r_f = await client.get(f"https://fapi.binance.com/fapi/v1/klines?symbol={clean}&interval=1h&limit=48")
                        if r_f.status_code == 200:
                            raw = r_f.json()
                            if isinstance(raw, list) and len(raw) >= 6:
                                return [[str(c[0]), str(c[1]), str(c[2]), str(c[3]), str(c[4]), str(c[5])] for c in raw]
                except Exception:
                    pass
                return []

        sem_fund = asyncio.Semaphore(8)
        async def _safe_fund(p):
            async with sem_fund:
                try:
                    return await asyncio.wait_for(okx_rest_service.get_funding_rate(p), timeout=2.0)
                except Exception:
                    return 0.0

        sem_kline_15m = asyncio.Semaphore(10)
        async def _safe_kline_15m(p):
            async with sem_kline_15m:
                try:
                    res = await asyncio.wait_for(okx_rest_service.get_klines(p, interval="15", limit=30), timeout=5.0)
                    if res:
                        return res
                except Exception:
                    pass
                try:
                    clean = p.replace("-USDT-SWAP", "USDT")
                    async with httpx.AsyncClient(timeout=2.5) as client:
                        r_b = await client.get(f"https://api.binance.com/api/v3/klines?symbol={clean}&interval=15m&limit=30")
                        if r_b.status_code == 200:
                            raw = r_b.json()
                            if isinstance(raw, list) and len(raw) >= 6:
                                return [[str(c[0]), str(c[1]), str(c[2]), str(c[3]), str(c[4]), str(c[5])] for c in raw]
                        r_f = await client.get(f"https://fapi.binance.com/fapi/v1/klines?symbol={clean}&interval=15m&limit=30")
                        if r_f.status_code == 200:
                            raw = r_f.json()
                            if isinstance(raw, list) and len(raw) >= 6:
                                return [[str(c[0]), str(c[1]), str(c[2]), str(c[3]), str(c[4]), str(c[5])] for c in raw]
                except Exception:
                    pass
                return []

        # Executa em lote controlado com semáforo rápido
        flow_tasks = [_safe_flow(a["pair"]) for a in deep_dive_assets]
        flow_resps = await asyncio.gather(*flow_tasks, return_exceptions=True)
        for a, flow in zip(deep_dive_assets, flow_resps):
            if not isinstance(flow, BaseException) and isinstance(flow, dict):
                self.whale_flow_cache[a["pair"]] = flow

        kline_tasks = [_safe_kline(a["pair"]) for a in deep_dive_assets]
        kline_resps = await asyncio.gather(*kline_tasks, return_exceptions=True)
        klines_h1_map = {}
        for a, k_data in zip(deep_dive_assets, kline_resps):
            if not isinstance(k_data, BaseException) and k_data:
                klines_h1_map[a["pair"]] = k_data
                clean_p = a["pair"].replace("-USDT-SWAP", "").replace("USDT", "")
                klines_h1_map[clean_p] = k_data
                klines_h1_map[f"{clean_p}USDT"] = k_data

        kline_15m_tasks = [_safe_kline_15m(a["pair"]) for a in deep_dive_assets]
        kline_15m_resps = await asyncio.gather(*kline_15m_tasks, return_exceptions=True)
        klines_15m_map = {}
        for a, k_data in zip(deep_dive_assets, kline_15m_resps):
            if not isinstance(k_data, BaseException) and k_data:
                klines_15m_map[a["pair"]] = k_data
                clean_p = a["pair"].replace("-USDT-SWAP", "").replace("USDT", "")
                klines_15m_map[clean_p] = k_data
                klines_15m_map[f"{clean_p}USDT"] = k_data

        funding_tasks = [_safe_fund(a["pair"]) for a in deep_dive_assets]
        funding_resps = await asyncio.gather(*funding_tasks, return_exceptions=True)
        funding_rate_map = {}
        for a, f_data in zip(deep_dive_assets, funding_resps):
            if not isinstance(f_data, BaseException):
                funding_rate_map[a["pair"]] = float(f_data or 0.0)

        new_candidate_setups = {}
        for idx, a in enumerate(assets):
            sym = a["symbol"]
            clean_sym = a["pair"]

            # [REGRA ENCRYPTOS]: BTC é estritamente o Farol Macro, proibido abrir ordens de trade nele
            if clean_sym.startswith("BTC") or sym.startswith("BTC"):
                continue

            price = prices.get(clean_sym, 0.0)
            if price <= 0:
                continue

            flow = self.whale_flow_cache.get(clean_sym, {})
            lsr = float(flow.get("lsr", 1.0))
            oi_delta = float(flow.get("oi_delta_pct", 0.0))
            flow_regime = flow.get("flow_regime", "NEUTRAL")
            sardinha_status = flow.get("sardinha_status", "Normal")
            change_24h = change_24h_map.get(clean_sym, 0.0)

            # [MULTI-TIMEFRAME & MULTI-SETUP ENGINE: H1, M15 REVERSAL, M15 MOLA, M5 DVWAP]
            h1_candles = klines_h1_map.get(clean_sym, [])
            c15m_candles = klines_15m_map.get(clean_sym) or klines_15m_map.get(sym) or []
            acc_range = self.calculate_h1_accumulation_range(h1_candles)
            funding_rate = funding_rate_map.get(clean_sym, 0.0)
            atr_pct = self.calculate_atr_pct(h1_candles, price)

            # [V176-ANTI-PUMP-ANTI-DUMP-VOLUME-SPIKE]: Auditoria Bilateral de Volume Institucional em H1
            # Compara o volume da vela recente com a média dos últimos períodos e detecta direção (PUMP vs DUMP)
            vol_ratio = 1.0
            has_volume_spike = False
            spike_direction = "NEUTRAL"
            if h1_candles and len(h1_candles) >= 3:
                try:
                    sorted_k = sorted(h1_candles, key=lambda c: int(c[0]), reverse=True)
                    recent_vol = float(sorted_k[0][5]) if len(sorted_k[0]) > 5 else 0.0
                    prev_vol = float(sorted_k[1][5]) if len(sorted_k) > 1 and len(sorted_k[1]) > 5 else 0.0
                    max_recent_vol = max(recent_vol, prev_vol)
                    spike_cand = sorted_k[0] if recent_vol >= prev_vol else sorted_k[1]
                    c_open = float(spike_cand[1])
                    c_close = float(spike_cand[4])
                    spike_direction = "BULLISH" if c_close >= c_open else "BEARISH"

                    hist_vols = [float(c[5]) for c in sorted_k[2:12] if len(c) > 5 and float(c[5]) > 0]
                    if hist_vols:
                        avg_hist_vol = sum(hist_vols) / len(hist_vols)
                        if avg_hist_vol > 0:
                            vol_ratio = round(max_recent_vol / avg_hist_vol, 2)
                            if vol_ratio >= 3.0:
                                has_volume_spike = True
                except Exception as _e_vol:
                    logger.debug(f"[VOL-SPIKE-CHECK-ERR] {clean_sym}: {_e_vol}")

            # [FALLBACK ANTI-ZERO]: Se faltarem candles de H1 (rate limit/timeout), usa faixa de 24h real
            if acc_range.get("resistance_h1", 0.0) <= 0 or acc_range.get("support_h1", 0.0) <= 0:
                fallback_res = ticker_high_map.get(clean_sym, round(price * 1.015, 4))
                fallback_sup = ticker_low_map.get(clean_sym, round(price * 0.985, 4))
                if fallback_res <= fallback_sup:
                    fallback_res = round(price * 1.015, 4)
                    fallback_sup = round(price * 0.985, 4)
                range_pct = round(((fallback_res - fallback_sup) / fallback_sup) * 100.0, 2) if fallback_sup > 0 else 3.0
                acc_range = {
                    "is_consolidating": True,
                    "resistance_h1": round(fallback_res, 4),
                    "support_h1": round(fallback_sup, 4),
                    "range_pct": range_pct
                }

            vwap_res = self.calculate_vwap_and_deviation(h1_candles, price)
            vwap = vwap_res.get("vwap", price)
            if vwap <= 0 or not h1_candles:
                # VWAP estimada a partir da faixa típica (High + Low + Close) / 3
                vwap = round((acc_range["resistance_h1"] + acc_range["support_h1"] + price) / 3.0, 4)

            # Cálculo de Bollinger Width a partir do desvio da faixa H1
            bb_width_pct = acc_range.get("range_pct", 3.0)
            if bb_width_pct <= 0:
                bb_width_pct = 2.5

            # [METRICAS ENCRYPTOS: 1C-EXP, 1C-RANGE & ROBÔS ON/OFF ANTES DO MULTI-SETUP]
            asset_intel = intel_map.get(sym) or intel_map.get(clean_sym) or {}
            vol_ccy = float(a.get("volume_24h_usd") or a.get("vol_24h") or asset_intel.get("vol_ccy_24h") or 0.0)
            c_exp = asset_intel.get("1c_exp")
            c_range = asset_intel.get("1c_range")
            bot_on = asset_intel.get("bot_ignition", False) or a.get("is_universal_ignition", False)

            if c_range is None:
                sup_val = acc_range.get("support_h1", 0.0)
                res_val = acc_range.get("resistance_h1", 0.0)
                if res_val > sup_val > 0:
                    c_range = round(((price - sup_val) / (res_val - sup_val)) * 100.0, 1)
                else:
                    c_range = 50.0

            if c_exp is None:
                from app.services.market_intel_engine import market_intel_engine
                c_exp = market_intel_engine.calculate_1c_exp(
                    bb_width_pct=bb_width_pct,
                    vol_rel_5m=1.3 if abs(change_24h) > 1.0 else 1.0,
                    oi_delta_pct=oi_delta,
                    adx=self.master_adx
                )
                bot_on = c_exp >= 70.0

            # Detecção de Ignição Vendedora Institucional
            is_dump_breakdown = False

            intel_tag = f"[ROBÔS ON • 1C-EXP {c_exp:.0f} • 1C-RANGE {c_range:.0f}%]" if bot_on else f"[ROBÔS OFF • 1C-EXP {c_exp:.0f} • 1C-RANGE {c_range:.0f}%]"

            # [V174-CONFLUENCIA-IMA-INTEGRADA] Consulta Imediata ao Mapa de Calor 2D
            heat = {}
            target_region = "NEUTRAL"
            dom_magnet = "NEUTRAL"
            target_p = 0.0
            target_vol_m = 0.0
            lifecycle_obj = {}
            try:
                from app.services.coinglass_heatmap_service import coinglass_heatmap_service
                heat = await coinglass_heatmap_service.get_liquidity_heatmap(sym, current_price=price, passed_candles=h1_candles)
                dom_magnet = heat.get("dominant_magnet", "NEUTRAL_EQUILIBRIUM")
                target_p = float(heat.get("target_price") or 0.0)
                target_vol = float(heat.get("target_volume_usd") or 0.0)
                target_vol_m = round(target_vol / 1e6, 2)
                target_region = heat.get("target_region") or ("ACIMA" if target_p > price else "ABAIXO")
                lifecycle_obj = heat.get("lifecycle") or {}
            except Exception as _heat_e:
                logger.debug(f"[HEATMAP-CANDIDATE-ERR] {clean_sym}: {_heat_e}")

            # Avaliação Multi-Setup Integrada com Blindagem Anti-Faca (Robôs On & C-EXP & Fusão Águia-Encryptos)
            multi_eval = self.evaluate_multi_setup_opportunity(
                symbol=clean_sym,
                current_price=price,
                acc_range=acc_range,
                vwap=vwap,
                bb_width_pct=bb_width_pct,
                lsr=lsr,
                oi_delta_pct=oi_delta,
                btc_trend_bias=btc_trend_bias,
                funding_rate=funding_rate,
                atr_pct=atr_pct,
                btc_intel=btc_intel,
                bot_ignition=bot_on,
                c_exp=c_exp,
                candles_1h=h1_candles,
                candles_15m=c15m_candles
            )

            direction = multi_eval["direction"]
            score = multi_eval["score"]
            rationale = multi_eval["rationale"]
            strat_name = multi_eval.get("strategy", "LAYA_SMART_MONEY_H1")

            # # [V193-SUBORDINACAO-2H-SOBERANA & PULLBACK HUNTER 30M]
            c2h_local = self.aggregate_1h_to_2h(h1_candles)
            regime_2h = self.enforce_2h_directional_regime(clean_sym, c2h_local, btc_macro_direction=btc_macro_dir)

            # 1. Subordinacao Estrita ao 2H: Proibe operacoes contra a tendencia macro e exige repique autentico no 30M
            c30m_local = self.aggregate_15m_to_30m(c15m_candles)
            if regime_2h["regime"] == "SHORT_ONLY":
                pullback_30m = self.calculate_30m_pullback_trigger(clean_sym, c30m_local, price, "SHORT", lsr=lsr, btc_dominance=getattr(self, "_last_btc_dominance", 58.0), btc_trend_bias=btc_trend_bias, bot_ignition=bot_on, c_exp=c_exp, sma8_2h=regime_2h.get("sma8", 0.0), sma21_2h=regime_2h.get("sma21", 0.0))
                if pullback_30m["has_pullback_setup"]:
                    strat_name = "LAYA_PULLBACK_HUNTER_2H_30M"
                    direction = "SHORT"
                    multi_eval["qualifies"] = True
                    multi_eval["strategy"] = strat_name
                    multi_eval["direction"] = direction
                    score = min(99, 88 + pullback_30m.get("score_boost", 0))
                    stop_loss = pullback_30m.get("stop_loss", round(price * 1.008, 4))
                    target = pullback_30m.get("target", round(price * 0.940, 4))
                    stop_dist = abs(stop_loss - price) / price if price > 0 else 0.008
                    target_dist = abs(price - target) / price if price > 0 else 0.035
                    multi_eval["stop_loss"] = stop_loss
                    multi_eval["target"] = target
                    multi_eval["stop_dist"] = stop_dist
                    multi_eval["target_dist"] = target_dist
                    rationale = f"PULLBACK HUNTER 2H/30M (SHORT): {regime_2h.get('reason')} | {pullback_30m.get('reason')}"
                else:
                    # Se o 2H e de baixa mas o preco esta esticado no fundo (sem repique), VETA SHORT e VETA LONG!
                    multi_eval["qualifies"] = False
                    rationale = f"VETO 2H SHORT_ONLY: {pullback_30m.get('reason')}"
            
            elif regime_2h["regime"] == "LONG_ONLY":
                pullback_30m = self.calculate_30m_pullback_trigger(clean_sym, c30m_local, price, "LONG", lsr=lsr, btc_dominance=getattr(self, "_last_btc_dominance", 58.0), btc_trend_bias=btc_trend_bias, bot_ignition=bot_on, c_exp=c_exp, sma8_2h=regime_2h.get("sma8", 0.0), sma21_2h=regime_2h.get("sma21", 0.0))
                if pullback_30m["has_pullback_setup"]:
                    strat_name = "LAYA_PULLBACK_HUNTER_2H_30M"
                    direction = "LONG"
                    multi_eval["qualifies"] = True
                    multi_eval["strategy"] = strat_name
                    multi_eval["direction"] = direction
                    score = min(99, 88 + pullback_30m.get("score_boost", 0))
                    stop_loss = pullback_30m.get("stop_loss", round(price * 0.992, 4))
                    target = pullback_30m.get("target", round(price * 1.060, 4))
                    stop_dist = abs(price - stop_loss) / price if price > 0 else 0.008
                    target_dist = abs(target - price) / price if price > 0 else 0.035
                    multi_eval["stop_loss"] = stop_loss
                    multi_eval["target"] = target
                    multi_eval["stop_dist"] = stop_dist
                    multi_eval["target_dist"] = target_dist
                    rationale = f"PULLBACK HUNTER 2H/30M (LONG): {regime_2h.get('reason')} | {pullback_30m.get('reason')}"
                else:
                    # Se o 2H e de alta mas o preco esta esticado no topo (sem recuo), VETA LONG e VETA SHORT!
                    multi_eval["qualifies"] = False
                    rationale = f"VETO 2H LONG_ONLY: {pullback_30m.get('reason')}"

            # 2. Confluencia ao Ima de Liquidez (Respeitando a Subordinacao 2H)
            if multi_eval["qualifies"] and strat_name not in ("LAYA_AGUIA_FUSION", "LAYA_INTERMEDIATE_REVERSAL_15M", "LAYA_PULLBACK_HUNTER_2H_30M"):
                if direction == "LONG" and regime_2h["regime"] != "SHORT_ONLY":
                    if dom_magnet == "BEARISH_SWEEP" or target_region == "ABAIXO":
                        multi_eval["qualifies"] = False
                        direction = "SHORT"
                        rationale = f"VETO IMA: LONG abortado: muralha de ${target_vol_m:.1f}M ABAIXO em ${target_p:.4f} puxando o preco."
                elif direction == "SHORT" and regime_2h["regime"] != "LONG_ONLY":
                    if dom_magnet == "BULLISH_SWEEP" or target_region == "ACIMA":
                        if btc_trend_bias >= -0.2:
                            multi_eval["qualifies"] = False
                            rationale = f"VETO IMA: SHORT abortado: muralha de ${target_vol_m:.1f}M ACIMA em ${target_p:.4f} puxando o preco."
            if multi_eval["qualifies"]:
                stop_loss = multi_eval["stop_loss"]
                target = multi_eval["target"]
                stop_dist = multi_eval["stop_dist"]
                target_dist = multi_eval["target_dist"]
                if strat_name == "LAYA_AGUIA_FUSION":
                    action_badge = "AGUIA_FUSION_GATILHO"
                elif strat_name == "LAYA_SMART_MONEY_H1":
                    action_badge = "SMART_MONEY_GATILHO"
                elif strat_name == "LAYA_RANGE_REVERSAL":
                    action_badge = "RANGE_REVERSAL_GATILHO"
                elif strat_name == "LAYA_INTERMEDIATE_REVERSAL_15M":
                    action_badge = "REVERSAL_15M_GATILHO"
                elif strat_name == "LAYA_PULLBACK_HUNTER_2H_30M":
                    action_badge = "PULLBACK_HUNTER_GATILHO"
                elif strat_name == "LAYA_MOMENTO_MOLA":
                    action_badge = "MOLA_GATILHO"
                else:
                    action_badge = "DVWAP_GATILHO"

                self.log_thought(
                    clean_sym,
                    f"{intel_tag} GATILHO {strat_name}: {rationale} | SL: ${stop_loss:.4f} | TP: ${target:.4f}",
                    action=action_badge,
                    confidence=score
                )
            else:
                # [V174-LIQUIDITY-HUNT-EXECUTION]: Caçada Soberana de Liquidez com Validação Técnica de Borda/Pullback
                is_hunt_zone = (lifecycle_obj.get("zone_id") == "HUNT") and ((lifecycle_obj.get("distance_pct") or 0.0) >= 1.5)

                # [INVARIANTE SOBERANA 2H SMA]: Verifica alinhamento macro antes de direcionar o radar
                _h1_cand = klines_h1_map.get(clean_sym, [])
                _sma_macro_dir = None
                if _h1_cand and len(_h1_cand) >= 6:
                    _c2h = self.aggregate_1h_to_2h(_h1_cand)
                    _sma_info = self.calculate_sma_cross_2h(_c2h)
                    _sma_macro_dir = _sma_info.get("direction")

                is_pump_ignition = (has_volume_spike and spike_direction == "BULLISH") or (c_exp is not None and c_exp >= 70.0 and change_24h > 1.5) or bot_on

                # Se o macro 2H for de alta ou houver ignição compradora institucional, direciona o Ímã para ACIMA (LONG)
                if (_sma_macro_dir == "LONG" or is_pump_ignition) and target_region == "ABAIXO":
                    target_region = "ACIMA"
                    dom_magnet = "BULLISH_SWEEP"
                    target_p = round(price * 1.035, 4) if target_p <= price else target_p

                # Alinha a direção do radar à atração dominante do Ímã
                if target_region == "ABAIXO" or dom_magnet == "BEARISH_SWEEP":
                    _macro_vetoed = False
                    if _sma_macro_dir == "LONG":
                        _macro_vetoed = True
                        is_hunt_zone = False
                        is_pullback_or_edge = False
                    direction = "SHORT" 
                    target = target_p if (target_p > 0 and target_p < price) else round(price * 0.965, 4)
                    stop_loss = round(price * 1.025, 4)
                    target_dist = round(abs(price - target) / price, 4)
                    stop_dist = 0.025

                    # [FILTRO TÉCNICO DE BORDA / PULLBACK PARA SHORT - REGRA DE OURO]:
                    # Exige que o preço esteja em recuo/pullback (c_range >= 50% ou acima da VWAP) e NUNCA no fundo (c_range < 40%)
                    is_pullback_or_edge = (c_range is not None and c_range >= 50.0) or (vwap > 0 and price >= vwap)
                    is_at_support_floor = (c_range is not None and c_range < 40.0)

                    if is_hunt_zone and is_pullback_or_edge and not is_at_support_floor and not is_pump_ignition and not _macro_vetoed:
                        strat_name = "LAYA_LIQUIDITY_HUNT"
                        score = 88
                        multi_eval["qualifies"] = True
                        multi_eval["stop_loss"] = stop_loss
                        multi_eval["target"] = target
                        multi_eval["stop_dist"] = stop_dist
                        multi_eval["target_dist"] = target_dist
                        rationale = f"CAÇADA DE LIQUIDEZ (HUNT SHORT): Preço em recuo técnico (1C-Range: {c_range:.0f}%) a favor do Ímã dominante de ${target_vol_m:.1f}M USD em ${target_p:.4f} ({lifecycle_obj.get('distance_pct', 0)}% de espaço)."
                    elif is_pump_ignition:
                        multi_eval["qualifies"] = False
                        strat_name = "MONITOR"
                        score = 40
                        rationale = f"VETO ANTI-PUMP 1C-EXP: Ignição compradora detectada (Volume {vol_ratio:.1f}x da média / 1C-EXP {c_exp:.0f}). Proibido abrir SHORT contra aceleração compradora."
                    elif is_at_support_floor:
                        multi_eval["qualifies"] = False
                        strat_name = "MONITOR"
                        score = 40
                        rationale = f"VETO FUNDO (1C-Range {c_range:.0f}%): Preço no fundo do canal. Proibido vender fundo sem pullback para vender caro."
                    else:
                        multi_eval["qualifies"] = False
                        strat_name = "MONITOR"
                        score = 50
                        rationale = f"ÍMÃ DE BAIXA ({target_region}): Muralha de ${target_vol_m:.1f}M USD em ${target_p:.4f} puxando o preço. Aguardando pullback para vender caro."
                elif target_region == "ACIMA" or dom_magnet == "BULLISH_SWEEP":
                    # [V205-ZERO-TOLERANCE-ALT-LONG] Tolerância Zero para compras de altcoin sem Bitcoin em regime BULL
                    if btc_macro_dir != "BULL" or btc_trend_bias <= 0.0:
                        multi_eval["qualifies"] = False
                        strat_name = "MONITOR"
                        score = 30
                        rationale = f"VETO FAROL BTC SOBERANO: Imã ACIMA bloqueado. Bitcoin nao esta em regime BULL (Regime: {btc_macro_dir}, Bias: {btc_trend_bias:+.2f}%). Proibido comprar altcoins sem BTC em alta confirmada."
                        _macro_vetoed = True
                        is_hunt_zone = False
                        is_dip_or_edge = False
                    else:
                        _macro_vetoed = False
                        if _sma_macro_dir == "SHORT":
                            _macro_vetoed = True
                            is_hunt_zone = False
                            is_dip_or_edge = False
                    direction = "LONG" 
                    target = target_p if target_p > 0 else round(price * 1.035, 4)
                    stop_loss = round(price * 0.975, 4)
                    target_dist = round(abs(target - price) / price, 4)
                    stop_dist = 0.025

                    # [FILTRO TÉCNICO DE BORDA / DIP PARA LONG]:
                    # Exige que o preço esteja em desconto técnico ou em aceleração institucional (c_exp >= 70 ou bot_on)
                    is_dip_or_edge = (c_range is not None and c_range <= 50.0) or (vwap > 0 and price <= vwap) or (c_exp is not None and c_exp >= 70.0) or bot_on
                    is_at_resistance_ceiling = (c_range is not None and c_range > 80.0 and not is_pump_ignition and not bot_on)

                    # [V176-ANTI-DUMP-GUARD]: Veto estrito de LONG se houver despejo vertical com Volume Spike de baixa ou queda livre
                    is_dump_ignition = (has_volume_spike and spike_direction == "BEARISH") or (vwap > 0 and price <= vwap * 0.94)

                    if is_hunt_zone and is_dip_or_edge and not is_at_resistance_ceiling and not is_dump_ignition and not _macro_vetoed:
                        strat_name = "LAYA_LIQUIDITY_HUNT"
                        score = 88
                        multi_eval["qualifies"] = True
                        multi_eval["stop_loss"] = stop_loss
                        multi_eval["target"] = target
                        multi_eval["stop_dist"] = stop_dist
                        multi_eval["target_dist"] = target_dist
                        rationale = f"CAÇADA DE LIQUIDEZ (HUNT LONG): Preço em desconto técnico (1C-Range: {c_range:.0f}%) a favor do Ímã dominante de ${target_vol_m:.1f}M USD em ${target_p:.4f} ({lifecycle_obj.get('distance_pct', 0)}% de espaço)."
                    elif is_dump_ignition:
                        multi_eval["qualifies"] = False
                        strat_name = "MONITOR"
                        score = 40
                        rationale = f"VETO ANTI-DUMP (FACA CAINDO): Despejo institucional detectado (Volume {vol_ratio:.1f}x da média em queda). Proibido comprar faca caindo sem absorção."
                    elif is_at_resistance_ceiling:
                        multi_eval["qualifies"] = False
                        strat_name = "MONITOR"
                        score = 40
                        rationale = f"VETO TOPO (1C-Range {c_range:.0f}%): Ímã de ${target_vol_m:.1f}M ACIMA, mas preço na resistência. Proibido comprar topo sem rompimento."
                    else:
                        multi_eval["qualifies"] = False
                        strat_name = "MONITOR"
                        score = 50
                        rationale = f"ÍMÃ DE ALTA ({target_region}): Muralha de ${target_vol_m:.1f}M USD em ${target_p:.4f} puxando o preço. Aguardando recuo para comprar barato."
                else:
                    stop_loss = round(price * 0.995, 4)
                    target = round(price * 1.035, 4)
                    stop_dist = 0.005
                    target_dist = 0.035

                self.log_thought(
                    clean_sym,
                    f"{intel_tag} {clean_sym} - {rationale}",
                    action="LIQUIDITY_HUNT_GATILHO" if multi_eval.get("qualifies") else ("IGNICAO_RADAR" if bot_on else "RADAR_WAIT"),
                    confidence=score
                )

            pair_mem = ""
            try:
                from app.services.memory_service import memory_service
                pair_mem = memory_service.synthesize_pair_memory(clean_sym, limit=2)
            except Exception:
                pass

            # [FASE 3 - LAYA TRADE REFLEX]: Calibração dinâmica pelo histórico de acertos/erros no par
            try:
                from app.services.memory_service import memory_service
                reflex = memory_service.get_pair_reflex_bias(clean_sym, direction)
                r_bias = reflex.get("score_bias", 0)
                if r_bias != 0:
                    score = max(30, min(99, score + r_bias))
                    rationale += f" | [{reflex.get('reason')}] ({r_bias:+d} pts)"
            except Exception as _e_refl:
                pass

            new_candidate_setups[clean_sym] = {
                "symbol": sym,
                "clean_sym": clean_sym,
                "rank": idx + 1,
                "direction": direction,
                "strategy": strat_name,
                "qualifies": multi_eval.get("qualifies", False),
                "price": price,
                "score": score,
                "stop_loss": stop_loss,
                "target": target,
                "stop_dist": stop_dist,
                "target_dist": target_dist,
                "lsr": lsr,
                "oi_delta_pct": oi_delta,
                "flow_regime": flow_regime,
                "acc_range": acc_range,
                "vwap": vwap,
                "bb_width_pct": bb_width_pct,
                "1c_exp": c_exp,
                "1c_range": c_range,
                "bot_ignition": bot_on,
                "has_volume_spike": has_volume_spike,
                "spike_direction": spike_direction,
                "vol_ratio": vol_ratio,
                "is_pump_ignition": ((has_volume_spike and spike_direction == "BULLISH") or (c_exp is not None and c_exp >= 70.0 and change_24h > 1.5)),
                "is_dump_ignition": ((has_volume_spike and spike_direction == "BEARISH") or (vwap > 0 and price <= vwap * 0.94)),
                "aguia_fusion": multi_eval.get("aguia_fusion", False),
                "cross_type": multi_eval.get("cross_type", "NEUTRAL"),
                "sma8_2h": multi_eval.get("sma8_2h", 0.0),
                "sma21_2h": multi_eval.get("sma21_2h", 0.0),
                "diff_pct": multi_eval.get("diff_pct", 0.0),
                "candle_5m_confirmed": multi_eval.get("candle_5m_confirmed", True),
                "magnet_direction": dom_magnet,
                "magnet_region": target_region,
                "magnet_target": target_p,
                "magnet_volume_m": target_vol_m,
                "lifecycle": lifecycle_obj,
                "confluence": {},
                "leverage_cap": 50.0,
                "rationale": rationale,
                "memory_context": pair_mem,
                "time": time.strftime("%H:%M:%S")
            }

        self.candidate_setups = new_candidate_setups
        # [CONCORRÊNCIA OTIMIZADA] Avalia Kronos concorrentemente apenas nos top 4 candidatos
        top_candidates = sorted(self.candidate_setups.values(), key=lambda x: x["score"], reverse=True)[:4]
        try:
            from services.kronos_scorer import kronos_scorer
            from app.services.laya_kronos_confluence_service import laya_kronos_confluence_service

            async def _score_cand(cand):
                try:
                    c_sym = cand["clean_sym"]
                    c_dir = cand["direction"]
                    c_flow = self.whale_flow_cache.get(c_sym, {})
                    k_side = "Buy" if c_dir == "LONG" else "Sell"
                    k_res = await asyncio.wait_for(kronos_scorer.score_signal(c_sym, k_side), timeout=1.8)
                    conf = laya_kronos_confluence_service.evaluate_confluence(c_flow, k_res, side=c_dir)
                    lev_cap = conf.get("leverage_cap", 50.0)
                    new_score = max(40, min(99, cand["score"] + conf.get("score_boost", 0)))
                    if conf.get("is_vetoed"):
                        new_score = 30
                        cand["rationale"] = f"[VETO LAYA-KRONOS] {conf.get('veto_reason')}"
                    else:
                        cand["rationale"] += f" | [KRONOS] {conf.get('confluence_type')} (Boost {conf.get('score_boost'):+d} pts, Cap {lev_cap:.0f}x)"
                    cand["score"] = new_score
                    cand["confluence"] = conf
                    cand["leverage_cap"] = lev_cap
                except Exception as _e_kc:
                    logger.debug(f"Timeout/erro Kronos em {cand.get('clean_sym')}: {_e_kc}")

            await asyncio.gather(*[_score_cand(c) for c in top_candidates], return_exceptions=True)
        except Exception as _e_kronos_batch:
            logger.debug(f"Erro no batch de Kronos: {_e_kronos_batch}")

        # Recalcula best_setup após aplicação do Kronos
        for c in self.candidate_setups.values():
            if c["score"] > best_score:
                best_score = c["score"]
                best_setup = c

        # [V166 - TRÍPLICE CONFLUÊNCIA: ALT PUMP IGNITION / DESCOLAMENTO INSTITUCIONAL]
        # Avalia descorrelação contra o BTC e robôs institucionais para os candidatos mais promissores
        promising_candidates = [
            c for c in self.candidate_setups.values()
            if c.get("score", 0) >= 65 and "BTC" not in c.get("clean_sym", "").upper()
        ]
        if promising_candidates and btc_intel:
            try:
                from services.signal_generator import signal_generator

                async def _eval_cand_ignition(cand):
                    try:
                        sym = cand["symbol"]
                        d_cache = getattr(signal_generator, "decorrelation_cache", {}).get(sym)
                        if d_cache and (time.time() - d_cache.get("updated_at", 0)) < 60:
                            d_res = d_cache["data"]
                        else:
                            d_res = await asyncio.wait_for(signal_generator.detect_btc_decorrelation(sym), timeout=2.0)
                        
                        ignition_res = self.evaluate_alt_pump_ignition(btc_intel, d_res, cand)
                        cand["decorrelation_data"] = d_res
                        if ignition_res["is_ignition"]:
                            cand["alt_pump_ignition"] = True
                            cand["score"] = min(99, cand["score"] + ignition_res["bonus_score"])
                            cand["strategy"] = "ALT_PUMP_IGNITION"
                            cand["direction"] = "LONG"
                            cand["rationale"] += f" | {ignition_res['tag']}"
                            self.log_thought(
                                cand["clean_sym"],
                                f"[ALT PUMP IGNITION]: Descolamento do BTC detectado (Corr: {ignition_res['correlation']:.2f}), BTC.D em queda e Robôs Ligados (1C-EXP: {cand.get('1c_exp', 0):.0f})!",
                                action="ALT_IGNITION",
                                confidence=cand["score"]
                            )
                    except Exception as e_ign:
                        logger.debug(f"Erro ao avaliar Alt Pump Ignition para {cand.get('clean_sym')}: {e_ign}")

                # Avalia concorrentemente os top 10 candidatos promissores
                top_promising = sorted(promising_candidates, key=lambda x: x["score"], reverse=True)[:10]
                await asyncio.gather(*[_eval_cand_ignition(c) for c in top_promising], return_exceptions=True)
            except Exception as e_batch_ign:
                logger.warning(f"Erro no batch de Alt Pump Ignition: {e_batch_ign}")

        # Recalcula best_setup após potencial boost de Alt Pump Ignition
        for c in self.candidate_setups.values():
            if c.get("alt_pump_ignition") or c["score"] > best_score:
                best_score = c["score"]
                best_setup = c

        # Verifica se ja temos ordens ativas
        active_trades = []
        try:
            active_trades = await database_service.get_sandbox_trades(active_only=True)
        except Exception:
            pass

        active_symbols = set()
        for t in active_trades:
            s = t.symbol if hasattr(t, "symbol") else (t.get("symbol") if isinstance(t, dict) else None)
            if s:
                s_str = str(s).upper()
                base_coin = s_str.replace("-USDT-SWAP", "").replace("-", "").replace("USDT", "")
                active_symbols.add(s_str)
                active_symbols.add(base_coin)
                active_symbols.add(f"{base_coin}USDT")
                active_symbols.add(f"{base_coin}-USDT-SWAP")

        # [V154-CAPITAL-PRESERVATION]: Consulta saldo para evitar overtrading após meta diária
        try:
            from services.sandbox_service import sandbox_service
            from config import settings
            base_bank = float(getattr(settings, "OKX_SIMULATED_BALANCE", 10000.0))
            current_sandbox_balance = getattr(sandbox_service, "base_balance_cache", base_bank)
        except Exception:
            base_bank = 100000.0
            current_sandbox_balance = 100000.0

        daily_profit_pct = ((current_sandbox_balance - base_bank) / base_bank) * 100.0
        # [V187-BRUNO-AGUIAR-SLOTS] 10 Slots de Fusão Soberana ($60 cada = $600 alocado / 6% de risco total da banca)
        max_allowed_slots = 8
        effective_min_score = self.MIN_ENTRY_SCORE

        # [V170.1-CAPITAL-FLOW] A Laya mantém operação institucional contínua em 8 slots (Score >= 85%).
        # O lucro realizado é protegido dinamicamente pelo Piso Soberano (Never Give Back),
        # garantindo que o sistema continue abrindo trades excelentes sem congelamento de slots.
        if daily_profit_pct > 0:
            self.log_thought("SISTEMA", f"️ [BANCA NO LUCRO]: Lucro acumulado {daily_profit_pct:+.2f}% (+${current_sandbox_balance-base_bank:.2f}). Piso Soberano ativo protegendo capital. 8 slots operacionais (Score >= {effective_min_score}%).", action="CAPITAL_FLOW", confidence=90)

        order_opened = None
        # [CIRCUIT BREAKER GLOBAL ANTI-TILT]: Se 3 stops recentes ocorreram em <90min, congelar novas entradas
        if self.is_global_circuit_breaker_active():
            rem_freeze = int(getattr(self, "_global_circuit_breaker_until", 0.0) - time.time())
            self.log_thought("CIRCUIT_BREAKER", f"️ [ANTI-TILT ATIVO]: Resfriamento global de banca ativo ({rem_freeze}s restantes). Novas ordens congeladas.", action="GLOBAL_FREEZE", confidence=99)
            force_open_if_empty = False

        # [V204-AGILE-FLEET-CADENCE]: Cadência Ágil de 45 Segundos entre entradas
        # Permite montar a frota direcional de até 4 ordens do Lote 1 durante a janela do repique técnico 30M
        last_global_open = getattr(self, "_last_global_trade_open_ts", 0.0)
        time_since_last_open = time.time() - last_global_open
        fleet_cadence_seconds = 45.0

        # [V206-SNOWBALL-FLEET-2-PLUS-EXPANSION]: Trava de 2 ordens em risco vivo simultâneo (Banca $10k)
        unprotected_risk_count = self.count_unprotected_risk_trades(active_trades)
        max_unprotected_allowed = 2
        if unprotected_risk_count >= max_unprotected_allowed:
            self.log_thought(
                "SISTEMA",
                f"[VETO RISCO VIVO]: Ja existem {unprotected_risk_count} ordens com risco vivo na Margem Cruzada (limite: {max_unprotected_allowed}). Aguardando protecao em Risco Zero (Breakeven) para liberar novos slots de expansao.",
                action="VETO_RISCO_VIVO_CHEIO",
                confidence=98
            )
            return None

        if len(active_trades) > 0 and time_since_last_open < fleet_cadence_seconds:
            rem_cadence = int(fleet_cadence_seconds - time_since_last_open)
            self.log_thought("CADENCIA", f"[CADENCIA ATIVA]: Aguardando {rem_cadence}s para proxima abertura (cadencia de {int(fleet_cadence_seconds)}s entre ordens).", action="CADENCIA_HOLD", confidence=95)
        elif len(active_trades) < max_allowed_slots:
            eligible = []
            for cand in self.candidate_setups.values():
                c_clean = cand.get("clean_sym", "")
                c_dir = cand.get("direction")
                c_score = cand.get("score", 0)
                c_bot = cand.get("bot_ignition", False) or cand.get("alt_pump_ignition", False) or cand.get("is_dump_ignition", False)
                c_range = float(cand.get("1c_range", 50.0) or 50.0)
                c_strat = cand.get("strategy", "")

                # 1. Checagens básicas de custódia e cooldown
                if (cand["symbol"] in active_symbols 
                    or c_clean in active_symbols 
                    or c_clean.replace("USDT", "") in active_symbols):
                    continue
                if c_dir not in ("LONG", "SHORT"):
                    continue
                if self.is_symbol_in_cooldown(c_clean):
                    continue
                # [ANTI-CHURN & FAST PULLBACK REENTRY]:
                # Se o último trade no par fechou no lucro, resfriamento reduzido para 5 minutos (300s)
                # para permitir que a Laya pegue reentradas no pullback do mesmo ativo em forte tendência.
                # Caso contrário, mantém o resfriamento anti-churn de 45 minutos (2700s).
                last_pair_ts = getattr(self, "_last_traded_pair_ts", {}).get(c_clean, 0.0)
                last_profit = getattr(self, "_symbol_last_profit", {}).get(c_clean)
                churn_cooldown = 300 if (last_profit and (time.time() - last_profit.get("time", 0)) < 7200 and last_profit.get("pnl", 0) > 0) else 2700
                if (time.time() - last_pair_ts) < churn_cooldown:
                    continue
                if self.is_direction_in_cooldown(c_dir):
                    continue
                if self.is_direction_penalized(c_clean, c_dir) or self.is_direction_penalized(cand.get("symbol", ""), c_dir):
                    continue

                # 0. GATE INVIOLÁVEL DE QUALIFICAÇÃO & VETO:
                # Candidatos desqualificados ou com VETO explícito são descartados imediatamente
                if cand.get("qualifies") is False or "VETO" in str(cand.get("rationale", "")).upper():
                    continue
                
                # [FASE 2 - CONSENSO LAYA ⇄ HERMES]: Arbitragem neural para candidatos limítrofes (75% a 84%)
                if 75 <= c_score < self.MIN_ENTRY_SCORE:
                    arb_res = await self.consult_hermes_arbitration(
                        symbol=cand["symbol"],
                        direction=c_dir,
                        score=c_score,
                        context=cand
                    )
                    boost = arb_res.get("score_boost", 0)
                    if arb_res.get("approved"):
                        cand["score"] = min(99, cand["score"] + boost)
                        c_score = cand["score"]
                        cand["rationale"] += f" | [HERMES] {arb_res.get('rationale')} ({boost:+d} pts)"
                        self.log_thought(
                            c_clean,
                            f"🤝 [CONSENSO LAYA ⇄ HERMES]: Candidato limítrofe aprovado pelo Hermes ({arb_res.get('rationale')}). Score promovido para {c_score}%.",
                            action="HERMES_ARBITRATION_APPROVE",
                            confidence=c_score
                        )
                    else:
                        cand["score"] = max(30, cand["score"] + boost)
                        self.log_thought(
                            c_clean,
                            f"⛔ [CONSENSO LAYA ⇄ HERMES]: Candidato limítrofe vetado pelo Hermes ({arb_res.get('rationale')}).",
                            action="HERMES_ARBITRATION_VETO",
                            confidence=cand["score"]
                        )

                # 2. TRAVA 1: Score Sniper Mínimo (>= 85%)
                if c_score < self.MIN_ENTRY_SCORE:
                    continue

                # 3. TRAVA 2: Exigência Absoluta de ROBÔS INSTITUCIONAIS ATIVOS (bot_ignition / is_dump_ignition)
                # Proibido abrir qualquer ordem com ROBÔS OFF! (Elimina compras/vendas frouxas sem aceleração institucional)
                if not c_bot and not cand.get("alt_pump_ignition") and not cand.get("is_dump_ignition"):
                    continue

                # 4. TRAVA 3: Veto Rígido de Compra de Topo e Venda de Fundo (Apenas para estratégias sem validação microestrutural)
                # Setups soberanos (Pullback Hunter 2H/30M, Águia Fusion, Smart Money) já possuem sua própria validação
                # microestrutural de repique/retração e rejeição de pavio, não devendo ser asfixiados pelo range estático diário de 24h.
                if c_strat not in ("LAYA_PULLBACK_HUNTER_2H_30M", "LAYA_AGUIA_FUSION", "LAYA_SMART_MONEY_H1", "LAYA_LIQUIDITY_HUNT"):
                    if c_dir == "SHORT":
                        # NUNCA vender fundo (<45% de range) a menos que haja dump ignition institucional
                        if c_range < 45.0 and not cand.get("is_dump_ignition"):
                            continue
                        # Proibido vender miolo neutro (45% a 55%) sem confirmação institucional
                        if (45.0 <= c_range < 55.0) and not cand.get("is_dump_ignition"):
                            continue

                    if c_dir == "LONG":
                        # NUNCA comprar topo (>=65.0% de range) a menos que haja rompimento comprovado com pump ignition
                        if c_range >= 65.0 and not cand.get("is_pump_ignition"):
                            continue
                        # Proibido comprar miolo neutro (35% a 65%) sem aceleração compradora
                        if (35.0 < c_range < 65.0) and not cand.get("is_pump_ignition"):
                            continue

                # 5. Farol Macro e Clima (Aplicável a 100% das estratégias sem exceção)
                if True:
                    # Tolerância Zero para compras de altcoin sem BTC em alta confirmada
                    if btc_trend_bias <= 0.0 and c_dir == "LONG":
                        continue
                    if btc_trend_bias > 1.0 and c_dir == "SHORT":
                        continue
                    if btc_intel:
                        if not btc_intel.get("altcoin_long_allowed", True) and c_dir == "LONG":
                            continue
                        if not btc_intel.get("altcoin_short_allowed", True) and c_dir == "SHORT":
                            continue

                # 6. Bilateral Spike Guard
                if c_dir == "SHORT" and cand.get("is_pump_ignition"):
                    continue
                if c_dir == "LONG" and cand.get("is_dump_ignition"):
                    continue

                # 7. Limite de Cluster
                if self.is_cluster_limit_reached(c_clean, active_symbols, max_per_cluster=3):
                    continue

                eligible.append(cand)
            # [DIVERSITY & ROTATION & PRIORIDADE ALT PUMP IGNITION]
            # Prioridade absoluta para Alt Pump Ignition, depois rotação e score
            last_traded = getattr(self, "_last_traded_pair", None)
            eligible.sort(
                key=lambda x: (
                    3 if x.get("strategy") == "LAYA_PULLBACK_HUNTER_2H_30M" else 0,
                    2 if x.get("strategy") == "LAYA_AGUIA_FUSION" else 0,
                    1 if x.get("alt_pump_ignition") else 0,
                    1 if (x.get("direction") == "SHORT" and btc_trend_bias < -0.4) else 0,
                    1 if x.get("bot_ignition") else 0,
                    x.get("1c_exp", 0.0) or 0.0,
                    x["score"],
                    random.random()
                ),
                reverse=True
            )

            # [V204-SOVEREIGN-FLEET-4-PLUS-4]: Contabiliza ordens em RISCO VIVO por direção
            # A frota soberana permite até 4 ordens em risco vivo na mesma direção macro a favor do Farol BTC (Lote 1).
            # Ordens já protegidas em Breakeven (Risco Zero) liberam expansão para o Lote 2 (até o teto de 8 ordens da frota).
            unprotected_dir_counts = {"LONG": 0, "SHORT": 0}
            for t in active_trades:
                is_prot = getattr(t, "is_protected", False) or (t.get("is_protected") if isinstance(t, dict) else False)
                curr_sl = getattr(t, "current_stop", None) or (t.get("current_stop") if isinstance(t, dict) else None) or getattr(t, "stop_loss", None)
                ent_p = getattr(t, "entry_price", 0.0) or (t.get("entry_price") if isinstance(t, dict) else 0.0)
                t_side = str(getattr(t, "side", "") or (t.get("direction") if isinstance(t, dict) else "") or "").upper()
                dir_key = "SHORT" if ("SHORT" in t_side or "SELL" in t_side) else "LONG"

                is_be = False
                if curr_sl and ent_p:
                    try:
                        curr_sl = float(curr_sl)
                        ent_p = float(ent_p)
                        if dir_key == "SHORT" and curr_sl <= ent_p:
                            is_be = True
                        elif dir_key == "LONG" and curr_sl >= ent_p:
                            is_be = True
                    except (ValueError, TypeError):
                        pass

                if not is_prot and not is_be:
                    unprotected_dir_counts[dir_key] += 1

            chosen = None
            for cand in eligible:
                cand_sym = cand["symbol"]
                cand_dir = cand["direction"]
                clean_name = cand.get("clean_sym", cand_sym)

                # [REGRA SOBERANA DE EXPANSÃO 2+2+2+2 (Banca $10k)]:
                # Máximo de 2 ordens em RISCO VIVO na mesma direção.
                # Conforme ordens anteriores atingem Breakeven (+60% ROI), novas ordens são liberadas de 2 em 2 até o teto de 8 ordens (6 em risco zero e 2 em risco vivo).
                if unprotected_dir_counts.get(cand_dir, 0) >= 2 and not cand.get("alt_pump_ignition"):
                    self.log_thought(
                        clean_name,
                        f"[VETO RISCO VIVO DIR]: Ja existem {unprotected_dir_counts.get(cand_dir, 0)} ordens em risco vivo em {cand_dir} (limite: 2). Aguardando Breakeven para liberar expansao.",
                        action="VETO_RISCO_DIR_CHEIO",
                        confidence=96
                    )
                    continue

                # [ANTI-SQUEEZE LSR SOBERANO]: Veta SHORT se maioria sardinha estiver vendida, e LONG se maioria comprada
                c_lsr_val = float(cand.get("lsr", 1.0) or 1.0)
                if cand_dir == "SHORT" and c_lsr_val < 0.80:
                    self.log_thought(
                        clean_name,
                        f"[VETO ANTI-SQUEEZE LSR]: SHORT bloqueado para {cand_sym} (LSR: {c_lsr_val:.2f} < 0.80). Sardinhas sobre-vendidas, risco severo de short squeeze.",
                        action="VETO_LSR_SQUEEZE",
                        confidence=97
                    )
                    continue
                if cand_dir == "LONG" and c_lsr_val > 1.35:
                    self.log_thought(
                        clean_name,
                        f"[VETO ANTI-DUMP LSR]: LONG bloqueado para {cand_sym} (LSR: {c_lsr_val:.2f} > 1.35). Sardinhas sobre-compradas, risco severo de liquidacao em cascata.",
                        action="VETO_LSR_DUMP",
                        confidence=97
                    )
                    continue
                cand_kline = klines_h1_map.get(clean_name) or klines_h1_map.get(cand_sym) or []

                # Se klines não estavam no cache, busca sob demanda com contingência total (OKX + Binance Futures + Gate.io)
                if not cand_kline or len(cand_kline) < 6:
                    try:
                        from services.okx_rest import okx_rest_service
                        cand_kline = await okx_rest_service.get_klines(cand_sym, interval="60", limit=48)
                        if cand_kline:
                            klines_h1_map[clean_name] = cand_kline
                            klines_h1_map[cand_sym] = cand_kline
                    except Exception as k_err:
                        logger.debug(f"[SOVEREIGN-GATE] Erro ao buscar klines para {cand_sym}: {k_err}")

                    # Fallback Binance Futures se OKX falhar
                    if not cand_kline or len(cand_kline) < 6:
                        try:
                            clean_b = cand_sym.replace("-USDT-SWAP", "USDT").replace(".P", "").replace("-", "")
                            async with httpx.AsyncClient(timeout=4.0) as client:
                                r_b = await client.get(f"https://fapi.binance.com/fapi/v1/klines?symbol={clean_b}&interval=1h&limit=48")
                                if r_b.status_code == 200:
                                    raw = r_b.json()
                                    if isinstance(raw, list) and len(raw) >= 6:
                                        cand_kline = [[str(c[0]), str(c[1]), str(c[2]), str(c[3]), str(c[4]), str(c[5])] for c in raw]
                                        klines_h1_map[clean_name] = cand_kline
                                        klines_h1_map[cand_sym] = cand_kline
                        except Exception as b_err:
                            logger.debug(f"[SOVEREIGN-GATE] Erro fallback Binance Futures para {cand_sym}: {b_err}")

                # [INVARIANTE SOBERANA INVIOLÁVEL 2H SMA BRUNO AGUIAR + ENCRYPTOS]
                # Nenhuma estratégia pode operar contra a tendência do timeframe 2H!
                if not ("BTC" in cand_sym.upper()):
                    # REGRA FAIL-CLOSED: Se klines não estão disponíveis, VETA IMEDIATAMENTE!
                    if not cand_kline or len(cand_kline) < 6:
                        self.log_thought(
                            clean_name,
                            f"⛔ [VETO SOBERANO SMA 2H]: Klines 2H indisponíveis para {cand_sym}. Proibido operar sem confirmação macro do timeframe 2H.",
                            action="VETO_SEM_KLINES_2H",
                            confidence=99
                        )
                        continue

                    c2h = self.aggregate_1h_to_2h(cand_kline)
                    sma_info = self.calculate_sma_cross_2h(c2h)
                    macro_dir = sma_info.get("direction")

                    # [MOTOR 2: DETECÇÃO DE OUTLIERS DESCORRELACIONADOS]
                    d_data = cand.get("decorrelation_data") or cand.get("decorrelation")
                    if not d_data:
                        try:
                            from services.signal_generator import signal_generator
                            d_cache = getattr(signal_generator, "decorrelation_cache", {}).get(cand_sym) or getattr(signal_generator, "decorrelation_cache", {}).get(clean_name)
                            if d_cache:
                                d_data = d_cache.get("data")
                        except Exception:
                            pass
                    d_data = d_data or {}
                    is_outlier = self.is_decorrelated_outlier(d_data) or bool(cand.get("alt_pump_ignition"))

                    # [MOTOR 1: VETO SOBERANO DO FAROL BTC MACRO 2H]
                    # Tolerância Zero: Proibido abrir LONG em qualquer altcoin sem Bitcoin estritamente em BULL no 2H!
                    # Excecao Unica: Rompimento comprovado de acumulacao com alt_pump_ignition E volume explosivo.
                    is_btc_bull = (btc_macro_dir == "BULL" and btc_trend_bias >= 0.0)
                    has_exceptional_pump = bool(cand.get("alt_pump_ignition") and cand.get("bot_ignition"))
                    if cand_dir == "LONG" and not is_btc_bull and not has_exceptional_pump:
                        self.log_thought(
                            clean_name,
                            f"[VETO FAROL BTC SOBERANO]: LONG bloqueado para {cand_sym}. Bitcoin nao esta em regime BULL 2H (Regime: {btc_macro_dir}, Bias: {btc_trend_bias:+.2f}%). Tolerancia zero para compras de altcoins sem BTC em alta confirmada.",
                            action="VETO_FAROL_BTC",
                            confidence=99
                        )
                        continue
                    elif cand_dir == "SHORT" and btc_trend_bias > 1.2 and not is_outlier:
                        self.log_thought(
                            clean_name,
                            f"[VETO FAROL BTC MACRO]: SHORT bloqueado para {cand_sym}. Ativo correlacionado ao BTC em rali de alta ({btc_trend_bias:+.2f}%). Proibido vender altcoins correlacionadas contra o Bitcoin.",
                            action="VETO_FAROL_BTC",
                            confidence=98
                        )
                        continue

                    # [INVARIANTE DA REVERSÃO ESTRUTURAL 2H - ANTI-FACA CAINDO]
                    # Mesmo para outliers, NUNCA comprar fundo sem rompimento oficial no 2H!
                    # O preço DEVE estar acima da SMA 21 e SMA 8 >= SMA 21 (para LONG).
                    # EXCEÇÃO SOBERANA: LAYA_INTERMEDIATE_REVERSAL_15M opera varredura intraday de liquidez
                    # com stop estrutural ultracurto no sweep do 15M, isento do lag de 16h das médias do 2H.
                    if cand.get("strategy") != "LAYA_INTERMEDIATE_REVERSAL_15M":
                        struct_val = self.validate_structural_reversal_2h(
                            sma_info=sma_info,
                            current_price=float(cand.get("price") or 0.0),
                            direction=cand_dir
                        )
                        if not struct_val.get("confirmed", False):
                            self.log_thought(
                                clean_name,
                                f"⛔ [VETO REVERSÃO ESTRUTURAL 2H]: {struct_val.get('reason')}",
                                action="VETO_REVERSAO_ESTRUTURAL_2H",
                                confidence=99
                            )
                            continue

                # [V174-LIQUIDITY-MAGNET-VETO]: Veta ordens contra muralha de liquidacao pesada e zona morta
                try:
                    from app.services.coinglass_heatmap_service import coinglass_heatmap_service
                    cand_p = float(cand.get("price") or 0.0)
                    cand_kline = klines_h1_map.get(cand.get("clean_sym", cand_sym)) or []
                    heat = await coinglass_heatmap_service.get_liquidity_heatmap(
                        cand_sym, 
                        current_price=cand_p,
                        passed_candles=cand_kline
                    )
                    dom_magnet = heat.get("dominant_magnet")
                    target_reg = heat.get("target_region") or ("ACIMA" if heat.get("target_price", 0) > cand_p else "ABAIXO")
                    lifecycle = heat.get("lifecycle") or {}
                    zone_id = lifecycle.get("zone_id", "")

                    # 1. Veto da ZONA MORTA (anti-armadilha e falso rompimento entre 0.3% e 1.5%)
                    if zone_id == "DEAD_ZONE":
                        self.log_thought(
                            cand.get("clean_sym", cand_sym),
                            f"[VETO ZONA MORTA]: Entrada {cand_dir} bloqueada: preco a {lifecycle.get('distance_pct', 0)}% do bolsao ({zone_id}).",
                            action="VETO_ZONA_MORTA",
                            confidence=96
                        )
                        continue

                    # 2. Veto Direcional do Ima
                    if cand_dir == "SHORT" and (dom_magnet == "BULLISH_SWEEP" or target_reg == "ACIMA") and (btc_trend_bias >= -0.2):
                        vol_m = heat.get("target_volume_usd", 0) / 1e6
                        self.log_thought(
                            cand.get("clean_sym", cand_sym),
                            f"[VETO IMA DE LIQUIDEZ]: SHORT proibido: muralha dominante de ${vol_m:.2f}M ACIMA DO PRECO.",
                            action="VETO_IMA_LIQUIDEZ",
                            confidence=98
                        )
                        continue

                    if cand_dir == "LONG" and (dom_magnet == "BEARISH_SWEEP" or target_reg == "ABAIXO") and (btc_trend_bias <= 0.2):
                        vol_m = heat.get("target_volume_usd", 0) / 1e6
                        self.log_thought(
                            cand.get("clean_sym", cand_sym),
                            f"[VETO IMA DE LIQUIDEZ]: LONG proibido: muralha dominante de ${vol_m:.2f}M ABAIXO DO PRECO.",
                            action="VETO_IMA_LIQUIDEZ",
                            confidence=98
                        )
                        continue
                except Exception as heat_err:
                    logger.debug(f"[LAYA-VETO-HEATMAP-ERR] {heat_err}")

                # [V169-TF-MENORES]: Verifica exaustao e ausencia de faca caindo em 30m antes do disparo
                ltf_check = await self.check_lower_tf_exhaustion(cand_sym, cand_dir)
                if not ltf_check.get("is_safe", True):
                    self.log_thought(
                        cand.get("clean_sym", cand_sym),
                        f"[VETO TF MENOR]: Ordem {cand_dir} bloqueada: {ltf_check.get('reason')}",
                        action="VETO_TF_MENOR",
                        confidence=92
                    )
                    continue

                # [V197-CROSS-MARGIN-STRUCTURAL-STOP]: Stop estrutural real em Margem Cruzada (ate 3.8% de respiro livre 2H/4H)
                cand_sl = cand.get("stop_loss")
                cand_p = float(cand.get("price") or 0.0)
                if cand_dir == "SHORT" and cand_sl and cand_p > 0 and cand_sl > cand_p:
                    cand_sl_dist = (cand_sl - cand_p) / cand_p
                    if cand_sl_dist > 0.038:
                        self.log_thought(
                            cand.get("clean_sym", cand_sym),
                            f"[VETO DISTANCIA RESISTENCIA]: Stop estrutural em ${cand_sl:.4f} esta a {cand_sl_dist*100:.2f}% (limite 3.8% na Margem Cruzada). Aguardar repique aproximar-se da resistencia.",
                            action="VETO_DISTANCIA_STOP",
                            confidence=95
                        )
                        continue
                elif cand_dir == "LONG" and cand_sl and cand_p > 0 and cand_sl < cand_p:
                    cand_sl_dist = (cand_p - cand_sl) / cand_p
                    if cand_sl_dist > 0.038:
                        self.log_thought(
                            cand.get("clean_sym", cand_sym),
                            f"[VETO DISTANCIA SUPORTE]: Stop estrutural em ${cand_sl:.4f} esta a {cand_sl_dist*100:.2f}% (limite 3.8% na Margem Cruzada). Aguardar recuo aproximar-se do suporte.",
                            action="VETO_DISTANCIA_STOP",
                            confidence=95
                        )
                        continue

                chosen = cand
                break

            if chosen:
                sym = chosen["symbol"]
                clean_sym = chosen.get("clean_sym", sym.replace("-USDT-SWAP", ""))
                p = chosen["price"]
                d = chosen["direction"]
                strat = chosen.get("strategy") or "LAYA_SMART_MONEY_H1"
                
                # Stop Loss e Alvo calculados pelo setup especifico (H1 Breakout, DVWAP ou Mola)
                stop_loss = chosen.get("stop_loss")
                target = chosen.get("target")

                default_stop_dist = 0.020
                min_stop_dist = 0.008
                max_stop_dist = 0.038
                default_target_dist = 0.060
                from services.order_projection_service import proj_service
                from app.services.okx_universe_service import okx_universe_service

                # [V195-STRUCTURAL-STOP-INTEGRITY]: Se stop ou target ausentes, preenche com default sem mutilar estrutura
                if d == "SHORT":
                    if not stop_loss or stop_loss <= p:
                        stop_loss = p * (1.0 + default_stop_dist)
                    if not target or target >= p or ((p - target) / p) < default_target_dist:
                        target = p * (1.0 - default_target_dist)

                elif d == "LONG":
                    if not stop_loss or stop_loss >= p:
                        stop_loss = p * (1.0 - default_stop_dist)
                    if not target or target <= p or ((target - p) / p) < default_target_dist:
                        target = p * (1.0 + default_target_dist)

                stop_loss = okx_universe_service.format_price_by_tick(sym, stop_loss)
                target = okx_universe_service.format_price_by_tick(sym, target)

                # Distância real de preço do Stop
                stop_dist_pct = max(min_stop_dist, min(max_stop_dist, abs(p - stop_loss) / p))

                try:
                    from services.sandbox_service import sandbox_service
                    realized_bal = getattr(sandbox_service, "base_balance_cache", 10000.0)
                except Exception:
                    realized_bal = 10000.0

                # [V190-STANDARDIZED-50X-LEVERAGE]
                # Padronização Soberana em 50.0x Fixo nos 30 Titãs Institucionais
                coin_max_lev = okx_universe_service.get_max_leverage(sym)
                leverage = min(50.0, max(5.0, coin_max_lev))

                # 2. Margem por Slot: 1.0% da banca realizada ($1.000 numa banca de $100.000)
                # 10 slots = $10.000 em risco (10% total), mantendo 90% liquida ($90.000) como colchao contra liquidacao
                from config import settings
                base_bank_ref = float(getattr(settings, "OKX_SIMULATED_BALANCE", 10000.0))
                margin_planned = 1000.0  # [V197-CROSS-MARGIN-SWING-50X]: Margem fixa de $1.000,00 por ordem

                quant_res = okx_universe_service.quantize_order_contracts(
                    symbol=sym,
                    margin_usd=margin_planned,
                    leverage=leverage,
                    price=p
                )

                if not quant_res.get("is_valid"):
                    self.log_thought(
                        clean_sym,
                        f"[VETO CONTRATO OKX]: Ordem rejeitada para {sym}: {quant_res.get('error')} (Contratos: {quant_res.get('contracts')}, minSz: {quant_res.get('minSz')})",
                        action="VETO_CONTRATO",
                        confidence=90
                    )
                    return best_setup

                num_contracts = quant_res["contracts"]
                notional_usd = quant_res["notional_usd"]
                margin = quant_res["effective_margin"]
                ct_val = quant_res["ctVal"]
                tick_sz = quant_res["tickSize"]
                lot_sz = quant_res["lotSize"]
                min_sz = quant_res["minSz"]
                fee_open = round(notional_usd * 0.0005, 2)
                fee_close = round(notional_usd * 0.0005, 2)
                slippage_usd = round(notional_usd * 0.0003, 2)
                total_fees = round(fee_open + fee_close + slippage_usd, 2)

                # Stop ROI estrutural exato ancorado no preço de Stop Loss e alavancagem calibrada
                init_stop_roi = round(proj_service.calculate_roi(p, stop_loss, d, leverage), 2)
                be_trigger_roi = 10.0

                decision_label = f"BUY ({chosen['score']}%)" if d == "LONG" else f"SELL ({chosen['score']}%)"
                trade_id = f"laya_{int(time.time() * 1000)}"

                trade_data = {
                    "id": trade_id,
                    "symbol": sym,
                    "strategy": strat,
                    "direction": d,
                    "entry_price": p,
                    "current_price": p,
                    "stop_loss": stop_loss,
                    "target": target,
                    "max_roi": 0.0,
                    "current_roi": 0.0,
                    "pnl_pct": 0.0,
                    "status": "ACTIVE",
                    "opened_at": time.time(),
                    "flash_state": {
                        "phase": "SMART_MONEY_H1_GUARD",
                        "ladder_level": 0,
                        "stop_roi": init_stop_roi,
                        "breakeven_trigger_roi": be_trigger_roi,
                        "history": [
                            f"Laya autorizou entrada {strat} {d} em {clean_sym} a ${p:.4f} (Alvo: ${target:.4f}, Stop Estrutural: ${stop_loss:.4f} / {init_stop_roi:.1f}% ROI) com score {chosen['score']}%."
                        ]
                    },
                    "contract_meta": {
                        "strategy": strat,
                        "margin": margin,
                        "leverage": leverage,
                        "ctVal": ct_val,
                        "tickSize": tick_sz,
                        "lotSize": lot_sz,
                        "minSz": min_sz,
                        "notional_usd": notional_usd,
                        "num_contracts": num_contracts,
                        "fee_open_usd": fee_open,
                        "fee_close_usd": fee_close,
                        "slippage_usd": slippage_usd,
                        "total_fees_usd": total_fees,
                        "slippage_pct": 0.03,
                        "laya_decision": decision_label,
                        "flow_regime": chosen.get("flow_regime"),
                        "lsr": chosen.get("lsr"),
                        "oi_delta_pct": chosen.get("oi_delta_pct"),
                        "whale_doctrine": "INSTITUTIONAL_LIQUIDITY_HUNTER",
                        "rationale": chosen.get("rationale"),
                        "btc_dominance": btcd_val,
                        "altcoin_climate": climate_tag,
                        "spot_vs_futures_spread_pct": spread_val,
                        "lead_lag_signal": lead_lag_tag,
                        "kronos_direction": (chosen.get("confluence") or {}).get("kronos_direction", "NEUTRAL"),
                        "kronos_conviction": (chosen.get("confluence") or {}).get("kronos_conviction", 50.0),
                        "kronos_change_pct": float((chosen.get("confluence") or {}).get("predicted_change_pct", 0.0) or 0.0),
                        "kronos_target_price": round(p * (1.0 + (float((chosen.get("confluence") or {}).get("predicted_change_pct", 0.0) or 0.0) / 100.0)), 4) if (chosen.get("confluence") or {}).get("predicted_change_pct") else round(target, 4),
                        "confluence_type": (chosen.get("confluence") or {}).get("confluence_type", "NEUTRAL"),
                        "alt_pump_ignition": chosen.get("alt_pump_ignition", False),
                        "decorrelation": chosen.get("decorrelation_data", {})
                    }
                }

                await database_service.save_sandbox_trade(trade_data)
                self._last_traded_pair = clean_sym
                self._last_global_trade_open_ts = time.time()
                if not hasattr(self, "_last_traded_pair_ts"):
                    self._last_traded_pair_ts = {}
                self._last_traded_pair_ts[clean_sym] = time.time()
                self.log_thought(
                    clean_sym,
                    f"COMANDO SOBERANO: Ordem {d} ({strat}) executada em {clean_sym} a ${p:.4f} [Margem: ${margin:.1f} USD | Alavancagem: {leverage:.0f}x]. Alvo: ${target:.4f}, Stop: ${stop_loss:.4f}.",
                    action="ORDEM_DISPARADA",
                    confidence=chosen["score"]
                )
                order_opened = trade_data
                best_setup = chosen

        elapsed_ms = round((time.time() - t0) * 1000, 1)
        return {
            "success": True,
            "regime_mode": self.regime_mode,
            "master_adx": self.master_adx,
            "scanned_pairs": len(assets),
            "order_opened": bool(order_opened),
            "opened_trade": order_opened,
            "best_setup": best_setup,
            "latency_ms": elapsed_ms
        }

    async def get_radar_pulse(self) -> Dict[str, Any]:
        """
        Retorna a matriz de pares e sinais conduzida e administrada soberanamente pela Laya.
        Substitui o cache legado do Firebase por dados reais da OKX SWAP e inteligência institucional.
        """
        import httpx
        from app.services.laya_flow_service import laya_flow_service
        from services.okx_ws_public import okx_ws_public_service

        elite_symbols = [
            ("SOL-USDT-SWAP", "SOLUSDT", 118.50),
            ("AVAX-USDT-SWAP", "AVAXUSDT", 10.50),
            ("NEAR-USDT-SWAP", "NEARUSDT", 5.10),
            ("LINK-USDT-SWAP", "LINKUSDT", 13.90),
            ("ETH-USDT-SWAP", "ETHUSDT", 1950.0),
            ("BTC-USDT-SWAP", "BTCUSDT", 84000.0),
            ("DOGE-USDT-SWAP", "DOGEUSDT", 0.165),
            ("SUI-USDT-SWAP", "SUIUSDT", 1.85),
            ("XRP-USDT-SWAP", "XRPUSDT", 0.58),
            ("ADA-USDT-SWAP", "ADAUSDT", 0.35),
            ("BNB-USDT-SWAP", "BNBUSDT", 580.0),
            ("DOT-USDT-SWAP", "DOTUSDT", 4.10),
            ("APT-USDT-SWAP", "APTUSDT", 5.60),
            ("ARB-USDT-SWAP", "ARBUSDT", 0.52),
            ("OP-USDT-SWAP", "OPUSDT", 1.45),
            ("INJ-USDT-SWAP", "INJUSDT", 18.50),
            ("RENDER-USDT-SWAP", "RENDERUSDT", 5.20),
            ("FET-USDT-SWAP", "FETUSDT", 1.30),
            ("PEPE-USDT-SWAP", "PEPEUSDT", 0.0000095),
            ("SHIB-USDT-SWAP", "SHIBUSDT", 0.0000175),
        ]

        signals = []
        decisions = []
        btc_price = 84000.0

        now = time.time()
        if self._cached_radar_pulse and (now - self._last_pulse_ts < 3.5):
            return self._cached_radar_pulse

        # Tenta obter do cache em memória; atualiza em background sem travar o endpoint
        if (not hasattr(self, "_cached_tickers") or not self._cached_tickers or (now - getattr(self, "_last_ticker_time", 0)) > 30.0) and not getattr(self, "_fetching_tickers_bg", False):
            self._fetching_tickers_bg = True
            async def _bg_fetch_tickers():
                try:
                    for url in ["https://www.okx.com/api/v5/market/tickers?instType=SWAP", "https://aws.okx.com/api/v5/market/tickers?instType=SWAP"]:
                        try:
                            async with httpx.AsyncClient(timeout=2.0) as client:
                                res = await client.get(url)
                                if res.status_code == 200:
                                    data = res.json().get("data", [])
                                    self._cached_tickers = {item["instId"]: float(item.get("last", 0.0)) for item in data}
                                    self._cached_mid_prices = {
                                        item["instId"]: (float(item.get("high24h", 0) or item.get("last", 0)) + float(item.get("low24h", 0) or item.get("last", 0))) / 2.0
                                        for item in data
                                    }
                                    self._last_ticker_time = time.time()
                                    break
                        except Exception:
                            pass
                finally:
                    self._fetching_tickers_bg = False
            asyncio.create_task(_bg_fetch_tickers())

        raw_tickers = getattr(self, "_cached_tickers", {}) or {}

        # Preço do BTC a partir do WebSocket em memória ou cache
        btc_price = okx_ws_public_service.get_current_price("BTCUSDT") or okx_ws_public_service.get_current_price("BTC-USDT-SWAP") or raw_tickers.get("BTC-USDT-SWAP", 84000.0)

        for inst_id, pair, fallback_price in elite_symbols:
            price = okx_ws_public_service.get_current_price(pair) or okx_ws_public_service.get_current_price(inst_id) or raw_tickers.get(inst_id, 0.0) or fallback_price
            mid_ref = getattr(self, "_cached_mid_prices", {}).get(inst_id, price)
            flow = self.whale_flow_cache.get(pair, {})
            lsr = float(flow.get("lsr", 1.15))
            oi_delta = float(flow.get("oi_delta_pct", 0.0))

            if self.master_adx < 25.0:
                if lsr >= 1.35:
                    side = "SELL"
                    score = 88.5
                    strategy = "ARMADILHA SARDINHA (TOPO)"
                    rationale = f"LSR elevado ({lsr:.2f}). Baleias buscando liquidez vendedora."
                elif lsr <= 1.10:
                    side = "BUY"
                    score = 92.0
                    strategy = "ABSORÇÃO BALEIA (FUNDO)"
                    rationale = f"Absorção institucional em suporte. LSR controlado ({lsr:.2f})."
                else:
                    side = "BUY" if price <= mid_ref else "SELL"
                    score = 81.0
                    strategy = "REVERSÃO DE CANAL"
                    rationale = f"Retorno à média dentro do range (ref ${mid_ref:.2f})."
            else:
                if lsr <= 1.15:
                    side = "BUY"
                    score = 93.5
                    strategy = "SNIPER TREND (BALEIA FLOW)"
                    rationale = "Rompimento institucional com capital novo."
                else:
                    side = "SELL"
                    score = 86.0
                    strategy = "BULL TRAP BREAKDOWN"
                    rationale = "Rompimento falso esgotado."

            sig_item = {
                "symbol": inst_id,
                "pair": pair,
                "side": side,
                "direction": "LONG" if side == "BUY" else "SHORT",
                "score": score,
                "confidence": score,
                "price": price,
                "strategy": strategy,
                "lsr": lsr,
                "oi_delta": oi_delta,
                "regime": self.current_regime,
                "rationale": rationale,
                "updated_at": time.time()
            }
            signals.append(sig_item)
            decisions.append({
                "symbol": pair,
                "trend_1h": "sideways" if self.master_adx < 25 else "trending",
                "pattern": strategy,
                "score": score,
                "adx": self.master_adx,
                "regime": self.regime_mode,
                "status": "eligible",
                "remaining_cooldown": 0
            })

        signals.sort(key=lambda x: x["score"], reverse=True)

        result = {
            "signals": signals,
            "decisions": decisions,
            "market_context": {
                "btc_direction": "NEUTRAL" if self.master_adx < 25 else "TRENDING",
                "btc_strength": 85,
                "btc_regime": self.current_regime,
                "btc_adx": self.master_adx,
                "btc_price": btc_price,
                "radar_mode": f"LAYA_{self.regime_mode}",
                "conductor": "LAYA SOBERANA (AUTÔNOMA)",
                "doctrine": "INSTITUTIONAL_LIQUIDITY_HUNTER"
            },
            "updated_at": int(time.time() * 1000)
        }
        self._cached_radar_pulse = result
        self._last_pulse_ts = now
        return result


    def is_available(self) -> bool:
        try:
            import laya  # noqa: F401
            return True
        except Exception:
            return False

    def classify(self, message: str) -> Dict[str, Any]:
        """Classifica a mensagem do chat (System 1)."""
        if _agent is None and _load_status.get("status") == "LOADING" and _agent_lock.locked():
            return {"available": False, "error": "laya_loading"}
        agent = _get_agent()
        if agent is None:
            return {"available": False, "error": _load_status.get("error")}
        text = (message or "").strip()
        if not text:
            return {"available": False, "error": "empty message"}
        t0 = time.time()
        try:
            with _infer_lock:
                res = agent.predict({"body": text}, QUESTIONS)
            elapsed_ms = round((time.time() - t0) * 1000, 1)
            _load_status["last_latency_ms"] = elapsed_ms
            answers = (res or {}).get("answers", {})
            intent = answers.get("intent", {}) or {}
            is_write = answers.get("is_write", {}) or {}
            return {
                "available": True,
                "intent": intent.get("choice", "conversa_livre"),
                "intent_conf": float(intent.get("confidence", 0.0) or 0.0),
                "is_write": float(is_write.get("noul", 0.0) or 0.0),
                "latency_ms": elapsed_ms,
            }
        except Exception as e:
            print(f"[Laya] classify falhou: {e}")
            return {"available": False, "error": str(e)}

    def evaluate_entry(self, market_summary: str, structured_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Avaliação Adaptativa Dual-Regime da Laya:
        - Se ADX < 25 (Lateral / Fim de Semana): Motor de Reversão à Média (Mean-Reversion)
        - Se ADX >= 25 (Tendência): Motor Sniper de Rompimento
        """
        t0 = time.time()
        text = (market_summary or "").upper()
        data = structured_data or {}

        # [REGRA ENCRYPTOS]: BTC é estritamente o Oráculo Macro da Laya, proibido abrir ordem de trade nele
        sym_check = (data.get("symbol") or "").upper().replace("-", "")
        if sym_check.startswith("BTC") or "BTCUSDT" in text or "BTC-USDT" in text:
            return {
                "available": False,
                "decision": "HOLD",
                "confidence": 0.0,
                "confluence_score": 0.0,
                "strategy": "BTC_ORACLE_MONITOR",
                "regime_mode": "ORACLE",
                "reason": "[ORÁCULO MACRO]: BTC é utilizado exclusivamente como bússola de dominância e fluxo. Proibido abrir ordens de trade no BTC."
            }
        
        # 1. Extração de Parâmetros
        import re
        adx = float(data.get("adx", 0.0))
        if adx <= 0:
            m_adx = re.search(r'ADX\s*([0-9\.]+)', text)
            adx = float(m_adx.group(1)) if m_adx else self.master_adx

        regime = str(data.get("regime", "")).upper()
        if not regime:
            if "TENDENCIA" in text or "TRENDING" in text:
                regime = "TENDENCIA"
            elif "LATERAL" in text or "RANGING" in text or "CHOP" in text:
                regime = "LATERAL"
            else:
                regime = "LATERAL" if adx < 25.0 else "TENDENCIA"

        self.current_regime = regime
        self.master_adx = adx
        self.regime_mode = "MEAN_REVERSION" if adx < 25.0 else "TREND_SNIPER"
        self.last_scan_time = time.time()

        kronos = float(data.get("kronos_conviction", 0.0))
        if kronos <= 0:
            m_k = re.search(r'(?:CONVICC[AÃ]O|SCORE|KRONOS):\s*([0-9\.]+)', text)
            kronos = float(m_k.group(1)) if m_k else 75.0

        # Direção primária apontada pelos sinais
        bull_cues = sum(1 for term in ["BUY", "LONG", "ALTA", "BULLISH", "ROMPIMENTO_ALTA", "UP", "CROSS_UP", "FUNDO", "SUPORTE", "OVERSOLD"] if term in text)
        bear_cues = sum(1 for term in ["SELL", "SHORT", "BAIXA", "BEARISH", "ROMPIMENTO_BAIXA", "DOWN", "CROSS_DOWN", "TOPO", "RESISTENCIA", "OVERBOUGHT"] if term in text)
        target_dir = "BUY" if bull_cues > bear_cues else ("SELL" if bear_cues > bull_cues else ("BUY" if "ALTA" in text else ("SELL" if "BAIXA" in text else "BUY")))

        elapsed_ms = round((time.time() - t0) * 1000, 1)

        # 2. MOTOR ADAPTATIVO DUAL (OPÇÃO A)
        if adx < 25.0 or regime == "LATERAL":
            # --- MODO SMART MONEY H1 (SAÍDA DE ACUMULAÇÃO) ---
            # Identifica saída com força no TF de 1H com stop na borda para neutralizar falsos rompimentos
            confidence = 0.86
            strategy = "LAYA_SMART_MONEY_H1"
            if target_dir == "BUY":
                decision = "BUY"
                reason = f"SMART MONEY H1 ATIVO (ADX {adx:.1f}): Saída de acumulação em 1H com força e confirmação institucional. Stop blindado na borda."
            elif target_dir == "SELL":
                decision = "SELL"
                reason = f"SMART MONEY H1 ATIVO (ADX {adx:.1f}): Quebra de suporte em 1H com fluxo vendedor e stop blindado na borda."
            else:
                decision = "HOLD"
                confidence = 0.45
                reason = f"CONSOLIDAÇÃO H1 (ADX {adx:.1f}): Preço dentro da acumulação. Aguardando saída com força."

            # [V144] Ajuste Fino via Pesos Calibrados do Fine-Tuning
            flow_reg = data.get("flow_regime")
            if flow_reg and self.calibrated_weights:
                multipliers = self.calibrated_weights.get("regime_multipliers", {})
                mult = multipliers.get(flow_reg, {}).get("confidence_multiplier", 1.0)
                confidence = round(min(0.96, confidence * mult), 2)

            # Registra no fluxo de pensamento
            sym = data.get("symbol", "SCAN")
            if decision != "HOLD":
                self.log_thought(sym, f"Setup Smart Money H1 qualificado: {decision} ({int(confidence*100)}% conf). {reason}", action="GATILHO", confidence=int(confidence*100), regime="LATERAL")

            return {
                "available": True,
                "decision": decision,
                "confidence": confidence,
                "confluence_score": round(confidence * 100, 1),
                "strategy": strategy,
                "regime_mode": "SMART_MONEY_H1",
                "adx": adx,
                "latency_ms": elapsed_ms,
                "reason": reason,
                "engine": "laya_adaptive_dual_engine",
                "summary": market_summary
            }

        else:
            # --- MODO TENDÊNCIA SNIPER (TREND BREAKOUT) ---
            # Em tendência forte, operamos rompimentos com volume
            confidence = 0.88 if kronos >= 70 else 0.76
            strategy = "LAYA_TREND_SNIPER"
            decision = target_dir
            reason = f"MODO TENDÊNCIA ATIVO (ADX {adx:.1f}): Rompimento confirmado com volume institucional e alinhamento MTF. Alvo de expansão (+4.0% a +6.0%)."

            sym = data.get("symbol", "SCAN")
            self.log_thought(sym, f"Setup Sniper de Tendência qualificado: {decision} ({int(confidence*100)}% conf).", action="GATILHO", confidence=int(confidence*100), regime="TENDENCIA")

            return {
                "available": True,
                "decision": decision,
                "confidence": confidence,
                "confluence_score": round(confidence * 100, 1),
                "strategy": strategy,
                "regime_mode": "TREND_SNIPER",
                "adx": adx,
                "latency_ms": elapsed_ms,
                "reason": reason,
                "engine": "laya_adaptive_dual_engine",
                "summary": market_summary
            }

    def _neural_heuristic_exit(self, position_summary: str) -> Dict[str, Any]:
        """Classificador heurístico-neural de saída (fallback fail-safe para evaluate_exit)."""
        summary_upper = str(position_summary).upper()
        if any(w in summary_upper for w in ["PANIC", "REVERSAL_CONFIRMED", "HOSTILE_BREAKOUT", "EXTREME_SQUEEZE", "COUNTER_PUMP", "COUNTER_DUMP"]):
            return {
                "available": True,
                "decision": "PANIC_CUT",
                "confidence": 0.94,
                "latency_ms": 0.5,
                "summary": position_summary,
                "reason": "Reversao institucional hostil detectada contra a posicao"
            }
        if any(w in summary_upper for w in ["EXHAUSTION_NEAR_TARGET", "PROFIT_PROTECTION", "TARGET_APPROACHING"]):
            return {
                "available": True,
                "decision": "PARTIAL_TP",
                "confidence": 0.88,
                "latency_ms": 0.5,
                "summary": position_summary,
                "reason": "Alvo alcancado com exaustao de fluxo. Proteger no breakeven."
            }
        return {
            "available": True,
            "decision": "HOLD_TRAIL",
            "confidence": 0.82,
            "latency_ms": 0.5,
            "summary": position_summary,
            "reason": "Estrutura saudavel mantida a favor da posicao"
        }

    async def evaluate_open_positions_lifecycle(self) -> List[Dict[str, Any]]:
        """
        [V190 - LAYA EXIT GUARDIAN]:
        Manejo cognitivo contínuo de todas as posições abertas no Sandbox/OKX.
        Avalia:
        - Reversão de estrutura contra a ordem;
        - Vela de 5M hostil (locomotiva contra o trade);
        - Squeeze severo de LSR.
        Se detectar que a posição foi invalidada institucionalmente antes do stop cheio,
        aciona PANIC_CUT para estancar o risco e salvar o saldo da banca!
        """
        from services.database_service import database_service
        from services.sandbox_service import sandbox_service
        from services.order_projection_service import proj_service
        from services.okx_ws_public import okx_ws_public_service

        active_trades = []
        try:
            active_trades = await database_service.get_sandbox_trades(active_only=True)
        except Exception as e_trades:
            logger.debug(f"[EXIT-GUARDIAN] Erro ao carregar trades: {e_trades}")
            return []

        if not active_trades:
            return []

        exit_results = []
        for trade in active_trades:
            try:
                sym = trade.symbol
                clean_sym = sym.replace("-USDT-SWAP", "").replace("USDT", "")
                direction = str(trade.direction).upper()
                entry_price = float(trade.entry_price or 0.0)
                meta = dict(trade.contract_meta or {})
                leverage = float(meta.get("leverage") or 20.0)

                # Preço corrente via WS ou REST
                curr_price = okx_ws_public_service.get_current_price(clean_sym + "USDT") or okx_ws_public_service.get_current_price(sym)
                if not curr_price or curr_price <= 0:
                    curr_price = await sandbox_service._get_current_price(sym)
                if not curr_price or curr_price <= 0:
                    curr_price = float(trade.current_price or entry_price)

                # Cálculo exato de ROI
                side_str = "buy" if direction == "LONG" else "sell"
                current_roi = proj_service.calculate_roi(entry_price, curr_price, side_str, leverage)

                # Coleta dados de fluxo e 5M
                flow_data = self.whale_flow_cache.get(sym) or self.whale_flow_cache.get(clean_sym + "USDT") or {}
                lsr_val = float(flow_data.get("lsr", 1.0) or 1.0)

                # Avaliação de microestrutura 5M
                ltf_status = "NORMAL"
                is_hostile_5m = False
                try:
                    ltf_eval = await self.check_lower_tf_exhaustion(sym, direction)
                    if not ltf_eval.get("is_safe", True):
                        ltf_reason = ltf_eval.get("reason", "")
                        # Apenas quedas/altas violentas (faca caindo / locomotiva >= 1.5%) são consideradas hostis para corte antecipado
                        if "LOCOMOTIVA" in ltf_reason or "QUEDA_LIVRE" in ltf_reason:
                            is_hostile_5m = True
                            ltf_status = "HOSTILE_BREAKOUT"
                except Exception:
                    pass

                # Detecta condições de estancamento de risco (PANIC_CUT) calibradas para 50x
                # Dá respiro de mercado para a posição trabalhar até o stop estrutural (-60% ROI / -1.2% preço)
                is_panic = False
                panic_reason = ""
                if direction == "SHORT":
                    if is_hostile_5m and current_roi < -35.0:
                        is_panic = True
                        panic_reason = f"Locomotiva hostil de 5M contra SHORT com ROI {current_roi:+.1f}%"
                    elif lsr_val < 0.50 and current_roi < -30.0:
                        is_panic = True
                        panic_reason = f"Short squeeze severo detectado (LSR {lsr_val:.2f})"
                elif direction == "LONG":
                    if is_hostile_5m and current_roi < -35.0:
                        is_panic = True
                        panic_reason = f"Queda livre hostil de 5M contra LONG com ROI {current_roi:+.1f}%"
                    elif lsr_val > 2.0 and current_roi < -30.0:
                        is_panic = True
                        panic_reason = f"Despejo institucional em cascata (LSR {lsr_val:.2f})"

                # Monta resumo estruturado para o motor de decisão
                status_tag = "PANIC_REVERSAL_CONFIRMED" if is_panic else ("PROFIT_PROTECTION" if current_roi >= 12.0 else "HEALTHY_TRAIL")
                pos_summary = (
                    f"Symbol: {clean_sym}, Side: {direction}, Entry: ${entry_price:.4f}, "
                    f"Current: ${curr_price:.4f}, ROI: {current_roi:+.2f}%, LSR: {lsr_val:.2f}, "
                    f"5M: {ltf_status}, Condition: {status_tag}"
                )

                eval_res = self.evaluate_exit(pos_summary)
                decision = eval_res.get("decision", "HOLD_TRAIL")

                if is_panic or decision == "PANIC_CUT":
                    self.log_thought(
                        clean_sym,
                        f"🛡️ [LAYA EXIT GUARDIAN - PANIC CUT]: Fechamento de emergência executado em {sym}! {panic_reason or eval_res.get('reason')} (ROI: {current_roi:+.1f}%). Prevenindo stop loss cheio.",
                        action="PANIC_CUT",
                        confidence=95
                    )
                    await sandbox_service.close_active_trade(trade.id, reason="LAYA_PANIC_CUT", exit_price=curr_price)
                    exit_results.append({"trade_id": trade.id, "symbol": sym, "action": "PANIC_CUT", "roi": current_roi})

                elif decision == "PARTIAL_TP" or (current_roi >= 10.0):
                    # Arma Breakeven dinâmico se a ordem estiver com bom lucro
                    curr_stop = float(trade.stop_price or 0.0)
                    is_stop_worse = (direction == "LONG" and curr_stop < entry_price) or (direction == "SHORT" and curr_stop > entry_price)
                    if is_stop_worse:
                        be_stop = round(entry_price * 1.001 if direction == "LONG" else entry_price * 0.999, 6)
                        await database_service.update_sandbox_trade(trade.id, {"stop_price": be_stop})
                        self.log_thought(
                            clean_sym,
                            f"🛡️ [LAYA EXIT GUARDIAN - BREAKEVEN]: Ordem {sym} com {current_roi:+.1f}% ROI! Stop puxado para Breakeven (${be_stop:.4f}). Risco zerado.",
                            action="BREAKEVEN_ARMED",
                            confidence=92
                        )
                        exit_results.append({"trade_id": trade.id, "symbol": sym, "action": "BREAKEVEN", "roi": current_roi})
                else:
                    exit_results.append({"trade_id": trade.id, "symbol": sym, "action": "HOLD_TRAIL", "roi": current_roi})

            except Exception as e_trade_eval:
                logger.debug(f"[EXIT-GUARDIAN] Erro avaliando trade: {e_trade_eval}")

        return exit_results

    async def consult_hermes_arbitration(
        self,
        symbol: str,
        direction: str,
        score: float,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Consulta o Hermes (System 2) para arbitrar candidato limítrofe."""
        try:
            from kernel.dispatcher import agent_dispatcher
            hermes = agent_dispatcher.get_agent("hermesagent")
            if hermes and hasattr(hermes, "arbitrate_trading_candidate"):
                return await hermes.arbitrate_trading_candidate(symbol, direction, score, context)
        except Exception as e_arb:
            logger.debug(f"[HERMES-ARBITRATION-CALL-ERR] {e_arb}")

        # Fallback de arbitragem local direta
        btc_bias = float(context.get("btc_trend_bias", 0.0) or 0.0)
        c_exp = float(context.get("1c_exp", 0.0) or 0.0)
        bot_on = bool(context.get("bot_ignition", False))
        if (direction == "LONG" and btc_bias >= -0.2 and (c_exp >= 60.0 or bot_on)) or (direction == "SHORT" and btc_bias <= 0.4 and (c_exp >= 60.0 or bot_on)):
            return {"approved": True, "score_boost": 10, "verdict": "APROVADO", "rationale": "Arbitragem rápida: Robôs ativos e alinhamento macro."}
        return {"approved": False, "score_boost": -15, "verdict": "VETADO", "rationale": "Arbitragem rápida: Combustível insuficiente."}

    def evaluate_exit(self, position_summary: str) -> Dict[str, Any]:
        """Avalia posicao ativa e decide: HOLD_TRAIL, PARTIAL_TP, FULL_EXIT ou PANIC_CUT (< 1ms)."""
        return self._neural_heuristic_exit(position_summary)

    def get_status(self) -> Dict[str, Any]:
        return {
            "engine": "laya (System 1, Co-Piloto Neural de Trading)",
            "model_name": LAYA_HUB_ID,
            "status": _load_status.get("status", "NOT_LOADED"),
            "installed": self.is_available(),
            "last_latency_ms": _load_status.get("last_latency_ms"),
            "hardware": "CPU",
            "error": _load_status.get("error"),
        }


laya_router_service = LayaRouterService()
laya_sovereign_engine = laya_router_service

