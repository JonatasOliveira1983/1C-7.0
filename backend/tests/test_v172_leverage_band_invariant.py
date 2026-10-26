# -*- coding: utf-8 -*-
"""
1CRYPTEN 7.0 — Testes de Invariante de Alavancagem Discreta (Exclusivamente 15X ou 20X)
Verifica que ordens abertas pela Laya Soberana são estritamente 15X ou 20X (sem valores intermediários).
"""
import pytest
from app.services.okx_universe_service import okx_universe_service


def calculate_discrete_leverage(stop_dist_pct: float, score: int = 85, target_stop_roi: float = 35.0) -> int:
    """Função idêntica à implementada em laya_router_service.py (V172-DISCRETE)."""
    calc_lev = int(target_stop_roi / (stop_dist_pct * 100.0))
    return 20 if (calc_lev >= 18 or score >= 90) else 15


class TestLeverageBandInvariant:

    @pytest.mark.parametrize("stop_dist_pct, score, expected_leverage", [
        (0.010, 85, 20),   # 1.0% stop -> calc_lev = 35 (>= 18) -> 20X
        (0.015, 85, 20),   # 1.5% stop -> calc_lev = 23 (>= 18) -> 20X
        (0.018, 85, 20),   # 1.8% stop -> calc_lev = 19 (>= 18) -> 20X
        (0.019, 85, 20),   # 1.9% stop -> calc_lev = 18 (>= 18) -> 20X
        (0.020, 85, 15),   # 2.0% stop -> calc_lev = 17 (< 18) e score 85 -> 15X
        (0.020, 92, 20),   # 2.0% stop mas score 92 (alta convicção >= 90) -> 20X
        (0.025, 85, 15),   # 2.5% stop -> 15X
        (0.031, 85, 15),   # 3.1% stop (caso AVAX) -> 15X
        (0.035, 85, 15),   # 3.5% stop (caso RENDER) -> 15X
        (0.050, 85, 15),   # 5.0% stop extremo -> 15X
    ])
    def test_leverage_strictly_15_or_20(self, stop_dist_pct, score, expected_leverage):
        """Garante que a alavancagem é EXCLUSIVAMENTE 15X ou 20X (nunca outro valor)."""
        lev = calculate_discrete_leverage(stop_dist_pct, score=score)
        assert lev == expected_leverage
        assert lev in (15, 20), f"Alavancagem {lev} não é 15X nem 20X!"

    @pytest.mark.parametrize("symbol, price, margin", [
        ("AVAX-USDT-SWAP", 18.80, 100.0),
        ("RENDER-USDT-SWAP", 3.78, 100.0),
        ("DOGE-USDT-SWAP", 0.145, 100.0),
        ("SOL-USDT-SWAP", 145.0, 100.0),
        ("LINK-USDT-SWAP", 11.20, 100.0),
    ])
    def test_quantize_contracts_valid_at_15x_and_20x(self, symbol, price, margin):
        """Valida que a quantização OKX SWAP funciona perfeitamente em 15X e 20X."""
        for lev in (15, 20):
            quant = okx_universe_service.quantize_order_contracts(
                symbol=symbol,
                margin_usd=margin,
                leverage=lev,
                price=price
            )
            assert quant.get("is_valid") is True, f"Quantização falhou para {symbol} em {lev}X: {quant}"
            assert quant.get("contracts", 0) > 0
            assert quant.get("notional_usd", 0) >= margin * (lev * 0.8)

    def test_laya_router_codebase_invariant(self):
        """Inspeciona diretamente o código-fonte de laya_router_service.py para garantir integridade."""
        with open("backend/app/services/laya_router_service.py", "r", encoding="utf-8") as f:
            code = f.read()

        assert 'leverage = 20 if (calc_lev >= 18 or chosen.get("score", 0) >= 90) else 15' in code, (
            "A trava discreta 'leverage = 20 if (calc_lev >= 18 or chosen.get(\"score\", 0) >= 90) else 15' deve estar presente no código de laya_router_service.py!"
        )
