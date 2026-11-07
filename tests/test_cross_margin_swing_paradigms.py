import sys, os
sys.path.insert(0, os.path.abspath("backend"))
import pytest
from services.order_projection_service import ORDER_STOP_LADDER_SWING, proj_service
from app.services.laya_router_service import laya_router_service


def test_swing_ladder_50x_breathing_room():
    """
    Garante que o Degrau 1 do Swing 2H/4H em Margem Cruzada
    dispare apenas com +50% de ROI (~1.0% de movimento real a favor),
    concedendo 12h a 24h de respiro livre sem estrangulamento precoce.
    """
    degrau_1 = ORDER_STOP_LADDER_SWING[0]
    assert degrau_1.trigger_roi >= 50.0, f"Trigger ROI do degrau 1 deve ser >= 50.0 (atual: {degrau_1.trigger_roi})"
    assert degrau_1.stop_roi >= 5.0
    assert degrau_1.status_risco == "RISCO_ZERO"


def test_swing_ladder_50x_chao_300_percent():
    """
    Garante que a escadinha possua o alvo chão de +300% de ROI
    com stop travado em +200% de ROI (+$2.000,00 de lucro garantido na banca).
    """
    level_300 = next((l for l in ORDER_STOP_LADDER_SWING if l.trigger_roi == 300.0), None)
    assert level_300 is not None, "Escadinha deve conter nivel de trigger em 300% ROI"
    assert level_300.stop_roi >= 200.0, f"Stop em 300% deve garantir pelo menos 200% de ROI (atual: {level_300.stop_roi})"


def test_cross_margin_unprotected_risk_count_rule():
    """
    Garante a regra dos Lotes 4+4:
    Se ja existirem 4 ordens com risco vivo (sem breakeven),
    novas ordens sao bloqueadas ate que ao menos uma atinja Risco Zero.
    """
    trades_simulados = [
        {"symbol": "LINK-USDT-SWAP", "side": "Sell", "entry_price": 10.90, "current_stop": 11.05, "is_protected": False},
        {"symbol": "AVAX-USDT-SWAP", "side": "Sell", "entry_price": 8.40, "current_stop": 8.55, "is_protected": False},
        {"symbol": "SOL-USDT-SWAP", "side": "Sell", "entry_price": 95.0, "current_stop": 97.0, "is_protected": False},
        {"symbol": "XPL-USDT-SWAP", "side": "Sell", "entry_price": 0.058, "current_stop": 0.060, "is_protected": False},
    ]
    # Com 4 ordens em risco vivo, contagem deve ser 4
    count = laya_router_service.count_unprotected_risk_trades(trades_simulados)
    assert count == 4

    # Se uma for protegida no Breakeven (current_stop <= entry_price para SHORT)
    trades_simulados[0]["current_stop"] = 10.89
    trades_simulados[0]["is_protected"] = True
    count_pos = laya_router_service.count_unprotected_risk_trades(trades_simulados)
    assert count_pos == 3, "Quando uma ordem atinge breakeven, o risco vivo cai para 3, destravando vaga para o Lote 2"
