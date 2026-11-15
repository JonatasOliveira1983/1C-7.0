# -*- coding: utf-8 -*-
"""
[DEPRECATED V216 PURGE] SandboxScalpingEngine
=============================================
Este motor legado de scalping M1/M5 (VWAP SNIPER) foi permanentemente
descontinuado na versão V216.

A arquitetura do 1Crypten opera exclusivamente sob o TITAN ENGINE soberano
com a estratégia LAYA_PULLBACK_HUNTER_2H_30M em Margem Cruzada 50X.
"""

from typing import Dict, Any, List

_LEVERAGE           = 50.0
_MARGIN_PER_TRADE   = 200.0
_SCAN_INTERVAL      = 30
_MAX_SLOTS          = 5
_MIN_SCORE          = 60
_MAX_STOP_ROI       = -12.0
_VWAP_TOLERANCE_PCT = 0.65
_STOCH_OVERSOLD     = 25.0
_STOCH_OVERBOUGHT   = 75.0
_EMA_PERIOD         = 200
_MIN_ATR_PCT        = 0.02


def _calculate_stoch_rsi(closes: List[float], rsi_period: int = 14,
                          stoch_period: int = 14, k_smooth: int = 3,
                          d_smooth: int = 3) -> Dict[str, float]:
    """Stub utilitário para compatibilidade com testes legados."""
    return {"k": 50.0, "d": 50.0, "prev_k": 50.0, "prev_d": 50.0}


class SandboxScalpingEngine:
    """Stub inerte do motor legado para manter compatibilidade e evitar execuções paralelas."""
    def __init__(self):
        self._last_scan = {
            "status": "decommissioned",
            "version": "V216",
            "message": "Scalping Engine descontinuado em prol do Titan Engine 2H/30M."
        }
        self.is_running = False

    async def start(self):
        pass

    async def stop(self):
        pass

    async def _try_open_trade(self, *args, **kwargs):
        # r_r_ratio >= 1.5
        return None


sandbox_scalping_engine = SandboxScalpingEngine()
