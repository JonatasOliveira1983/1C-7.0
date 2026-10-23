# -*- coding: utf-8 -*-
"""
1CRYPTEN — Market Intel Engine (1C-EXP, 1C-RANGE & AI-Ready Export)
===================================================================
Motor de inteligência de mercado em tempo real inspirado no eAssets.ai.
Consolida métricas proprietárias:
1. 1C-EXP: Índice de Expansão/Explosão Iminente (0 a 100).
2. 1C-RANGE: Nível percentual de posicionamento no canal H1 (0% a 100%).
3. AI Context Export: Serialização semântica pronta para LLMs e Agentes Autônomos.
"""

import time
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("1CryptenMarketIntelEngine")


class MarketIntelEngine:
    """Motor de cálculo e exportação de inteligência de mercado para humanos e IAs."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MarketIntelEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._last_snapshot: Dict[str, Any] = {}
        self._last_update_ts: float = 0.0

    def calculate_1c_range(self, current_price: float, support: float, resistance: float) -> float:
        """
        Calcula a posição percentual do preço dentro do canal H1:
        - 0.0% = no suporte
        - 100.0% = na resistência
        - 50.0% = centro
        - < 0% = rompimento baixista
        - > 100% = rompimento altista
        """
        span = resistance - support
        if span <= 0:
            return 50.0
        
        raw_pct = ((current_price - support) / span) * 100.0
        return round(raw_pct, 2)

    def calculate_1c_exp(
        self,
        bb_width_pct: float,
        vol_rel_5m: float,
        oi_delta_pct: float,
        adx: float = 20.0
    ) -> float:
        """
        Calcula o índice de explosão/expansão iminente 1C-EXP (0 a 100):
        - Compressão de volatilidade (bb_width_pct <= 6.5% gera pontuação alta)
        - Volume relativo crescente (vol_rel_5m >= 1.2x)
        - Fluxo de capital novo (oi_delta_pct > 0.5%)
        - Regime de pré-tendência (ADX saindo da consolidação)
        """
        score = 0.0

        # 1. Compressão de Bollinger (máx 45 pontos)
        if bb_width_pct <= 3.5:
            score += 45.0
        elif bb_width_pct <= 5.0:
            score += 35.0
        elif bb_width_pct <= 6.5:
            score += 25.0
        elif bb_width_pct <= 9.0:
            score += 15.0
        elif bb_width_pct <= 12.0:
            score += 5.0

        # 2. Volume Relativo de 5m (máx 30 pontos)
        if vol_rel_5m >= 2.0:
            score += 30.0
        elif vol_rel_5m >= 1.5:
            score += 25.0
        elif vol_rel_5m >= 1.2:
            score += 18.0
        elif vol_rel_5m >= 1.0:
            score += 10.0

        # 3. Open Interest Delta (máx 20 pontos)
        if oi_delta_pct >= 2.0:
            score += 20.0
        elif oi_delta_pct >= 1.0:
            score += 15.0
        elif oi_delta_pct >= 0.5:
            score += 10.0
        elif oi_delta_pct > 0.0:
            score += 5.0

        # 4. Fase de ignição por ADX (máx 5 pontos)
        if 15.0 <= adx <= 25.0:
            score += 5.0

        return min(100.0, max(0.0, round(score, 1)))

    def evaluate_single_asset_intel(
        self,
        symbol: str,
        last_price: float,
        open24h: float,
        high24h: float,
        low24h: float,
        vol24h: float,
        btc_climate: str = "ALTCOIN_EXPANSION"
    ) -> Dict[str, Any]:
        """
        Avalia as métricas de um único ativo, calculando 1C-EXP, 1C-RANGE e ignição de robôs.
        """
        change_24h = round(((last_price - open24h) / open24h * 100.0), 2) if open24h > 0 else 0.0

        # 1C-RANGE calculado sobre a faixa H1/24h
        range_level = self.calculate_1c_range(
            current_price=last_price,
            support=low24h,
            resistance=high24h
        )

        # Estimativa sintética de compressão de BB e aceleração de volume
        spread_span_pct = round(((high24h - low24h) / last_price * 100.0), 2) if last_price > 0 else 5.0
        bb_width_est = max(2.5, min(15.0, spread_span_pct * 0.45))
        vol_rel = 1.8 if vol24h > 40_000_000 else 1.3 if vol24h > 15_000_000 else 0.9
        oi_delta = 2.0 if change_24h > 1.5 else 0.8 if change_24h >= 0 else -0.5

        # 1C-EXP
        exp_score = self.calculate_1c_exp(
            bb_width_pct=bb_width_est,
            vol_rel_5m=vol_rel,
            oi_delta_pct=oi_delta,
            adx=22.0
        )

        # Detecção de Ignição de Robôs Institucionais
        bot_ignition = exp_score >= 70.0 and vol24h >= 1_000_000.0
        if exp_score >= 80.0:
            bot_status = "EXPANSÃO INSTITUCIONAL MÁXIMA"
        elif exp_score >= 70.0:
            bot_status = "IGNIÇÃO DE ROBÔS DETECTADA"
        elif exp_score >= 50.0:
            bot_status = "COMPRESSÃO PRÉ-ROMPE"
        else:
            bot_status = "FLUXO RESIDUAL/LATERAL"

        # Setup inferido
        if range_level <= 15.0:
            setup = "RANGE_FLOOR_REVERSAL"
            action = "LONG"
        elif range_level >= 85.0:
            setup = "RANGE_CEILING_REVERSAL"
            action = "SHORT" if "SHORT" not in btc_climate else "HOLD"
        elif exp_score >= 70.0:
            setup = "MOMENTO_MOLA_COMPRESSION"
            action = "LONG" if change_24h >= 0 else "SHORT"
        else:
            setup = "ACCUMULATION_CONSOLIDATION"
            action = "HOLD"

        return {
            "symbol": symbol,
            "pair": symbol.replace("-USDT-SWAP", ""),
            "price": last_price,
            "change_24h": change_24h,
            "high24h": high24h,
            "low24h": low24h,
            "vol_ccy_24h": vol24h,
            "1c_exp": exp_score,
            "1c_range": range_level,
            "lsr": 1.05,
            "funding_rate": 0.0001,
            "setup": setup,
            "action": action,
            "bot_ignition": bot_ignition,
            "bot_status": bot_status
        }

    def scan_universal_market(
        self,
        tickers_cache: Dict[str, Any],
        min_volume_usd: float = 500_000.0,
        exclude_btc: bool = True,
        btc_climate: str = "ALTCOIN_EXPANSION"
    ) -> List[Dict[str, Any]]:
        """
        [METODOLOGIA ENCRYPTOS — VARREDURA UNIVERSAL]
        Varre até 507 pares da OKX em tempo real, expurga pares zumbis (volume < min_volume_usd),
        calcula a aceleração e velocidade dos robôs e retorna os ativos ordenados por 1C-EXP.
        """
        active_assets = []

        for inst_id, t_data in tickers_cache.items():
            if not inst_id.endswith("-USDT-SWAP"):
                continue
            if exclude_btc and inst_id.startswith("BTC"):
                continue

            last_px = float(t_data.get("last", 0.0) or 0.0)
            if last_px <= 0:
                continue

            vol_usd = float(t_data.get("volume_24h_usd", t_data.get("volCcy24h", 0.0)) or 0.0)
            if vol_usd < min_volume_usd:
                continue  # Filtra zumbis e pó sem liquidez

            open_24 = float(t_data.get("open24h", last_px) or last_px)
            high_24 = float(t_data.get("high24h", last_px * 1.05) or (last_px * 1.05))
            low_24 = float(t_data.get("low24h", last_px * 0.95) or (last_px * 0.95))

            row = self.evaluate_single_asset_intel(
                symbol=inst_id,
                last_price=last_px,
                open24h=open_24,
                high24h=high_24,
                low24h=low_24,
                vol24h=vol_usd,
                btc_climate=btc_climate
            )
            active_assets.append(row)

        # Ordena prioritariamente por ignição de robôs (1C-EXP decrescente)
        active_assets.sort(key=lambda x: (x.get("1c_exp", 0.0), x.get("vol_ccy_24h", 0.0)), reverse=True)
        return active_assets

    def format_ai_market_context(
        self,
        btc_climate: str,
        btc_dominance: float,
        matrix_assets: List[Dict[str, Any]],
        top_limit: int = 5
    ) -> Dict[str, Any]:
        """
        Exporta o contexto de mercado em formato semântico normalizado pronto para IAs.
        """
        # Ordena os ativos mais explosivos por 1c_exp decrescente
        sorted_by_exp = sorted(matrix_assets, key=lambda x: x.get("1c_exp", 0.0), reverse=True)
        top_explosive = sorted_by_exp[:top_limit]

        # Gera resumo executivo para o prompt de agentes
        lines = [
            f"CLIMA MACRO: {btc_climate} | DOMINÂNCIA BTC: {btc_dominance:.1f}%",
            "TOP ATIVOS EM PONTO DE IGNIÇÃO:"
        ]
        for a in top_explosive:
            lines.append(
                f"- {a['symbol']}: EXP={a.get('1c_exp', 0)} | RANGE={a.get('1c_range', 0)}% | "
                f"LSR={a.get('lsr', 1.0):.2f} | SETUP={a.get('setup', 'NEUTRAL')} -> {a.get('action', 'HOLD')}"
            )

        summary_prompt = "\n".join(lines)

        return {
            "timestamp": time.time(),
            "macro_climate": {
                "regime": btc_climate,
                "btc_dominance": btc_dominance,
            },
            "total_assets_scanned": len(matrix_assets),
            "top_explosive_assets": top_explosive,
            "summary_prompt": summary_prompt,
            "instructions_for_ai": (
                "Dados em tempo real normalizados pelo 1Crypten Market Intel Engine. "
                "1C-EXP >= 75 indica compressão severa pronta para rompimento. "
                "1C-RANGE <= 15% representa piso de canal (compras assimétricas); >= 85% representa teto (vendas/exaustão)."
            )
        }


# Singleton export
market_intel_engine = MarketIntelEngine()
