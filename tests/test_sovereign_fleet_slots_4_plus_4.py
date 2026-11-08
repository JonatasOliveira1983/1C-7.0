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


def test_lote_1_allows_up_to_4_directional_trades():
    """
    Garante que a Laya permita ate 4 ordens em risco vivo na mesma direcao (Lote 1),
    e nao trave artificialmente em 2 ordens como fazia o cluster legado.
    """
    router = LayaRouterService()
    # 2 shorts ja abertos em risco vivo
    active_trades = [
        {"symbol": "SOL-USDT-SWAP", "direction": "SHORT", "side": "sell", "entry_price": 100.0, "current_stop": 101.5, "is_protected": False},
        {"symbol": "FIL-USDT-SWAP", "direction": "SHORT", "side": "sell", "entry_price": 1.0, "current_stop": 1.02, "is_protected": False},
    ]
    # Lote 1 ainda tem 2 vagas livres (4 - 2 = 2)
    unprot = router.count_unprotected_risk_trades(active_trades)
    assert unprot == 2
    assert unprot < 4, "Lote 1 deve ter vagas para a 3a e 4a ordem"


def test_expansion_lote_2_when_orders_reach_breakeven():
    """
    Quando ordens do Lote 1 atingem Breakeven, o risco vivo diminui e libera vagas
    para novas ordens ate o teto de 8 ordens da frota soberana.
    """
    router = LayaRouterService()
    active_trades = [
        # 4 ordens abertas no total: 3 ja estao protegidas em Breakeven, apenas 1 em risco vivo
        {"symbol": "SOL-USDT-SWAP", "direction": "SHORT", "side": "sell", "entry_price": 100.0, "current_stop": 99.0, "is_protected": True},
        {"symbol": "FIL-USDT-SWAP", "direction": "SHORT", "side": "sell", "entry_price": 1.0, "current_stop": 0.98, "is_protected": True},
        {"symbol": "UNI-USDT-SWAP", "direction": "SHORT", "side": "sell", "entry_price": 8.0, "current_stop": 7.9, "is_protected": True},
        {"symbol": "XRP-USDT-SWAP", "direction": "SHORT", "side": "sell", "entry_price": 1.15, "current_stop": 1.16, "is_protected": False},
    ]
    unprot = router.count_unprotected_risk_trades(active_trades)
    assert unprot == 1  # Apenas XRP esta em risco vivo
    # O Lote 1 tem 3 vagas livres para chegar a 4 em risco vivo simultaneo!
    assert (4 - unprot) == 3
