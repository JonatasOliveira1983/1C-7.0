# -*- coding: utf-8 -*-
"""
LAYA + KRONOS CONFLUENCE SERVICE (System 1 Flow + Foundation Time-Series)
========================================================================
Módulo de confluência entre o Radar de Fluxo Institucional da Laya (OKX Rubik)
e a Previsão Geométrica de Séries Temporais do Kronos (AAAI 2026).

Cruza a psicologia de mercado (Baleias vs Sardinhas) com a projeção probabilística
das próximas 12 velas para emitir:
1. Vetos anti-armadilha de varejo (Retail Trap / FOMO no topo).
2. Super-gatilhos de entrada institucional (Sniper Long/Short).
3. Calibração dinâmica de teto de alavancagem por dispersão de trajetórias.
4. Detecção de divergências temporais.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("LayaKronosConfluence")


class LayaKronosConfluenceService:
    def __init__(self):
        pass

    def evaluate_confluence(
        self,
        flow_radar: Dict[str, Any],
        kronos_result: Dict[str, Any],
        side: str = "BUY"
    ) -> Dict[str, Any]:
        """
        Avalia a confluência bidimensional entre fluxo de dinheiro (Laya) e tempo (Kronos).
        """
        side_norm = side.upper()
        if side_norm in ("BUY", "LONG"):
            side_norm = "BUY"
        else:
            side_norm = "SELL"

        lsr = float(flow_radar.get("lsr", 1.0) or 1.0)
        oi_delta = float(flow_radar.get("oi_delta_pct", 0.0) or 0.0)
        flow_regime = flow_radar.get("flow_regime", "NEUTRAL")
        whale_signal = flow_radar.get("whale_signal", "HOLD")

        kronos_conviction = float(kronos_result.get("conviction", 50.0) or 50.0)
        kronos_direction = str(kronos_result.get("prediction_direction", "NEUTRAL")).upper()
        paths_dispersion = float(kronos_result.get("paths_dispersion", 0.0) or 0.0)
        pred_change_pct = float(kronos_result.get("predicted_change_pct", 0.0) or 0.0)

        # Defaults
        is_vetoed = False
        veto_reason = None
        confluence_type = "NEUTRAL"
        score_boost = 0
        leverage_cap = 50.0
        rationale = "Sem confluência extrema ou veto. Operação prossegue em parâmetros padrão."

        # REGRA 1: Veto de Armadilha de Varejo (Retail Trap / Veto Buy)
        # Se o varejo está em euforia extrema compradora (LSR >= 1.35), o sinal de compra é vetado
        # mesmo que o Kronos aponte subida, pois o risco de despejo pelas baleias é agudo.
        if side_norm == "BUY" and (whale_signal == "VETO_BUY" or lsr >= 1.35 or flow_regime == "RETAIL_FOMO_INJECTION"):
            is_vetoed = True
            confluence_type = "RETAIL_TRAP_VETO"
            score_boost = -40
            leverage_cap = 10.0
            veto_reason = (
                f"VETO LAYA: Varejo em euforia extrema de compra (LSR {lsr:.2f}). "
                f"Risco crítico de despejo institucional (dump) apesar da projeção técnica."
            )
            rationale = veto_reason
            return {
                "is_vetoed": is_vetoed,
                "veto_reason": veto_reason,
                "confluence_type": confluence_type,
                "score_boost": score_boost,
                "leverage_cap": leverage_cap,
                "rationale": rationale,
                "lsr": lsr,
                "oi_delta_pct": oi_delta,
                "kronos_conviction": kronos_conviction,
                "kronos_direction": kronos_direction,
                "paths_dispersion": paths_dispersion
            }

        # REGRA 2: Super Confluência Sniper Long (Varredura de Stops + Inflexão Alta Kronos)
        # Baleias absorvendo a mínima (OI caindo ou LSR baixo) e Kronos projetando alta com convicção
        if side_norm == "BUY":
            is_whale_absorption = (
                flow_regime in ("LONG_LIQUIDATION_BOTTOM", "INSTITUTIONAL_ACCUMULATION")
                or (lsr <= 1.10 and (oi_delta > 0.3 or oi_delta < -0.3))
                or whale_signal in ("SNIPER_BUY_REVERSAL", "STRONG_BUY")
            )
            is_kronos_bullish = kronos_direction == "UP" and kronos_conviction >= 60.0

            if is_whale_absorption and is_kronos_bullish:
                confluence_type = "INSTITUTIONAL_SNIPER_LONG"
                score_boost = +15
                leverage_cap = 50.0 if paths_dispersion < 0.025 else 20.0
                rationale = (
                    f"CONFLUÊNCIA MÁXIMA INSTITUCIONAL (LONG): Baleias absorvendo liquidez no fundo "
                    f"(LSR {lsr:.2f}, Regime {flow_regime}) com Kronos confirmando inflexão altista "
                    f"({pred_change_pct:+.2f}%, convicção {kronos_conviction:.0f} pts)."
                )
                return {
                    "is_vetoed": False,
                    "veto_reason": None,
                    "confluence_type": confluence_type,
                    "score_boost": score_boost,
                    "leverage_cap": leverage_cap,
                    "rationale": rationale,
                    "lsr": lsr,
                    "oi_delta_pct": oi_delta,
                    "kronos_conviction": kronos_conviction,
                    "kronos_direction": kronos_direction,
                    "paths_dispersion": paths_dispersion
                }

        # REGRA 3: Super Confluência Sniper Short (Exaustão de Compradores + Queda Kronos)
        if side_norm == "SELL":
            is_whale_distribution = (
                flow_regime in ("SHORT_SQUEEZE_EXHAUSTION", "RETAIL_FOMO_INJECTION")
                or lsr >= 1.30
                or whale_signal in ("PREPARE_SHORT_REVERSAL", "VETO_BUY")
            )
            is_kronos_bearish = kronos_direction == "DOWN" and kronos_conviction >= 60.0

            if is_whale_distribution and is_kronos_bearish:
                confluence_type = "INSTITUTIONAL_SNIPER_SHORT"
                score_boost = +15
                leverage_cap = 50.0 if paths_dispersion < 0.025 else 20.0
                rationale = (
                    f"CONFLUÊNCIA MÁXIMA INSTITUCIONAL (SHORT): Sardinhas estopadas em topo "
                    f"(LSR {lsr:.2f}, Regime {flow_regime}) com Kronos confirmando quebra de suporte "
                    f"({pred_change_pct:+.2f}%, convicção {kronos_conviction:.0f} pts)."
                )
                return {
                    "is_vetoed": False,
                    "veto_reason": None,
                    "confluence_type": confluence_type,
                    "score_boost": score_boost,
                    "leverage_cap": leverage_cap,
                    "rationale": rationale,
                    "lsr": lsr,
                    "oi_delta_pct": oi_delta,
                    "kronos_conviction": kronos_conviction,
                    "kronos_direction": kronos_direction,
                    "paths_dispersion": paths_dispersion
                }

        # REGRA 4: Proteção por Dispersão Caótica de Trajetórias
        # Se as trajetórias do Kronos divergirem muito, há incerteza geométrica aguda.
        if paths_dispersion >= 0.035:
            confluence_type = "HIGH_DISPERSION_UNCERTAINTY"
            score_boost = -10
            leverage_cap = 20.0
            rationale = (
                f"INCERTEZA GEOMÉTRICA KRONOS: Dispersão entre trajetórias elevada ({paths_dispersion:.4f}). "
                f"Alavancagem capada em {leverage_cap:.0f}x para contenção de risco de wick."
            )
            return {
                "is_vetoed": False,
                "veto_reason": None,
                "confluence_type": confluence_type,
                "score_boost": score_boost,
                "leverage_cap": leverage_cap,
                "rationale": rationale,
                "lsr": lsr,
                "oi_delta_pct": oi_delta,
                "kronos_conviction": kronos_conviction,
                "kronos_direction": kronos_direction,
                "paths_dispersion": paths_dispersion
            }

        # REGRA 5: Divergência Direcional (Conflito entre Fluxo e Geometria)
        if side_norm == "BUY" and kronos_direction == "DOWN" and kronos_conviction >= 65.0:
            confluence_type = "TEMPORAL_DIVERGENCE"
            score_boost = -20
            leverage_cap = 20.0
            rationale = (
                f"DIVERGÊNCIA TEMPORAL: Sinal é BUY, mas Kronos projeta DOWN com alta convicção "
                f"({kronos_conviction:.0f} pts, {pred_change_pct:+.2f}%). Sinal enfraquecido."
            )
        elif side_norm == "SELL" and kronos_direction == "UP" and kronos_conviction >= 65.0:
            confluence_type = "TEMPORAL_DIVERGENCE"
            score_boost = -20
            leverage_cap = 20.0
            rationale = (
                f"DIVERGÊNCIA TEMPORAL: Sinal é SELL, mas Kronos projeta UP com alta convicção "
                f"({kronos_conviction:.0f} pts, {pred_change_pct:+.2f}%). Sinal enfraquecido."
            )

        return {
            "is_vetoed": is_vetoed,
            "veto_reason": veto_reason,
            "confluence_type": confluence_type,
            "score_boost": score_boost,
            "leverage_cap": leverage_cap,
            "rationale": rationale,
            "lsr": lsr,
            "oi_delta_pct": oi_delta,
            "kronos_conviction": kronos_conviction,
            "kronos_direction": kronos_direction,
            "paths_dispersion": paths_dispersion
        }


laya_kronos_confluence_service = LayaKronosConfluenceService()
