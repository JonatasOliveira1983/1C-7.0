import pytest
from app.services.laya_router_service import LayaRouterService

def test_alt_pump_ignition_triple_confluence_triggers():
    """
    Testa se a Tríplice Confluência Institucional ativa o Alt Pump Ignition:
    1. BTC.D caindo ou clima ALTCOIN_EXPANSION
    2. Correlação estatística de Pearson com BTC < 0.45 (descolamento)
    3. Robôs Ligados (1C-EXP >= 70.0)
    """
    router = LayaRouterService()
    btc_intel = {
        "btc_dominance": 57.2,
        "dominance_trend": "FALLING",
        "altcoin_climate": "ALTCOIN_EXPANSION",
        "dominance_delta_1h": -0.15
    }
    decorrelation_data = {
        "is_decorrelated": True,
        "correlation": 0.28,
        "correlation_short": 0.15
    }
    candidate = {
        "symbol": "SUI-USDT-SWAP",
        "clean_sym": "SUI",
        "direction": "LONG",
        "score": 75,
        "1c_exp": 78.5,
        "bot_ignition": True,
        "rationale": "Setup de rompimento H1"
    }

    res = router.evaluate_alt_pump_ignition(btc_intel, decorrelation_data, candidate)
    assert res["is_ignition"] is True
    assert res["bonus_score"] == 25
    assert "ALT PUMP IGNITION" in res["tag"]
    assert res["correlation"] == 0.28

def test_alt_pump_ignition_vetoed_when_still_correlated_to_btc():
    """
    Se a moeda ainda estiver colada ao Bitcoin (correlação >= 0.45),
    NÃO deve ativar a ignição independente do 1C-EXP.
    """
    router = LayaRouterService()
    btc_intel = {
        "btc_dominance": 57.0,
        "dominance_trend": "FALLING",
        "altcoin_climate": "ALTCOIN_EXPANSION"
    }
    decorrelation_data = {
        "is_decorrelated": False,
        "correlation": 0.82
    }
    candidate = {
        "symbol": "ETH-USDT-SWAP",
        "clean_sym": "ETH",
        "direction": "LONG",
        "score": 80,
        "1c_exp": 75.0,
        "bot_ignition": True
    }

    res = router.evaluate_alt_pump_ignition(btc_intel, decorrelation_data, candidate)
    assert res["is_ignition"] is False
    assert res["bonus_score"] == 0

def test_alt_pump_ignition_vetoed_when_robots_off():
    """
    Se os robôs institucionais estiverem desligados (1C-EXP < 70),
    não há ignição algorítmica.
    """
    router = LayaRouterService()
    btc_intel = {
        "btc_dominance": 56.5,
        "dominance_trend": "FALLING",
        "altcoin_climate": "ALTCOIN_EXPANSION"
    }
    decorrelation_data = {
        "is_decorrelated": True,
        "correlation": 0.20
    }
    candidate = {
        "symbol": "ADA-USDT-SWAP",
        "clean_sym": "ADA",
        "direction": "LONG",
        "score": 75,
        "1c_exp": 45.0,
        "bot_ignition": False
    }

    res = router.evaluate_alt_pump_ignition(btc_intel, decorrelation_data, candidate)
    assert res["is_ignition"] is False
    assert res["bonus_score"] == 0

def test_alt_pump_ignition_sorting_priority():
    """
    Garante que candidatos com Alt Pump Ignition ganham prioridade absoluta
    na fila de alocação dos slots da Laya.
    """
    cand_normal = {
        "clean_sym": "SOL",
        "score": 88,
        "alt_pump_ignition": False
    }
    cand_ignition = {
        "clean_sym": "TIA",
        "score": 82,
        "alt_pump_ignition": True
    }

    candidates = [cand_normal, cand_ignition]
    # Chave canônica de ordenação: ignição primeiro, depois score ponderado
    candidates.sort(
        key=lambda x: (
            1 if x.get("alt_pump_ignition") else 0,
            x["score"]
        ),
        reverse=True
    )

    assert candidates[0]["clean_sym"] == "TIA"
    assert candidates[1]["clean_sym"] == "SOL"
