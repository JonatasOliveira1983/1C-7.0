# -*- coding: utf-8 -*-
"""
1CRYPTEN 7.0 — Testes de Invariante de Alavancagem Obrigatória (15X a 20X)
Verifica que ordens abertas pela Laya Soberana respeitam rigorosamente a faixa:
15 <= leverage <= 20, e NUNCA abrem abaixo de 15X.
"""
import pytest
from app.services.okx_universe_service import okx_universe_service


def calculate_adaptive_leverage(stop_dist_pct: float, target_stop_roi: float = 35.0) -> int:
    """Função idêntica à implementada em laya_router_service.py."""
    calc_lev = int(target_stop_roi / (stop_dist_pct * 100.0))
    return max(15, min(20, calc_lev))


class TestLeverageBandInvariant:

    @pytest.mark.parametrize("stop_dist_pct, expected_leverage", [
        (0.010, 20),   # 1.0% de stop -> calc_lev = 35 -> limitado ao teto de 20x
        (0.015, 20),   # 1.5% de stop -> calc_lev = 23 -> limitado ao teto de 20x
        (0.018, 19),   # 1.8% de stop -> calc_lev = 19 -> 19x
        (0.020, 17),   # 2.0% de stop -> calc_lev = 17 -> 17x
        (0.023, 15),   # 2.3% de stop -> calc_lev = 15 -> 15x
        (0.028, 15),   # 2.8% de stop -> calc_lev = 12 -> forçado ao piso de 15x
        (0.031, 15),   # 3.1% de stop (caso AVAX) -> calc_lev = 11 -> forçado ao piso de 15x
        (0.035, 15),   # 3.5% de stop (caso RENDER) -> calc_lev = 10 -> forçado ao piso de 15x
        (0.050, 15),   # 5.0% de stop extremo -> calc_lev = 7 -> forçado ao piso de 15x
        (0.100, 15),   # 10.0% de stop anômalo -> calc_lev = 3 -> forçado ao piso de 15x
    ])
    def test_leverage_always_between_15_and_20(self, stop_dist_pct, expected_leverage):
        """Garante que qualquer distância de stop resulta em alavancagem entre 15 e 20."""
        lev = calculate_adaptive_leverage(stop_dist_pct)
        assert lev == expected_leverage
        assert 15 <= lev <= 20
        assert lev >= 15, f"Alavancagem {lev} violou a regra inegociável de nunca ser menor que 15X!"
        assert lev <= 20, f"Alavancagem {lev} violou o teto de 20X!"

    @pytest.mark.parametrize("symbol, price, margin", [
        ("AVAX-USDT-SWAP", 18.80, 100.0),
        ("RENDER-USDT-SWAP", 3.78, 100.0),
        ("DOGE-USDT-SWAP", 0.145, 100.0),
        ("SOL-USDT-SWAP", 145.0, 100.0),
        ("LINK-USDT-SWAP", 11.20, 100.0),
    ])
    def test_quantize_contracts_valid_at_15x_and_20x(self, symbol, price, margin):
        """Valida que a quantização OKX SWAP funciona perfeitamente em 15X e 20X."""
        for lev in [15, 17, 20]:
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

        assert "leverage = max(15, min(20, calc_lev))" in code, (
            "A trava estrita 'max(15, min(20, calc_lev))' deve estar presente no código de laya_router_service.py!"
        )
        assert "leverage = max(5, min(15, calc_lev))" not in code, (
            "O limitador legado 'max(5, min(15, calc_lev))' ainda está presente e deve ser removido!"
        )
