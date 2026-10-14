"""
LAYA ORDER FLOW & WHALE INTELLIGENCE SERVICE (System 1 - Flow Radar)
===================================================================
Módulo de inteligência de fluxo institucional e caça de liquidez:
- Coleta métricas de Open Interest (OI) e Long/Short Ratio (LSR) da OKX Rubik.
- Mapeia o descompasso entre Baleias (Institucionais) e Sardinhas (Varejo).
- Identifica armadilhas de liquidez: Short Squeeze, Long Liquidation e Varreduras (Sweeps).
"""

import time
import asyncio
import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger("LayaFlowService")

class LayaFlowService:
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 45.0  # 45 segundos para respeitar rate limits e garantir frescor
        self._lock = asyncio.Lock()

    async def get_flow_radar(self, symbol_or_pair: str) -> Dict[str, Any]:
        """
        Retorna o diagnóstico de fluxo institucional e sentimento das sardinhas para um ativo.
        Aceita formatos: 'SOL', 'SOLUSDT', 'SOL-USDT-SWAP'.
        """
        clean_ccy = symbol_or_pair.replace("-USDT-SWAP", "").replace("USDT", "").upper()
        inst_id = f"{clean_ccy}-USDT-SWAP"
        now = time.time()

        # Verifica cache
        cached = self._cache.get(clean_ccy)
        if cached and (now - cached.get("ts", 0)) < self._cache_ttl:
            return cached.get("data", {})

        async with self._lock:
            # Dupla checagem após adquirir lock
            cached = self._cache.get(clean_ccy)
            if cached and (now - cached.get("ts", 0)) < self._cache_ttl:
                return cached.get("data", {})

            radar = await self._fetch_and_calculate_metrics(clean_ccy, inst_id)
            self._cache[clean_ccy] = {
                "ts": now,
                "data": radar
            }
            return radar

    async def _fetch_and_calculate_metrics(self, ccy: str, inst_id: str) -> Dict[str, Any]:
        """Executa consultas concorrentes à OKX e extrai deltas de fluxo."""
        now = time.time()
        lsr_url = f"https://www.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio?ccy={ccy}&period=5m"
        oi_url = f"https://www.okx.com/api/v5/rubik/stat/contracts/open-interest-volume?ccy={ccy}&period=5m"
        funding_url = f"https://www.okx.com/api/v5/public/funding-rate?instId={inst_id}"

        lsr_val = 1.0
        lsr_prev = 1.0
        oi_val_usd = 0.0
        oi_prev_usd = 0.0
        funding_rate = 0.0

        async with httpx.AsyncClient(timeout=4.0) as client:
            tasks = [
                client.get(lsr_url),
                client.get(oi_url),
                client.get(funding_url)
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # 1. Processar Long/Short Ratio (LSR)
            resp_lsr = responses[0]
            if not isinstance(resp_lsr, BaseException) and resp_lsr.status_code == 200:
                try:
                    d = resp_lsr.json().get("data", [])
                    if len(d) >= 1:
                        lsr_val = float(d[0][1])
                    if len(d) >= 4:  # Comparar com 15-20 min atrás
                        lsr_prev = float(d[3][1])
                    elif len(d) >= 2:
                        lsr_prev = float(d[1][1])
                except Exception as e:
                    logger.debug(f"Erro ao parsear LSR para {ccy}: {e}")

            # 2. Processar Open Interest Volume
            resp_oi = responses[1]
            if not isinstance(resp_oi, BaseException) and resp_oi.status_code == 200:
                try:
                    d = resp_oi.json().get("data", [])
                    if len(d) >= 1:
                        oi_val_usd = float(d[0][1])
                    if len(d) >= 4:  # Comparar com 15-20 min atrás
                        oi_prev_usd = float(d[3][1])
                    elif len(d) >= 2:
                        oi_prev_usd = float(d[1][1])
                except Exception as e:
                    logger.debug(f"Erro ao parsear OI para {ccy}: {e}")

            # 3. Processar Funding Rate
            resp_fr = responses[2]
            if not isinstance(resp_fr, BaseException) and resp_fr.status_code == 200:
                try:
                    d = resp_fr.json().get("data", [])
                    if len(d) >= 1:
                        funding_rate = float(d[0].get("fundingRate", 0.0))
                except Exception as e:
                    logger.debug(f"Erro ao parsear Funding para {ccy}: {e}")

        # Calcular Deltas
        lsr_delta_pct = round(((lsr_val - lsr_prev) / lsr_prev) * 100.0, 2) if lsr_prev > 0 else 0.0
        oi_delta_pct = round(((oi_val_usd - oi_prev_usd) / oi_prev_usd) * 100.0, 2) if oi_prev_usd > 0 else 0.0

        # Classificação de Sentimento do Varejo (Sardinhas)
        if lsr_val >= 1.40:
            lsr_bias = "RETAIL_EXTREME_LONG"
            sardinha_status = "Sardinhas eufóricas em Long (Risco iminente de liquidação)"
        elif lsr_val >= 1.15:
            lsr_bias = "RETAIL_LONG"
            sardinha_status = "Maioria do varejo comprada"
        elif lsr_val <= 0.75:
            lsr_bias = "RETAIL_EXTREME_SHORT"
            sardinha_status = "Sardinhas desesperadas em Short (Combustível para Squeeze)"
        elif lsr_val <= 0.88:
            lsr_bias = "RETAIL_SHORT"
            sardinha_status = "Maioria do varejo vendida"
        else:
            lsr_bias = "BALANCED"
            sardinha_status = "Equilíbrio de posicionamento do varejo"

        # Diagnóstico de Regime de Fluxo Institucional (Baleias)
        flow_regime = "NEUTRAL"
        whale_signal = "HOLD"
        whale_rationale = ""
        veto_reason = None

        if oi_delta_pct > 0.4:
            if lsr_val <= 1.10:
                flow_regime = "INSTITUTIONAL_ACCUMULATION"
                whale_signal = "STRONG_BUY"
                whale_rationale = f"Baleias injetando capital novo (+{oi_delta_pct}% OI) sem euforia de sardinhas (LSR {lsr_val:.2f}). Tendência genuína."
            elif lsr_val >= 1.35:
                flow_regime = "RETAIL_FOMO_INJECTION"
                whale_signal = "VETO_BUY"
                veto_reason = f"Veto de Long: Varejo acumulando posições agressivas (LSR {lsr_val:.2f}) - risco de despejo pelas baleias."
                whale_rationale = veto_reason
        elif oi_delta_pct < -0.3:
            if lsr_delta_pct < -2.0 or lsr_val < 1.0:
                flow_regime = "LONG_LIQUIDATION_BOTTOM"
                whale_signal = "SNIPER_BUY_REVERSAL"
                whale_rationale = f"Varredura de stops concluída (OI caiu {oi_delta_pct}%). Sardinhas estopadas em Long. Baleias absorvendo a mínima."
            elif lsr_delta_pct > 2.0 or lsr_val > 1.3:
                flow_regime = "SHORT_SQUEEZE_EXHAUSTION"
                whale_signal = "PREPARE_SHORT_REVERSAL"
                whale_rationale = f"OI caiu {oi_delta_pct}% com exaustão de compradores. Sardinhas estopadas em short; baleias desovando no topo."
        else:
            flow_regime = "CONSOLIDATION_ABSORPTION"
            whale_signal = "RANGE_REVERSAL"
            whale_rationale = f"OI estável ({oi_delta_pct}%). Mercado em absorção passiva de liquidez nos extremos do canal."

        return {
            "ccy": ccy,
            "inst_id": inst_id,
            "lsr": round(lsr_val, 2),
            "lsr_prev": round(lsr_prev, 2),
            "lsr_delta_pct": lsr_delta_pct,
            "lsr_bias": lsr_bias,
            "sardinha_status": sardinha_status,
            "oi_usd": round(oi_val_usd, 2),
            "oi_delta_pct": oi_delta_pct,
            "funding_rate": funding_rate,
            "funding_pct": round(funding_rate * 100.0, 4),
            "flow_regime": flow_regime,
            "whale_signal": whale_signal,
            "whale_rationale": whale_rationale,
            "veto_reason": veto_reason,
            "ts": now
        }

laya_flow_service = LayaFlowService()
