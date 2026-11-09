import sys, os
sys.path.insert(0, os.path.abspath("backend"))
import pytest
from app.services.laya_router_service import LayaRouterService


def test_count_unprotected_risk_trades():
    router = LayaRouterService()
    # 4 trades onde 2 estao desprotegidos e 2 estao em Breakeven (risco zero)
    trades = [
        # Trade 1: SHORT desprotegido (SL acima do preco de entrada)
        {"symbol": "SOL-USDT-SWAP", "direction": "SHORT", "side": "sell", "entry_price": 100.0, "current_stop": 101.5, "is_protected": False},
        # Trade 2: SHORT protegido no Breakeven (SL abaixo da entrada)
        {"symbol": "FIL-USDT-SWAP", "direction": "SHORT", "side": "sell", "entry_price": 1.0, "current_stop": 0.99, "is_protected": True},
        # Trade 3: SHORT desprotegido
        {"symbol": "UNI-USDT-SWAP", "direction": "SHORT", "side": "sell", "entry_price": 8.0, "current_stop": 8.1, "is_protected": False},
        # Trade 4: SHORT em Breakeven exato
        {"symbol": "XRP-USDT-SWAP", "direction": "SHORT", "side": "sell", "entry_price": 1.15, "current_stop": 1.15, "is_protected": False},
    ]

    unprotected = router.count_unprotected_risk_trades(trades)
    # Trade 1 e Trade 3 estao em risco (2 ordens em risco vivo)
    # Trade 2 e Trade 4 estao em Breakeven (risco zero)
    assert unprotected == 2, f"Esperava 2 ordens em risco vivo, obteve {unprotected}"


def test_snowball_allows_only_2_unprotected_risk_trades():
    """
    [V206-SNOWBALL-FLEET-2-PLUS-EXPANSION (Banca $10k)]
    Garante que a Laya permita no máximo 2 ordens simultâneas em risco vivo (Lote 1),
    preservando 80% do colateral garantidor na Margem Cruzada 50X.
    """
    router = LayaRouterService()
    # 2 shorts ja abertos em risco vivo
    active_trades = [
        {"symbol": "SOL-USDT-SWAP", "direction": "SHORT", "side": "sell", "entry_price": 100.0, "current_stop": 101.5, "is_protected": False},
        {"symbol": "FIL-USDT-SWAP", "direction": "SHORT", "side": "sell", "entry_price": 1.0, "current_stop": 1.02, "is_protected": False},
    ]
    unprot = router.count_unprotected_risk_trades(active_trades)
    assert unprot == 2
    # Risco vivo atingiu o teto de 2: novas entradas são vetadas até que uma atinja Breakeven
    assert unprot >= 2, "Com 2 ordens em risco vivo, novas entradas devem aguardar Breakeven"


def test_snowball_expands_to_8_with_6_at_risk_zero_and_2_in_risk():
    """
    Conforme ordens atingem Breakeven (+60% ROI), novas ordens abrem de 2 em 2
    até atingir o ápice de 8 ordens (6 em risco zero e 2 em risco vivo).
    """
    router = LayaRouterService()
    active_trades = [
        # 6 ordens protegidas em Breakeven / Trailing (+60% ROI alcançado)
        {"symbol": "SOL-USDT-SWAP", "direction": "SHORT", "side": "sell", "entry_price": 100.0, "current_stop": 98.8, "is_protected": True},
        {"symbol": "FIL-USDT-SWAP", "direction": "SHORT", "side": "sell", "entry_price": 1.0, "current_stop": 0.985, "is_protected": True},
        {"symbol": "UNI-USDT-SWAP", "direction": "SHORT", "side": "sell", "entry_price": 8.0, "current_stop": 7.9, "is_protected": True},
        {"symbol": "XPL-USDT-SWAP", "direction": "SHORT", "side": "sell", "entry_price": 0.05, "current_stop": 0.045, "is_protected": True},
        {"symbol": "NEAR-USDT-SWAP", "direction": "SHORT", "side": "sell", "entry_price": 3.6, "current_stop": 3.55, "is_protected": True},
        {"symbol": "ETH-USDT-SWAP", "direction": "SHORT", "side": "sell", "entry_price": 2230.0, "current_stop": 2200.0, "is_protected": True},
        # 2 ordens recém-abertas em risco vivo
        {"symbol": "ARB-USDT-SWAP", "direction": "SHORT", "side": "sell", "entry_price": 0.50, "current_stop": 0.51, "is_protected": False},
        {"symbol": "SUI-USDT-SWAP", "direction": "SHORT", "side": "sell", "entry_price": 2.0, "current_stop": 2.04, "is_protected": False},
    ]
    unprot = router.count_unprotected_risk_trades(active_trades)
    assert len(active_trades) == 8, "Frota atingiu o teto máximo de 8 ordens"
    assert unprot == 2, "Exatamente 2 ordens em risco vivo"
    assert (len(active_trades) - unprot) == 6, "Exatamente 6 ordens protegidas em risco zero"
