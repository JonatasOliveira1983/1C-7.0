# -*- coding: utf-8 -*-
"""
1CRYPTEN 7.0 — TESTES TDD DO AGENTE PLUTUS (VIVER DE RENDA / MÉTODO ARCA)
Verifica a integridade matemática da alocação ARCA, a orquestração do Hermes
e os limites de risco/retorno para a meta de renda passiva.
"""
import sys
import os
import pytest

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.plutus_agent import plutus_agent, ARCA_PROFILES, ARCA_UNIVERSE


def test_plutus_profiles_invariants():
    """Garante que todos os perfis ARCA somam exatamente 100% de alocação."""
    for p_key, p_data in ARCA_PROFILES.items():
        weights = p_data["weights"]
        total_weight = sum(weights.values())
        assert pytest.approx(total_weight, 0.001) == 1.0, f"Perfil {p_key} deve somar 100%"
        assert "REAL_ESTATE" in weights
        assert "EQUITIES_BR" in weights
        assert "FIXED_INCOME" in weights
        assert "INTERNATIONAL" in weights


def test_plutus_universe_integrity():
    """Garante que todos os pilares do universo possuem ativos válidos e consistentes."""
    assert len(ARCA_UNIVERSE["REAL_ESTATE"]) >= 4
    assert len(ARCA_UNIVERSE["EQUITIES_BR"]) >= 4
    assert len(ARCA_UNIVERSE["FIXED_INCOME"]) >= 3
    assert len(ARCA_UNIVERSE["INTERNATIONAL"]) >= 3

    for p_key, assets in ARCA_UNIVERSE.items():
        for a in assets:
            assert "ticker" in a and len(a["ticker"]) > 0
            assert "dy_12m" in a and a["dy_12m"] > 0.0
            assert "name" in a


def test_plutus_simulate_50k_income():
    """Valida a simulação matemática reversa para a meta de R$ 50.000/mês."""
    target_income = 50000.0
    res = plutus_agent.simulate_income(target_monthly_income_brl=target_income, profile_key="ARCA_EQUILIBRADA")

    assert res["status"] == "success"
    assert res["target_monthly_income_brl"] == target_income
    
    # Renda anual de R$ 600.000 / ~9.2% DY = ~R$ 6.5 milhões
    req_patrimony = res["required_patrimony_brl"]
    assert 5000000.0 <= req_patrimony <= 8000000.0

    # Valida que todos os 4 pilares foram gerados
    pillars = res["pillars"]
    assert len(pillars) == 4
    assert "REAL_ESTATE" in pillars
    assert "EQUITIES_BR" in pillars
    assert "FIXED_INCOME" in pillars
    assert "INTERNATIONAL" in pillars

    # Soma dos valores alocados deve igualar o patrimônio requerido
    allocated_sum = sum(p["allocated_brl"] for p in pillars.values())
    assert pytest.approx(allocated_sum, 1.0) == req_patrimony

    # Renda mensal total gerada deve ser próxima ou igual a meta
    monthly_gen = res["total_monthly_est_brl"]
    assert monthly_gen >= target_income * 0.95

    # Valida a lista de ativos recomendados
    rec = res["recommended_assets"]
    assert len(rec) >= 14
    for item in rec:
        assert item["shares_to_buy"] > 0
        assert item["allocated_brl"] > 0
        assert item["monthly_income_brl"] > 0


def test_plutus_schedule_12_months():
    """Valida que o cronograma sazonal de proventos possui 12 meses."""
    res = plutus_agent.simulate_income(target_monthly_income_brl=50000.0)
    sched = res["monthly_schedule"]
    assert len(sched) == 12
    assert sched[0]["month_name"] == "Janeiro"
    assert sched[11]["month_name"] == "Dezembro"
    # Maio ou Novembro devem ser marcados como meses de pico (JCP/NTN-B)
    peak_months = [m["month_name"] for m in sched if m["is_peak_month"]]
    assert "Maio" in peak_months or "Novembro" in peak_months


def test_plutus_hermes_diagnosis():
    """Valida que o Hermes gera o parecer executivo com diretrizes acionáveis."""
    sim = plutus_agent.simulate_income(target_monthly_income_brl=50000.0)
    diag = plutus_agent.generate_hermes_diagnosis(sim)

    assert diag["status"] == "success"
    assert diag["conductor"] == "HERMES INTELLIGENCE"
    assert "BLINDAGEM TRIBUTÁRIA" in diag["diagnosis_text"]
    assert "PROTEÇÃO CAMBIAL" in diag["diagnosis_text"]
    assert len(diag["recommended_actions"]) >= 3
