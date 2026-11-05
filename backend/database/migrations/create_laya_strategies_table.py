# -*- coding: utf-8 -*-
"""
Migração e Gerenciador de Estratégias Quantitativas da Laya Soberana (SQLite).
Banco de Dados: local_sniper.db
Padrão 1Crypten: Zero Emojis, Alavancagem Fixa 50X, Never Give Back.
"""
import os
import sqlite3
from typing import Dict, List, Any, Optional
from pathlib import Path

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "local_sniper.db"
)

def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    target = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row
    return conn

def init_laya_strategy_tables(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Cria tabelas relacionais de estratégias da Laya se não existirem."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS laya_strategies (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        regime TEXT NOT NULL,
        mathematical_basis TEXT NOT NULL,
        academic_source TEXT,
        default_leverage REAL NOT NULL DEFAULT 50.0,
        min_adx REAL NOT NULL DEFAULT 0.0,
        max_adx REAL NOT NULL DEFAULT 100.0,
        active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS laya_strategy_params (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        strategy_id TEXT NOT NULL,
        param_key TEXT NOT NULL,
        param_value TEXT NOT NULL,
        param_type TEXT NOT NULL,
        description TEXT,
        FOREIGN KEY (strategy_id) REFERENCES laya_strategies(id) ON DELETE CASCADE,
        UNIQUE(strategy_id, param_key)
    )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_strat_params_strat_id ON laya_strategy_params(strategy_id)")
    conn.commit()
    return conn

def seed_canonical_strategies(db_path: Optional[str] = None) -> None:
    """Insere o catálogo de estratégias canônicas da Laya validadas pela literatura."""
    conn = init_laya_strategy_tables(db_path)
    cursor = conn.cursor()

    canonical_strategies = [
        {
            "id": "STRAT_COINT_ZSCORE_50X",
            "name": "Pairs Trading Cointegration & Z-Score 50X",
            "category": "STATISTICAL_ARBITRAGE",
            "regime": "LATERAL",
            "mathematical_basis": "Z = (Spread - Mean) / StdDev; Cointegration Engle-Granger p < 0.05",
            "academic_source": "Stanford University (2021) MS&E 448 & Bitfinex/Kraken dataset",
            "default_leverage": 50.0,
            "min_adx": 0.0,
            "max_adx": 25.0,
            "params": [
                ("z_entry_threshold", "2.0", "float", "Desvio padrao de entrada estatistica"),
                ("z_exit_threshold", "0.0", "float", "Retorno medio para fechar ordem"),
                ("z_stop_threshold", "3.2", "float", "Corte estatistico para evitar rompimento"),
                ("lookback_short_hours", "6", "int", "Janela curta de media movel"),
                ("lookback_long_hours", "72", "int", "Janela longa de media movel e desvio padrao"),
                ("p_value_max", "0.05", "float", "Valor-p maximo de cointegracao")
            ]
        },
        {
            "id": "STRAT_TRIPLE_BARRIER_50X",
            "name": "Triple Barrier Volatility & Time Expiry 50X",
            "category": "TRIPLE_BARRIER",
            "regime": "TENDENCIA",
            "mathematical_basis": "Barreira Superior = Entry + 2*ATR; Barreira Inferior = Never Give Back 5 Escadinhas; Barreira Temporal = T_max velas",
            "academic_source": "University of Warsaw / Marcos Lopez de Prado (2018)",
            "default_leverage": 50.0,
            "min_adx": 25.0,
            "max_adx": 100.0,
            "params": [
                ("take_profit_atr_mult", "2.5", "float", "Multiplicador ATR da Barreira Superior de Lucro"),
                ("stop_loss_escadinha_active", "true", "bool", "Ativacao da Barreira Inferior Never Give Back"),
                ("time_barrier_bars", "16", "int", "Maximo de velas 15m para resolucao antes do corte"),
                ("never_give_back_rule", "true", "bool", "Invariante de subida unilateral do stop")
            ]
        },
        {
            "id": "STRAT_FUNDING_ARB_50X",
            "name": "Funding Rate Delta Neutral Arbitrage 50X",
            "category": "FUNDING_ARBITRAGE",
            "regime": "LATERAL",
            "mathematical_basis": "Spot Long + Perp Short Swap (Delta = 0); Coleta da taxa de financiamento a cada 8h",
            "academic_source": "Ernst & Young Crypto Derivatives (2021) & OKX Arbitrage Manual",
            "default_leverage": 50.0,
            "min_adx": 0.0,
            "max_adx": 30.0,
            "params": [
                ("min_funding_rate_bps", "15.0", "float", "Taxa minima de financiamento em bps"),
                ("collection_interval_hours", "8", "int", "Ciclo de cobranca da taxa OKX"),
                ("delta_neutral_tolerance", "0.02", "float", "Margem de desvio delta neutro aceitavel")
            ]
        }
    ]

    for strat in canonical_strategies:
        cursor.execute("""
        INSERT INTO laya_strategies (
            id, name, category, regime, mathematical_basis, academic_source,
            default_leverage, min_adx, max_adx, active, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            category=excluded.category,
            regime=excluded.regime,
            mathematical_basis=excluded.mathematical_basis,
            academic_source=excluded.academic_source,
            default_leverage=excluded.default_leverage,
            min_adx=excluded.min_adx,
            max_adx=excluded.max_adx,
            active=1,
            updated_at=CURRENT_TIMESTAMP
        """, (
            strat["id"], strat["name"], strat["category"], strat["regime"],
            strat["mathematical_basis"], strat["academic_source"],
            strat["default_leverage"], strat["min_adx"], strat["max_adx"]
        ))

        for key, val, ptype, desc in strat["params"]:
            cursor.execute("""
            INSERT INTO laya_strategy_params (
                strategy_id, param_key, param_value, param_type, description
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(strategy_id, param_key) DO UPDATE SET
                param_value=excluded.param_value,
                param_type=excluded.param_type,
                description=excluded.description
            """, (strat["id"], key, val, ptype, desc))

    conn.commit()
    conn.close()

def list_active_strategies(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lista todas as estratégias ativas com seus parâmetros."""
    conn = init_laya_strategy_tables(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, name, category, regime, mathematical_basis, academic_source,
           default_leverage, min_adx, max_adx, active, created_at, updated_at
    FROM laya_strategies
    WHERE active = 1
    ORDER BY id ASC
    """)
    rows = cursor.fetchall()

    results = []
    for r in rows:
        strat = dict(r)
        # Obter params
        cursor.execute("""
        SELECT param_key, param_value, param_type, description
        FROM laya_strategy_params
        WHERE strategy_id = ?
        """, (strat["id"],))
        param_rows = cursor.fetchall()
        params = {}
        for p in param_rows:
            params[p["param_key"]] = p["param_value"]
        strat["params"] = params
        results.append(strat)

    conn.close()
    return results

def get_strategy_by_id(strategy_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retorna detalhes de uma estratégia específica pelo ID."""
    conn = init_laya_strategy_tables(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, name, category, regime, mathematical_basis, academic_source,
           default_leverage, min_adx, max_adx, active, created_at, updated_at
    FROM laya_strategies
    WHERE id = ?
    """, (strategy_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    strat = dict(row)
    cursor.execute("""
    SELECT param_key, param_value, param_type, description
    FROM laya_strategy_params
    WHERE strategy_id = ?
    """, (strategy_id,))
    params = {}
    for p in cursor.fetchall():
        params[p["param_key"]] = p["param_value"]
    strat["params"] = params
    conn.close()
    return strat

if __name__ == "__main__":
    init_laya_strategy_tables()
    seed_canonical_strategies()
    print("[MIGRATION] Estrategias quantitativas migradas e populadas com sucesso no local_sniper.db.")
