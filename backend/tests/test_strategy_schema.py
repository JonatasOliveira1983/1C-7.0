# -*- coding: utf-8 -*-
"""
Tests for Laya Quantitative Knowledge Base & Strategy Relational Schema.
Padrao 1Crypten: Zero Emojis, TDD Estrito, Invariante 50X.
"""
import os
import sys
import sqlite3
import pytest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database.migrations.create_laya_strategies_table import (
    init_laya_strategy_tables,
    seed_canonical_strategies,
    get_strategy_by_id,
    list_active_strategies,
)

TEST_DB = BACKEND_DIR / "test_quant_strategies.db"

@pytest.fixture(autouse=True)
def cleanup():
    if TEST_DB.exists():
        try:
            TEST_DB.unlink()
        except Exception:
            pass
    yield
    if TEST_DB.exists():
        try:
            TEST_DB.unlink()
        except Exception:
            pass

def test_tables_creation():
    """Valida a criacao das tabelas laya_strategies e laya_strategy_params."""
    conn = init_laya_strategy_tables(str(TEST_DB))
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='laya_strategies'")
    assert cursor.fetchone() is not None, "Tabela laya_strategies deve existir"
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='laya_strategy_params'")
    assert cursor.fetchone() is not None, "Tabela laya_strategy_params deve existir"
    conn.close()

def test_canonical_strategies_seeding():
    """Valida a insercao das estrategias canonicas validadas pela literatura."""
    conn = init_laya_strategy_tables(str(TEST_DB))
    seed_canonical_strategies(str(TEST_DB))
    
    strategies = list_active_strategies(str(TEST_DB))
    strat_ids = [s["id"] for s in strategies]
    
    assert "STRAT_COINT_ZSCORE_50X" in strat_ids, "Estrategia Pairs Trading Z-Score deve estar presente"
    assert "STRAT_TRIPLE_BARRIER_50X" in strat_ids, "Estrategia Triple Barrier deve estar presente"
    assert "STRAT_FUNDING_ARB_50X" in strat_ids, "Estrategia Funding Rate Arbitrage deve estar presente"

def test_leverage_invariant():
    """Invariante 1Crypten: Alavancagem default de todas as estrategias quantitativas deve ser 50.0X."""
    conn = init_laya_strategy_tables(str(TEST_DB))
    seed_canonical_strategies(str(TEST_DB))
    
    strategies = list_active_strategies(str(TEST_DB))
    for strat in strategies:
        assert strat["default_leverage"] == 50.0, f"Estrategia {strat['id']} deve ter alavancagem exatamente 50.0X"
        assert strat["default_leverage"] != 15.0, "Alavancagem 15X eh obsoleta e proibida"

def test_strategy_parameters_query():
    """Valida a consulta dos parametros matematicos (Z-Score, ATR, janelas temporais)."""
    conn = init_laya_strategy_tables(str(TEST_DB))
    seed_canonical_strategies(str(TEST_DB))
    
    zscore_strat = get_strategy_by_id("STRAT_COINT_ZSCORE_50X", str(TEST_DB))
    assert zscore_strat is not None
    assert zscore_strat["regime"] == "LATERAL"
    assert "Z = (Spread - Mean) / StdDev" in zscore_strat["mathematical_basis"]
    
    params = zscore_strat.get("params", {})
    assert float(params.get("z_entry_threshold", 0)) == 2.0
    assert float(params.get("z_exit_threshold", 99)) == 0.0
    assert float(params.get("z_stop_threshold", 0)) == 3.2
