# -*- coding: utf-8 -*-
"""
1CRYPTEN — Laya BTC Specialist & Market Climate Engine (V160)
============================================================
Módulo Soberano de Análise Macro do Bitcoin e Microestrutura Spot x Futuros:
1. Rastreamento em tempo real da Dominância do Bitcoin (BTC.D).
2. Lead-Lag entre mercado SPOT à vista (BTC-USDT) e perpétuos (BTC-USDT-SWAP).
3. Matriz Encryptos de Clima para Altcoins (Expansão, Sangria, Drenagem, Chop).
"""
import time
import asyncio
import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger("LayaBTCSpecialist")


class LayaBTCSpecialistService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LayaBTCSpecialistService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._dom_cache: float = 58.0
        self._dom_history = []  # [(timestamp, dominance)]
        self._last_dom_fetch: float = 0.0
        self._last_spot_vs_swap: Dict[str, Any] = {}
        self._last_spot_fetch: float = 0.0
        self._lock = asyncio.Lock()

    async def get_btc_dominance(self) -> Dict[str, Any]:
        """
        Obtém a dominância global do Bitcoin (BTC.D) com fallback e cache de 300s.
        Retorna o valor atual e a tendência (RISING, FALLING, STABLE).
        """
        now = time.time()
        if now - self._last_dom_fetch < 300 and self._dom_cache > 0:
            trend, delta = self._calc_dominance_trend()
            return {
                "dominance": self._dom_cache,
                "trend": trend,
                "delta_1h": delta,
                "cached": True
            }

        dom = None
        # Fonte 1: CoinGecko
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get("https://api.coingecko.com/api/v3/global")
                if res.status_code == 200:
                    data = res.json().get("data", {})
                    dom_val = data.get("market_cap_percentage", {}).get("btc", 0.0)
                    if dom_val and float(dom_val) > 20:
                        dom = float(dom_val)
        except Exception:
            pass

        # Fonte 2: CoinCap (Fallback)
        if not dom:
            try:
                async with httpx.AsyncClient(timeout=4.0) as client:
                    res = await client.get("https://api.coincap.io/v2/assets/bitcoin")
                    if res.status_code == 200:
                        b_data = res.json().get("data", {})
                        b_mcap = float(b_data.get("marketCapUsd", 0.0) or 0.0)
                        # Busca total mcap
                        res_g = await client.get("https://api.coincap.io/v2/assets?limit=20")
                        if res_g.status_code == 200:
                            top_mcap = sum(float(a.get("marketCapUsd", 0.0) or 0.0) for a in res_g.json().get("data", []))
                            if top_mcap > 0 and b_mcap > 0:
                                dom = round((b_mcap / top_mcap) * 100.0, 2)
            except Exception:
                pass

        # Se falhar todas as APIs externas, usa o valor anterior em cache ou 58.0%
        if not dom or dom <= 0:
            dom = self._dom_cache if self._dom_cache > 0 else 58.0

        self._dom_cache = round(dom, 2)
        self._last_dom_fetch = now
        self._dom_history.append((now, self._dom_cache))
        # Mantém histórico das últimas 24h
        cutoff = now - 86400
        self._dom_history = [(ts, v) for ts, v in self._dom_history if ts >= cutoff]

        trend, delta = self._calc_dominance_trend()
        return {
            "dominance": self._dom_cache,
            "trend": trend,
            "delta_1h": delta,
            "cached": False
        }

    def _calc_dominance_trend(self) -> tuple[str, float]:
        """Calcula a variação do BTC.D na última hora."""
        now = time.time()
        if len(self._dom_history) < 2:
            return "STABLE", 0.0
        
        # Pega valor de ~1 hora atrás ou o mais antigo disponível
        old_val = self._dom_history[0][1]
        for ts, v in self._dom_history:
            if now - ts <= 3600:
                old_val = v
                break
        
        delta = round(self._dom_cache - old_val, 2)
        if delta >= 0.15:
            trend = "RISING"
        elif delta <= -0.15:
            trend = "FALLING"
        else:
            trend = "STABLE"
        return trend, delta

    async def get_btc_spot_vs_futures(self) -> Dict[str, Any]:
        """
        [MICROESTRUTURA LEAD-LAG SPOT x FUTUROS]
        Compara o preço do BTC no mercado SPOT (BTC-USDT) com os FUTUROS (BTC-USDT-SWAP).
        Detecta se o Smart Money está acumulando no SPOT (conduzindo o mercado) ou se
        os futuros estão descolados em euforia alavancada (risco de flush).
        """
        now = time.time()
        if now - self._last_spot_fetch < 15 and self._last_spot_vs_swap:
            return self._last_spot_vs_swap

        spot_px = 0.0
        swap_px = 0.0
        try:
            async with httpx.AsyncClient(timeout=2.5) as client:
                res_spot = await client.get("https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT")
                if res_spot.status_code == 200:
                    d_s = res_spot.json().get("data", [{}])[0]
                    spot_px = float(d_s.get("last", 0.0) or 0.0)

                res_swap = await client.get("https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT-SWAP")
                if res_swap.status_code == 200:
                    d_sw = res_swap.json().get("data", [{}])[0]
                    swap_px = float(d_sw.get("last", 0.0) or 0.0)
        except Exception as _e_spr:
            logger.debug(f"[BTC-SPREAD] OKX indisponível para spread: {_e_spr}")

        # Fallback de alta disponibilidade: Binance Spot + Futures pública (sem rate limit)
        if spot_px <= 0 or swap_px <= 0:
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    r_s = await client.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
                    if r_s.status_code == 200:
                        spot_px = float(r_s.json().get("price", 0.0) or spot_px)
                    r_f = await client.get("https://fapi.binance.com/fapi/v1/ticker/price?symbol=BTCUSDT")
                    if r_f.status_code == 200:
                        swap_px = float(r_f.json().get("price", 0.0) or swap_px)
            except Exception:
                pass

        # Fallback de memória anterior
        if spot_px <= 0 or swap_px <= 0:
            prev = getattr(self, "_last_spot_vs_swap", {})
            if prev.get("spot_price", 0) > 0:
                spot_px = prev.get("spot_price", spot_px)
                swap_px = prev.get("swap_price", swap_px or spot_px)
            elif spot_px > 0 and swap_px <= 0:
                swap_px = spot_px
            elif swap_px > 0 and spot_px <= 0:
                spot_px = swap_px

        if spot_px <= 0:
            return getattr(self, "_last_spot_vs_swap", {
                "spot_price": spot_px,
                "swap_price": swap_px,
                "basis_spread_usd": 0.0,
                "basis_spread_pct": 0.0,
                "lead_lag_signal": "SPOT_FUTURES_PARITY"
            })

        spread_usd = round(swap_px - spot_px, 2)
        spread_pct = round((spread_usd / spot_px) * 100.0, 3)

        # Interpretação Institucional do Spread
        # Se Spot > Swap (Backwardation): Institucionais comprando ativo real no à vista. Bullish!
        # Se Swap >> Spot (+0.10% ou mais): Varejo eufórico alavancado em futuros. Risco de caça de stops.
        if spread_pct < -0.02:
            signal = "SPOT_ACCUMULATION_LEAD"  # Spot liderando alta
        elif spread_pct > 0.06:
            signal = "FUTURES_OVERLEVERAGED"   # Futuros sobrealavancados
        else:
            signal = "SPOT_FUTURES_PARITY"     # Paridade equilibrada

        self._last_spot_vs_swap = {
            "spot_price": spot_px,
            "swap_price": swap_px,
            "basis_spread_usd": spread_usd,
            "basis_spread_pct": spread_pct,
            "lead_lag_signal": signal,
            "updated_at": now
        }
        self._last_spot_fetch = now
        return self._last_spot_vs_swap

    def classify_altcoin_climate(
        self,
        btc_change_24h: float = 0.0,
        btc_trend_bias: float = 0.0,
        btc_dominance: float = 58.0,
        dominance_trend: str = "STABLE",
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        [MATRIZ ENCRYPTOS DE CLIMA PARA ALTCOINS]
        Determina a governança de permissão direcional para as Altcoins:
        - ALTCOIN_EXPANSION: BTC.D caindo + BTC estável/alta -> LIBERA COMPRAS AGRESSIVAS (LONG)
        - ALTCOIN_BLOODBATH: BTC.D subindo + BTC caindo -> VETO TOTAL DE COMPRAS; SÓ SHORT
        - BTC_DRAINAGE: BTC rali forte + BTC.D subindo -> Foco exclusivo em BTC/ETH
        - CONSOLIDATION_CHOP: Mercado sem tendência clara -> Caça de liquidez em bordas
        """
        if "btc_24h_change_pct" in kwargs:
            btc_change_24h = float(kwargs["btc_24h_change_pct"])
        if not btc_trend_bias:
            btc_trend_bias = btc_change_24h
        # 1. PÂNICO / SANGRIA: Bitcoin em queda ou sangria de mercado
        # [V169-FAROL-MACRO]: Se BTC estiver em queda (< -0.4% ou 24h < -1.0%), altcoins sangram dobrado.
        # Veto total e inegociável de ordens LONG em altcoins.
        if btc_trend_bias < -0.4 or btc_change_24h < -1.0 or (btc_dominance >= 58.0 and btc_trend_bias < 0.0):
            return {
                "climate": "ALTCOIN_BLOODBATH",
                "altcoin_long_allowed": False,
                "altcoin_short_allowed": True,
                "focus": "SHORTS_ONLY",
                "rationale": f"SANGRIA DE ALTCOINS: BTC em queda ({btc_trend_bias:+.1f}% / 24h: {btc_change_24h:+.1f}%) com Dominância em {btc_dominance:.1f}%. Veto absoluto em compras de altcoins."
            }

        # 2. EXPANSÃO / ALTSEASON: Bitcoin estável ou positivo e dominância caindo (Capital migrando para Altcoins)
        if btc_trend_bias >= -0.2 and (dominance_trend == "FALLING" or btc_dominance < 56.5):
            return {
                "climate": "ALTCOIN_EXPANSION",
                "altcoin_long_allowed": True,
                "altcoin_short_allowed": False,
                "focus": "HIGH_BETA_LONGS",
                "rationale": f"EXPANSÃO DE ALTCOINS: Dominância em queda ({btc_dominance:.1f}% {dominance_trend}) com BTC estável ({btc_trend_bias:+.1f}%). Compras liberadas com alavancagem calibrada. Proibido shortar altcoins em expansão."
            }

        # 3. DRENAGEM DE LIQUIDEZ: Bitcoin positivo (>= +0.3% ou trend bias positivo) com dominância elevada (>= 59.0%) ou em alta (RISING)
        # Quando o BTC sobe com dominância alta/crescente, ele atua como um buraco negro de liquidez:
        # shortar altcoins é suicídio técnico (rompimentos falsos de resistência para cima).
        if (btc_change_24h >= 0.3 or btc_trend_bias >= 0.3) and (dominance_trend == "RISING" or btc_dominance >= 59.0):
            return {
                "climate": "BTC_DRAINAGE",
                "altcoin_long_allowed": False,
                "altcoin_short_allowed": False,
                "focus": "BTC_ETH_ONLY",
                "rationale": f"DRENAGEM PELO BTC: Bitcoin em alta ({btc_change_24h:+.1f}%) com Dominância elevada ({btc_dominance:.1f}% {dominance_trend}). Proibido shortar altcoins sob sucção de liquidez."
            }

        # 4. CHOP LATERAL / CONSOLIDAÇÃO: Padrão neutro para reversões de liquidez
        # Veto assimétrico: se a Dominância estiver >= 58.0% e o BTC estiver em alta (> 0.2%), veta SHORT em altcoins
        short_allowed = btc_trend_bias <= 1.0
        if (btc_dominance >= 58.0 or dominance_trend == "RISING") and (btc_trend_bias > 0.2 or btc_change_24h > 0.2):
            short_allowed = False

        return {
            "climate": "CONSOLIDATION_CHOP",
            "altcoin_long_allowed": btc_trend_bias >= -0.3,
            "altcoin_short_allowed": short_allowed,
            "focus": "LIQUIDITY_EDGE_REVERSAL",
            "rationale": f"LATERALIDADE GERAL: BTC ({btc_trend_bias:+.1f}%) e Dominância ({btc_dominance:.1f}% {dominance_trend}) em consolidação. Operando caça de liquidez em bordas."
        }

    async def get_btc_macro_intelligence(
        self,
        btc_price: float = 0.0,
        btc_change_24h: float = 0.0,
        btc_trend_bias: float = 0.0,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Retorna o pacote completo de inteligência macro do Bitcoin para a Laya."""
        btc_price = float(kwargs.get("current_btc_price", btc_price) or btc_price)
        btc_change_24h = float(kwargs.get("btc_24h_change_pct", btc_change_24h) or btc_change_24h)
        btc_trend_bias = float(kwargs.get("btc_trend_bias", btc_trend_bias) or btc_trend_bias or btc_change_24h)

        dom_data = await self.get_btc_dominance()
        spot_data = await self.get_btc_spot_vs_futures()
        
        btc_dom = dom_data.get("dominance", 58.0)
        dom_trend = dom_data.get("trend", "STABLE")
        
        climate_data = self.classify_altcoin_climate(
            btc_change_24h=btc_change_24h,
            btc_trend_bias=btc_trend_bias,
            btc_dominance=btc_dom,
            dominance_trend=dom_trend
        )

        basis_pct = spot_data.get("basis_spread_pct", 0.0)

        return {
            "btc_price": btc_price or spot_data.get("swap_price", 0.0),
            "btc_change_24h": btc_change_24h,
            "btc_trend_bias": btc_trend_bias,
            "btc_dominance": btc_dom,
            "dominance_trend": dom_trend,
            "dominance_delta_1h": dom_data.get("delta_1h", 0.0),
            "spot_price": spot_data.get("spot_price", 0.0),
            "swap_price": spot_data.get("swap_price", 0.0),
            "basis_spread_usd": spot_data.get("basis_spread_usd", 0.0),
            "basis_spread_pct": basis_pct,
            "spot_vs_futures_spread_pct": basis_pct,
            "lead_lag_signal": spot_data.get("lead_lag_signal", "SPOT_FUTURES_PARITY"),
            "altcoin_climate": climate_data["climate"],
            "altcoin_long_allowed": climate_data["altcoin_long_allowed"],
            "altcoin_short_allowed": climate_data["altcoin_short_allowed"],
            "climate_rationale": climate_data["rationale"]
        }


laya_btc_specialist = LayaBTCSpecialistService()
