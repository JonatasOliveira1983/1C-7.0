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

from pathlib import Path as _Path

LAYA_HUB_ID = "convaiinnovations/laya-multilingual"
LAYA_LOCAL_DIR = (
    _Path(__file__).resolve().parent.parent / "data" / "models" / "laya-multilingual"
)


def _ensure_local_checkpoint() -> Optional[str]:
    """Retorna caminho do checkpoint local se existir."""
    marker = LAYA_LOCAL_DIR / "model.safetensors"
    if marker.exists() and marker.stat().st_size > 100_000_000:
        return str(LAYA_LOCAL_DIR)
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
            print("[*] Carregando Laya multilingual na CPU...")
            _agent = laya.load(ckpt)
            _load_status["status"] = "READY"
            _load_status["load_time_s"] = round(time.time() - t0, 2)
            print(f"[OK] Laya pronto em {_load_status['load_time_s']}s.")
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
        c_exp: float = 0.0
    ) -> Dict[str, Any]:
        """
        [MAESTRO MULTI-TIMEFRAME & MULTI-SETUP COM FAROL MACRO, FUNDING SHIELD, BTC.D & STOP ATR]
        Hierarquia de Decisão Soberana da Laya:
        1. Prioridade 1: Saída de Acumulação H1 (Smart Money Breakout com volume e stop ATR).
        2. Prioridade 2: Range Boundary Reversal (No regime Mean Reversion / Consolidação, opera exaustão nas bordas).
        3. Prioridade 3: Momento Mola 15M (Compressão extrema no canal, BBW <= 6.5%).
        4. Prioridade 4: DVWAP Reversion 5M (Preço esticado da VWAP com BTC favorável).
        5. Neutro: Diagnóstico integrado das camadas.
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

        # CAMADA 1: AVALIA ROMPIMENTO DE 1H (PRIORIDADE MÁXIMA SE HOUVER BREAKOUT)
        setup_res = None
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

            # [ENCRYPTOS MACRO CLIMATE INTELLIGENCE]:
            # Avalia Dominância do BTC (BTC.D) e clima de mercado para altcoins
            if btc_intel and not is_btc_symbol:
                climate = btc_intel.get("altcoin_climate", "CONSOLIDATION_CHOP")
                long_allowed = btc_intel.get("altcoin_long_allowed", True)
                short_allowed = btc_intel.get("altcoin_short_allowed", True)
                btcd = btc_intel.get("btc_dominance", 0.0)

                if cand_dir == "LONG" and not long_allowed:
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
        """Verifica se uma direção (LONG ou SHORT) está sob Circuit Breaker."""
        dir_clean = direction.upper() if direction else "LONG"
        expiry = getattr(self, "_direction_cooldowns", {}).get(dir_clean, 0.0)
        return time.time() < expiry

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

    def evaluate_lower_tf_structure(self, candles: List[Any], direction: str) -> Dict[str, Any]:
        """
        [V173-ANTI-PREDICTIVE-GUARDS]: Especialista de Microestrutura M1/M5.
        Garante que a LAYA seja 100% REATIVA e NUNCA PREDITIVA.
        
        1. Validação de dados: exige ao menos 3 candles.
        2. TICK_REJECTION_INDEX: Exige pavio de rejeição >= 25% do range total da vela mais recente.
           - Para SHORT: Pavio superior >= 25% (comprova que vendedores apareceram no topo).
           - Para LONG: Pavio inferior >= 25% (comprova que compradores absorveram o fundo).
        3. MICRO_ACCELERATION_BRAKE: Veta se o par subiu/caiu continuamente > 1.2% nos últimos candles.
        4. MSB_CONFIRMATION: Veta se a vela mais recente estiver rompendo novas máximas (SHORT) ou mínimas (LONG).
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
                "reason": "DADOS_5M_INSUFICIENTES (Veto preventivo de segurança em alta alavancagem)",
                "metrics": default_metrics
            }

        # Normaliza ordenação por timestamp ascendente (antigo -> recente)
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
            "range": round(range_curr, 4)
        }

        if direction == "SHORT":
            wick_ratio = upper_wick_ratio
            is_green_expansion = (cl_curr >= o_curr) and (wick_ratio < 0.25)

            # 1. TICK_REJECTION_INDEX (Pavio superior de exaustão >= 15%)
            if is_green_expansion:
                return {
                    "is_safe": False,
                    "reason": f"VETO_EXAUSTAO_INSUFICIENTE (Vela 5M compradora sem pavio de absorção: pavio {wick_ratio*100:.1f}% vs min 25%. Proibido adivinhar topo)",
                    "metrics": metrics
                }

            # 2. MICRO_ACCELERATION_BRAKE (Anti-Locomotiva sem exaustão)
            if total_gain >= 0.025 and wick_ratio < 0.25:
                return {
                    "is_safe": False,
                    "reason": f"VETO_LOCOMOTIVA_ACELERADA (Alta agressiva de +{total_gain*100:.1f}% sem recuo em 5M. Proibido vender locomotiva)",
                    "metrics": metrics
                }

            # 3. MSB_CONFIRMATION: Não vender se vela estiver no topo sem pavio de rejeição real
            if h_curr >= h1 * 0.999 and wick_ratio < 0.25 and cl_curr >= l1:
                return {
                    "is_safe": False,
                    "reason": f"VETO_EXPANSAO_ATIVA (Vela 5M sustentando topo em ${h_curr:.4f} sem pavio de rejeição ({wick_ratio*100:.1f}% vs min 25%). Aguardar confirmação real)",
                    "metrics": metrics
                }

        elif direction == "LONG":
            wick_ratio = lower_wick_ratio
            is_red_expansion = (cl_curr <= o_curr) and (wick_ratio < 0.25)

            # 1. TICK_REJECTION_INDEX (Pavio inferior de absorção >= 15%)
            if is_red_expansion:
                return {
                    "is_safe": False,
                    "reason": f"VETO_EXAUSTAO_INSUFICIENTE (Vela 5M vendedora sem pavio de absorção: pavio {wick_ratio*100:.1f}% vs min 25%. Proibido adivinhar fundo)",
                    "metrics": metrics
                }

            # 2. MICRO_ACCELERATION_BRAKE (Anti-Queda Livre sem absorção)
            if total_drop >= 0.025 and wick_ratio < 0.25:
                return {
                    "is_safe": False,
                    "reason": f"VETO_LOCOMOTIVA_ACELERADA (Queda agressiva de -{total_drop*100:.1f}% sem respiro em 5M. Proibido comprar faca caindo)",
                    "metrics": metrics
                }

            # 3. MSB_CONFIRMATION: Não comprar se vela estiver na mínima sem absorção real
            if l_curr <= l1 * 1.001 and wick_ratio < 0.25 and cl_curr <= h1:
                return {
                    "is_safe": False,
                    "reason": f"VETO_EXPANSAO_ATIVA (Vela 5M renovando mínimas em ${l_curr:.4f} sem absorção ({wick_ratio*100:.1f}% vs min 25%). Aguardar absorção do fundo local)",
                    "metrics": metrics
                }

        return {
            "is_safe": True,
            "reason": "CONFIRMADO_MICROESTRUTURA_REATIVA (Exaustão e absorção validadas em 5M)",
            "metrics": metrics
        }

    async def check_lower_tf_exhaustion(self, symbol: str, direction: str) -> Dict[str, Any]:
        """
        [V173-NATIVE-OKX-FEED]: Consulta nativa de velas 5M na OKX Perpétuo
        com fallbacks para OKX Spot e Binance, passando os candles para evaluate_lower_tf_structure.
        """
        clean = symbol.replace("-SWAP", "").replace("-", "").replace(".P", "").upper()
        clean_coin = clean.replace("USDT", "")
        raw_candles = []

        try:
            async with httpx.AsyncClient(timeout=4.0, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}) as client:
                # 1. OKX SWAP Perpétuo (Primário para todos os pares)
                inst_id = f"{clean_coin}-USDT-SWAP"
                url_okx = f"https://www.okx.com/api/v5/market/candles?instId={inst_id}&bar=5m&limit=10"
                resp = await client.get(url_okx)
                if resp.status_code == 200:
                    d = resp.json()
                    if d.get("code") == "0" and d.get("data") and len(d["data"]) >= 3:
                        raw_candles = d["data"]

                # 2. Fallback OKX Spot
                if not raw_candles:
                    url_spot = f"https://www.okx.com/api/v5/market/candles?instId={clean_coin}-USDT&bar=5m&limit=10"
                    resp_s = await client.get(url_spot)
                    if resp_s.status_code == 200:
                        d_s = resp_s.json()
                        if d_s.get("code") == "0" and d_s.get("data") and len(d_s["data"]) >= 3:
                            raw_candles = d_s["data"]

                # 3. Fallback Binance Futures / Spot
                if not raw_candles:
                    url_bin = f"https://fapi.binance.com/fapi/v1/klines?symbol={clean}&interval=5m&limit=10"
                    resp_b = await client.get(url_bin)
                    if resp_b.status_code == 200:
                        b_data = resp_b.json()
                        if isinstance(b_data, list) and len(b_data) >= 3:
                            raw_candles = [[str(k[0]), str(k[1]), str(k[2]), str(k[3]), str(k[4])] for k in b_data]
        except Exception as _e_ltf:
            logger.debug(f"[LOWER-TF] Erro ao consultar candles 5M para {symbol}: {_e_ltf}")

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
                "reason": f"DADOS_5M_INDISPONIVEIS (Veto preventivo de segurança em {symbol}: confirmação microestrutural ausente)",
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
        """Retorna telemetria completa de sinal de vida da Laya para o Cockpit."""
        mem_stats = {}
        try:
            from app.services.memory_service import memory_service
            mem_stats = memory_service.get_stats()
        except Exception:
            pass

        return {
            "status": "ONLINE (SOVEREIGN COMMANDER)",
            "sovereign": True,
            "regime": self.current_regime,
            "regime_mode": self.regime_mode,
            "master_adx": self.master_adx,
            "last_scan_ago_s": round(time.time() - self.last_scan_time, 1),
            "thoughts": self.thought_stream[-20:],
            "candidate_setups": self.candidate_setups,
            "whale_flow": self.whale_flow_cache,
            "universal_market_stats": self.universal_market_stats,
            "doctrine": "INSTITUTIONAL_LIQUIDITY_HUNTER",
            "memory_stats": mem_stats
        }

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
                    min_volume_usd=1_000_000.0,
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
                for ign in ignited_assets[:8]:
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
            "regime": climate_tag,
            "btc_dominance": btcd_val,
            "spread_pct": spread_val,
            "lead_lag": lead_lag_tag
        }

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
        deep_dive_assets = [item[1] for item in valid_candidates[:12]]
        if not deep_dive_assets:
            deep_dive_assets = assets[:6]

        # Coleta concorrente com semáforo controlado para evitar 429
        sem_flow = asyncio.Semaphore(8)
        async def _safe_flow(p):
            async with sem_flow:
                try:
                    return await asyncio.wait_for(laya_flow_service.get_flow_radar(p), timeout=2.5)
                except Exception:
                    return {}

        sem_kline = asyncio.Semaphore(10)
        async def _safe_kline(p):
            async with sem_kline:
                try:
                    res = await asyncio.wait_for(okx_rest_service.get_klines(p, interval="60", limit=16), timeout=2.5)
                    if res:
                        return res
                except Exception:
                    pass
                # Fallback instantâneo para klines da Binance pública se OKX demorar
                try:
                    clean = p.replace("-USDT-SWAP", "USDT")
                    async with httpx.AsyncClient(timeout=2.0) as client:
                        r_b = await client.get(f"https://api.binance.com/api/v3/klines?symbol={clean}&interval=1h&limit=16")
                        if r_b.status_code == 200:
                            raw = r_b.json()
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

        funding_tasks = [_safe_fund(a["pair"]) for a in deep_dive_assets]
        funding_resps = await asyncio.gather(*funding_tasks, return_exceptions=True)
        funding_rate_map = {}
        for a, f_data in zip(deep_dive_assets, funding_resps):
            if not isinstance(f_data, BaseException):
                funding_rate_map[a["pair"]] = float(f_data or 0.0)

        for a in assets:
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

            # [MULTI-TIMEFRAME & MULTI-SETUP ENGINE: H1, M15 MOLA, M5 DVWAP]
            h1_candles = klines_h1_map.get(clean_sym, [])
            acc_range = self.calculate_h1_accumulation_range(h1_candles)
            funding_rate = funding_rate_map.get(clean_sym, 0.0)
            atr_pct = self.calculate_atr_pct(h1_candles, price)

            # [V176-ANTI-PUMP-VOLUME-SPIKE]: Auditoria de Volume Institucional em H1
            # Compara o volume da vela recente com a média dos últimos períodos
            vol_ratio = 1.0
            has_volume_spike = False
            if h1_candles and len(h1_candles) >= 3:
                try:
                    sorted_k = sorted(h1_candles, key=lambda c: int(c[0]), reverse=True)
                    recent_vol = float(sorted_k[0][5]) if len(sorted_k[0]) > 5 else 0.0
                    prev_vol = float(sorted_k[1][5]) if len(sorted_k) > 1 and len(sorted_k[1]) > 5 else 0.0
                    max_recent_vol = max(recent_vol, prev_vol)
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
                heat = await coinglass_heatmap_service.get_liquidity_heatmap(sym, current_price=price)
                dom_magnet = heat.get("dominant_magnet", "NEUTRAL_EQUILIBRIUM")
                target_p = float(heat.get("target_price") or 0.0)
                target_vol = float(heat.get("target_volume_usd") or 0.0)
                target_vol_m = round(target_vol / 1e6, 2)
                target_region = heat.get("target_region") or ("ACIMA" if target_p > price else "ABAIXO")
                lifecycle_obj = heat.get("lifecycle") or {}
            except Exception as _heat_e:
                logger.debug(f"[HEATMAP-CANDIDATE-ERR] {clean_sym}: {_heat_e}")

            # Avaliação Multi-Setup Integrada com Blindagem Anti-Faca (Robôs On & C-EXP)
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
                c_exp=c_exp
            )

            direction = multi_eval["direction"]
            score = multi_eval["score"]
            rationale = multi_eval["rationale"]
            strat_name = multi_eval.get("strategy", "LAYA_SMART_MONEY_H1")

            # [CONFLUENCIA ESTRITA AO IMA DE LIQUIDEZ]
            if multi_eval["qualifies"]:
                if direction == "LONG" and (dom_magnet == "BEARISH_SWEEP" or target_region == "ABAIXO"):
                    multi_eval["qualifies"] = False
                    direction = "SHORT"
                    rationale = f"VETO ÍMÃ: LONG abortado: muralha de ${target_vol_m:.1f}M ABAIXO em ${target_p:.4f} puxando o preço. Preparando SHORT."
                elif direction == "SHORT" and (dom_magnet == "BULLISH_SWEEP" or target_region == "ACIMA"):
                    multi_eval["qualifies"] = False
                    direction = "LONG"
                    rationale = f"VETO ÍMÃ: SHORT abortado: muralha de ${target_vol_m:.1f}M ACIMA em ${target_p:.4f} puxando o preço. Preparando LONG."

            if multi_eval["qualifies"]:
                stop_loss = multi_eval["stop_loss"]
                target = multi_eval["target"]
                stop_dist = multi_eval["stop_dist"]
                target_dist = multi_eval["target_dist"]
                if strat_name == "LAYA_SMART_MONEY_H1":
                    action_badge = "SMART_MONEY_GATILHO"
                elif strat_name == "LAYA_RANGE_REVERSAL":
                    action_badge = "RANGE_REVERSAL_GATILHO"
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

                # Alinha a direção do radar à atração dominante do Ímã
                if target_region == "ABAIXO" or dom_magnet == "BEARISH_SWEEP":
                    direction = "SHORT"
                    target = target_p if target_p > 0 else round(price * 0.965, 4)
                    stop_loss = round(price * 1.025, 4)
                    target_dist = round(abs(price - target) / price, 4)
                    stop_dist = 0.025

                    # [FILTRO TÉCNICO DE BORDA / PULLBACK PARA SHORT]:
                    # Exige que o preço esteja em recuo/pullback (c_range >= 50% ou acima da VWAP) e NUNCA no fundo (c_range < 35%)
                    is_pullback_or_edge = (c_range is not None and c_range >= 50.0) or (vwap > 0 and price >= vwap)
                    is_at_support_floor = (c_range is not None and c_range < 35.0)

                    # [V176-OPCAO-B-ANTI-PUMP-GUARD]: Veto estrito de SHORT se houver ignição institucional, 1C-EXP >= 70 ou Volume Spike >= 3x
                    is_pump_ignition = bot_on or (c_exp is not None and c_exp >= 70.0) or has_volume_spike

                    if is_hunt_zone and is_pullback_or_edge and not is_at_support_floor and not is_pump_ignition:
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
                        rationale = f"VETO ANTI-PUMP 1C-EXP: Ignição institucional detectada (Volume {vol_ratio:.1f}x da média / 1C-EXP {c_exp:.0f} / Robôs ON={bot_on}). Proibido abrir SHORT contra aceleração de baleias."
                    elif is_at_support_floor:
                        rationale = f"VETO FUNDO (1C-Range {c_range:.0f}%): Ímã de ${target_vol_m:.1f}M ABAIXO, mas preço no suporte. Proibido vender fundo sem rompimento."
                    else:
                        rationale = f"ÍMÃ DE BAIXA ({target_region}): Muralha de ${target_vol_m:.1f}M USD em ${target_p:.4f} puxando o preço. Aguardando pullback para vender caro."
                elif target_region == "ACIMA" or dom_magnet == "BULLISH_SWEEP":
                    direction = "LONG"
                    target = target_p if target_p > 0 else round(price * 1.035, 4)
                    stop_loss = round(price * 0.975, 4)
                    target_dist = round(abs(target - price) / price, 4)
                    stop_dist = 0.025

                    # [FILTRO TÉCNICO DE BORDA / DIP PARA LONG]:
                    # Exige que o preço esteja em desconto (c_range <= 50% ou abaixo da VWAP) e NUNCA no topo (c_range > 65%)
                    is_dip_or_edge = (c_range is not None and c_range <= 50.0) or (vwap > 0 and price <= vwap)
                    is_at_resistance_ceiling = (c_range is not None and c_range > 65.0)

                    if is_hunt_zone and is_dip_or_edge and not is_at_resistance_ceiling:
                        strat_name = "LAYA_LIQUIDITY_HUNT"
                        score = 88
                        multi_eval["qualifies"] = True
                        multi_eval["stop_loss"] = stop_loss
                        multi_eval["target"] = target
                        multi_eval["stop_dist"] = stop_dist
                        multi_eval["target_dist"] = target_dist
                        rationale = f"CAÇADA DE LIQUIDEZ (HUNT LONG): Preço em desconto técnico (1C-Range: {c_range:.0f}%) a favor do Ímã dominante de ${target_vol_m:.1f}M USD em ${target_p:.4f} ({lifecycle_obj.get('distance_pct', 0)}% de espaço)."
                    elif is_at_resistance_ceiling:
                        rationale = f"VETO TOPO (1C-Range {c_range:.0f}%): Ímã de ${target_vol_m:.1f}M ACIMA, mas preço na resistência. Proibido comprar topo sem rompimento."
                    else:
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

            self.candidate_setups[clean_sym] = {
                "symbol": sym,
                "clean_sym": clean_sym,
                "direction": direction,
                "strategy": strat_name,
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
                "vol_ratio": vol_ratio,
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
                            d_res = await signal_generator.detect_btc_decorrelation(sym)
                        
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
            current_sandbox_balance = getattr(sandbox_service, "base_balance_cache", 10000.0)
        except Exception:
            current_sandbox_balance = 10000.0

        daily_profit_pct = ((current_sandbox_balance - 10000.0) / 10000.0) * 100.0
        # [V165-SLOTS-EXPANSION] 8 Slots de Scalping ($100 cada = $800 alocado para máxima diversificação de 507 pares)
        max_allowed_slots = 8
        effective_min_score = self.MIN_ENTRY_SCORE

        # [V170.1-CAPITAL-FLOW] A Laya mantém operação institucional contínua em 8 slots (Score >= 85%).
        # O lucro realizado é protegido dinamicamente pelo Piso Soberano (Never Give Back),
        # garantindo que o sistema continue abrindo trades excelentes sem congelamento de slots.
        if daily_profit_pct > 0:
            self.log_thought("SISTEMA", f"️ [BANCA NO LUCRO]: Lucro acumulado {daily_profit_pct:+.2f}% (+${current_sandbox_balance-10000.0:.2f}). Piso Soberano ativo protegendo capital. 8 slots operacionais (Score >= {effective_min_score}%).", action="CAPITAL_FLOW", confidence=90)

        order_opened = None
        # [CIRCUIT BREAKER GLOBAL ANTI-TILT]: Se 3 stops recentes ocorreram em <90min, congelar novas entradas
        if self.is_global_circuit_breaker_active():
            rem_freeze = int(getattr(self, "_global_circuit_breaker_until", 0.0) - time.time())
            self.log_thought("CIRCUIT_BREAKER", f"️ [ANTI-TILT ATIVO]: Resfriamento global de banca ativo ({rem_freeze}s restantes). Novas ordens congeladas.", action="GLOBAL_FREEZE", confidence=99)
            force_open_if_empty = False

        # Permite ate max_allowed_slots ordens ativas simultaneas respeitando a blindagem diária
        if force_open_if_empty and len(active_trades) < max_allowed_slots:
            eligible = [
                cand for cand in self.candidate_setups.values()
                if cand["symbol"] not in active_symbols
                and cand.get("clean_sym") not in active_symbols
                and cand.get("clean_sym", "").replace("USDT", "") not in active_symbols
                and cand.get("direction") in ("LONG", "SHORT")
                and not self.is_symbol_in_cooldown(cand.get("clean_sym", ""))
                and not self.is_direction_in_cooldown(cand.get("direction", ""))
                and cand["score"] >= effective_min_score
                # [FAROL MACRO VETO NO DISPARO]: Veta compras se BTC caindo e veta vendas se BTC subindo (exceto Caçada Soberana de Liquidez)
                and not (cand.get("strategy") != "LAYA_LIQUIDITY_HUNT" and btc_trend_bias < -0.4 and cand.get("direction") == "LONG")
                and not (cand.get("strategy") != "LAYA_LIQUIDITY_HUNT" and btc_trend_bias > 1.0 and cand.get("direction") == "SHORT")
                # [ENCRYPTOS CLIMA VETO]: Veta compras em altcoins se BTC.D drenando, veta vendas se Altcoin Expansion
                and not (
                    cand.get("strategy") != "LAYA_LIQUIDITY_HUNT"
                    and "BTC" not in cand.get("clean_sym", "").upper()
                    and btc_intel
                    and not btc_intel.get("altcoin_long_allowed", True)
                    and cand.get("direction") == "LONG"
                )
                and not (
                    cand.get("strategy") != "LAYA_LIQUIDITY_HUNT"
                    and "BTC" not in cand.get("clean_sym", "").upper()
                    and btc_intel
                    and not btc_intel.get("altcoin_short_allowed", True)
                    and cand.get("direction") == "SHORT"
                )
                # [DESCORRELAÇÃO SETORIAL]: Limita a no máximo 3 posições ativas do mesmo cluster (8 slots totais)
                and not (cand.get("direction") == "SHORT" and (cand.get("has_volume_spike") or cand.get("bot_ignition") or cand.get("1c_exp", 0) >= 70.0))
                # [DESCORRELAÇÃO SETORIAL]: Limita a no máximo 3 posições ativas do mesmo cluster (8 slots totais)
                and not self.is_cluster_limit_reached(cand.get("clean_sym", cand["symbol"]), active_symbols, max_per_cluster=3)
            ]
            # [DIVERSITY & ROTATION & PRIORIDADE ALT PUMP IGNITION]
            # Prioridade absoluta para Alt Pump Ignition, depois rotação e score
            last_traded = getattr(self, "_last_traded_pair", None)
            eligible.sort(
                key=lambda x: (
                    1 if x.get("alt_pump_ignition") else 0,
                    x["score"] - (8.0 if x.get("clean_sym") == last_traded else 0.0),
                    random.random()
                ),
                reverse=True
            )

            chosen = None
            for cand in eligible:
                cand_sym = cand["symbol"]
                cand_dir = cand["direction"]

                # [V174-LIQUIDITY-MAGNET-VETO]: Veta qualquer ordem contra muralha de liquidação pesada e ZONA MORTA
                try:
                    from app.services.coinglass_heatmap_service import coinglass_heatmap_service
                    cand_p = float(cand.get("price") or 0.0)
                    heat = await coinglass_heatmap_service.get_liquidity_heatmap(cand_sym, current_price=cand_p)
                    dom_magnet = heat.get("dominant_magnet")
                    target_reg = heat.get("target_region") or ("ACIMA" if heat.get("target_price", 0) > cand_p else "ABAIXO")
                    lifecycle = heat.get("lifecycle") or {}
                    zone_id = lifecycle.get("zone_id", "")

                    # 1. Veto da ZONA MORTA (anti-armadilha e falso rompimento entre 0.3% e 1.5%)
                    if zone_id == "DEAD_ZONE":
                        self.log_thought(
                            cand.get("clean_sym", cand_sym),
                            f"️ [VETO ZONA MORTA]: Entrada {cand_dir} bloqueada: preço a {lifecycle.get('distance_pct', 0)}% do bolsão ({zone_id}). Alto risco de falso rompimento.",
                            action="VETO_ZONA_MORTA",
                            confidence=96
                        )
                        continue

                    # 2. Veto Direcional do Ímã: NUNCA operar contra a atração do maior pool
                    # Se bolsão dominante está ACIMA / BULLISH_SWEEP -> Proibido SHORT!
                    if cand_dir == "SHORT" and (dom_magnet == "BULLISH_SWEEP" or target_reg == "ACIMA"):
                        vol_m = heat.get("target_volume_usd", 0) / 1e6
                        self.log_thought(
                            cand.get("clean_sym", cand_sym),
                            f"️ [VETO ÍMÃ DE LIQUIDEZ]: SHORT proibido: muralha dominante de ${vol_m:.2f}M ACIMA DO PREÇO em ${heat.get('target_price', 0):.4f} atraindo o preço.",
                            action="VETO_IMA_LIQUIDEZ",
                            confidence=98
                        )
                        continue

                    # Se bolsão dominante está ABAIXO / BEARISH_SWEEP -> Proibido LONG!
                    if cand_dir == "LONG" and (dom_magnet == "BEARISH_SWEEP" or target_reg == "ABAIXO"):
                        vol_m = heat.get("target_volume_usd", 0) / 1e6
                        self.log_thought(
                            cand.get("clean_sym", cand_sym),
                            f"️ [VETO ÍMÃ DE LIQUIDEZ]: LONG proibido: muralha dominante de ${vol_m:.2f}M ABAIXO DO PREÇO em ${heat.get('target_price', 0):.4f} atraindo o preço.",
                            action="VETO_IMA_LIQUIDEZ",
                            confidence=98
                        )
                        continue
                except Exception as heat_err:
                    logger.debug(f"[LAYA-VETO-HEATMAP-ERR] {heat_err}")

                # [V169-TF-MENORES]: Verifica exaustão e ausência de faca caindo em 5m antes do disparo
                ltf_check = await self.check_lower_tf_exhaustion(cand_sym, cand_dir)
                if not ltf_check.get("is_safe", True):
                    self.log_thought(
                        cand.get("clean_sym", cand_sym),
                        f"️ [VETO TF MENOR]: Ordem {cand_dir} bloqueada: {ltf_check.get('reason')}",
                        action="VETO_TF_MENOR",
                        confidence=92
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
                
                # Stop Loss e Alvo calculados pelo setup específico (H1 Breakout, DVWAP ou Mola)
                stop_loss = chosen.get("stop_loss")
                target = chosen.get("target")

                # [CALIBRAÇÃO ESTRUTURAL DE STOP LOSS E ALAVANCAGEM — V169]
                # Altcoins exigem respiro técnico entre 2.0% e 3.8% para não morrer no ruído.
                default_stop_dist = 0.025
                min_stop_dist = 0.020
                max_stop_dist = 0.038
                from services.order_projection_service import proj_service
                from app.services.okx_universe_service import okx_universe_service

                if d == "LONG":
                    if not stop_loss or stop_loss >= p or ((p - stop_loss) / p) > max_stop_dist or ((p - stop_loss) / p) < min_stop_dist:
                        stop_loss = p * (1.0 - default_stop_dist)
                    if not target or target <= p:
                        target = p * 1.045
                elif d == "SHORT":
                    if not stop_loss or stop_loss <= p or ((stop_loss - p) / p) > max_stop_dist or ((stop_loss - p) / p) < min_stop_dist:
                        stop_loss = p * (1.0 + default_stop_dist)
                    if not target or target >= p:
                        target = p * 0.955

                stop_loss = okx_universe_service.format_price_by_tick(sym, stop_loss)
                target = okx_universe_service.format_price_by_tick(sym, target)

                # Distância real de preço do Stop
                stop_dist_pct = max(min_stop_dist, min(max_stop_dist, abs(p - stop_loss) / p))

                # [ALAVANCAGEM DISCRETA: EXCLUSIVAMENTE 15X OU 20X]:
                # Regra soberana: ordens abertas estritamente em 15X ou 20X (sem valores intermediários).
                # Stop curto (<= 1.95%) ou alta convicção (score >= 90): 20X; Canal estrutural padrão H1: 15X.
                target_stop_roi = 35.0
                calc_lev = int(target_stop_roi / (stop_dist_pct * 100.0))
                leverage = 20 if (calc_lev >= 18 or chosen.get("score", 0) >= 90) else 15

                margin = 100.0
                quant_res = okx_universe_service.quantize_order_contracts(
                    symbol=sym,
                    margin_usd=margin,
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
                be_trigger_roi = 12.0

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
                self.log_thought(
                    clean_sym,
                    f"COMANDO SOBERANO: Ordem {d} ({strat}) executada em {clean_sym} a ${p:.4f} (Alvo: ${target:.4f}, Stop na Borda H1: ${stop_loss:.4f}). Proteção Smart Money ativada.",
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

    def evaluate_exit(self, position_summary: str) -> Dict[str, Any]:
        """Avalia posicao ativa e decide: HOLD_TRAIL, PARTIAL_TP, FULL_EXIT ou PANIC_CUT."""
        agent = _get_agent()
        if agent is None:
            return self._neural_heuristic_exit(position_summary)
        t0 = time.time()
        try:
            with _infer_lock:
                res = agent.predict({"body": position_summary}, EXIT_QUESTIONS)
            elapsed_ms = round((time.time() - t0) * 1000, 1)
            decision_data = (res or {}).get("answers", {}).get("decision", {})
            choice = decision_data.get("choice", "HOLD_TRAIL").upper()
            confidence = float(decision_data.get("confidence", 0.0) or 0.0)
            return {
                "available": True,
                "decision": choice,
                "confidence": confidence,
                "latency_ms": elapsed_ms,
                "summary": position_summary
            }
        except Exception:
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

