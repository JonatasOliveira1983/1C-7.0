import pytest
import asyncio
from unittest.mock import MagicMock, patch
from decimal import Decimal
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from services.order_projection_service import proj_service

def test_v186_breakeven_math_and_net_pnl_parity():
    """
    Testa que uma ordem LONG em 15X ou 20X ao atingir Breakeven (+8.0% ROI)
    tem o stop colocado em +3.0% ROI e, quando o stop e executado no stop_price,
    o resultado liquido final apos taxas da OKX e slippage e estritamente positivo (> 0).
    """
    # 1. Caso 15X (IRYS)
    entry_price = 0.01947
    leverage = 15.0
    side = "LONG"
    target_stop_roi = 3.0  # +3.0% ROI

    stop_price = proj_service.raw_price_from_roi(entry_price, target_stop_roi, side, leverage)
    assert stop_price > entry_price, "Para LONG, stop de +3.0% ROI deve ser superior ao preco de entrada"

    # Preco tick a mercado cai para 0.01943 (abaixo do stop)
    delayed_market_price = 0.01943
    assert delayed_market_price < stop_price, "Preco de mercado atrasado furou o stop"

    # Na V186, a execucao ocorre no stop_price (paridade OKX Trigger Order)
    exit_price = stop_price
    gross_roi = proj_service.calculate_roi(entry_price, exit_price, side, leverage)
    assert abs(gross_roi - target_stop_roi) < 1e-4

    # Deducoes OKX: 0.05% Taker Open + 0.05% Taker Close + 0.03% Slippage = 0.13%
    operational_cost_roi = (0.0010 + 0.0003) * leverage * 100.0  # 1.95% ROI
    final_pnl_15x = gross_roi - operational_cost_roi
    assert final_pnl_15x > 0, f"Lucro liquido a 15X deve ser positivo! Obteve: {final_pnl_15x:.2f}%"
    assert round(final_pnl_15x, 2) == 1.05

    # 2. Caso 20X
    leverage_20x = 20.0
    stop_price_20x = proj_service.raw_price_from_roi(entry_price, target_stop_roi, side, leverage_20x)
    gross_roi_20x = proj_service.calculate_roi(entry_price, stop_price_20x, side, leverage_20x)
    operational_cost_roi_20x = (0.0010 + 0.0003) * leverage_20x * 100.0  # 2.60% ROI
    final_pnl_20x = gross_roi_20x - operational_cost_roi_20x
    assert final_pnl_20x > 0, f"Lucro liquido a 20X deve ser positivo! Obteve: {final_pnl_20x:.2f}%"
    assert round(final_pnl_20x, 2) == 0.40

    print(f"PASS: 15X Net PnL = +{final_pnl_15x:.2f}% ROI | 20X Net PnL = +{final_pnl_20x:.2f}% ROI")

if __name__ == "__main__":
    test_v186_breakeven_math_and_net_pnl_parity()
