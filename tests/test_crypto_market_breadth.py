# -*- coding: utf-8 -*-
"""
1CRYPTEN — Suite de Testes para Market Breadth e Skills Quantitativas.
Valida:
1. Calculo de amplitude de mercado (BEAR_DOMINANT, CHOP_CONSOLIDATION, BULL_EXPANSION).
2. Integridade dos arquivos SKILL.md em .agents/skills/ (Zero Emojis e formato canônico).
"""
import sys
from pathlib import Path
root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

import pytest
from backend.app.services.market_intel_engine import market_intel_engine


def test_market_breadth_empty_default():
    """Valida retorno padrao neutro quando matriz esta vazia."""
    res = market_intel_engine.calculate_crypto_market_breadth([])
    assert res["breadth_score"] == 50.0
    assert res["regime"] == "NEUTRAL"
    assert res["total_monitored"] == 0


def test_market_breadth_bear_dominant():
    """Valida deteccao de BEAR_DOMINANT com alta pressao vendedora."""
    bear_universe = [
        {"symbol": f"ALT{i}-USDT-SWAP", "1c_range": 20.0, "change_24h": -4.5, "1c_exp": 60.0, "lsr": 1.4}
        for i in range(20)
    ]
    res = market_intel_engine.calculate_crypto_market_breadth(bear_universe)
    assert res["regime"] == "BEAR_DOMINANT"
    assert res["breadth_score"] <= 35.0
    assert "SHORT" in res["directive"]


def test_market_breadth_bull_expansion():
    """Valida deteccao de BULL_EXPANSION com forca compradora generalizada."""
    bull_universe = [
        {"symbol": f"ALT{i}-USDT-SWAP", "1c_range": 85.0, "change_24h": 6.0, "1c_exp": 75.0, "lsr": 0.85}
        for i in range(20)
    ]
    res = market_intel_engine.calculate_crypto_market_breadth(bull_universe)
    assert res["regime"] == "BULL_EXPANSION"
    assert res["breadth_score"] >= 66.0
    assert "Alta" in res["directive"] or "Compras" in res["directive"]


def test_skills_zero_emojis_and_existence():
    """Valida existencia e ausencia de emojis nas skills backtest_quant_auditor e crypto_market_breadth."""
    skills_dir = root_path / ".agents" / "skills"
    
    backtest_skill = skills_dir / "backtest_quant_auditor" / "SKILL.md"
    assert backtest_skill.exists(), "Skill backtest_quant_auditor deve existir"
    text_backtest = backtest_skill.read_text(encoding="utf-8")
    assert "name: backtest_quant_auditor" in text_backtest
    assert "Walk-Forward" in text_backtest or "walk-forward" in text_backtest.lower()

    breadth_skill = skills_dir / "crypto_market_breadth" / "SKILL.md"
    assert breadth_skill.exists(), "Skill crypto_market_breadth deve existir"
    text_breadth = breadth_skill.read_text(encoding="utf-8")
    assert "name: crypto_market_breadth" in text_breadth
    assert "BEAR_DOMINANT" in text_breadth

    import re
    emoji_regex = re.compile(r'[\U00010000-\U0010ffff]|[\u2600-\u27bf]')
    assert not emoji_regex.search(text_backtest), "backtest_quant_auditor nao deve conter emojis"
    assert not emoji_regex.search(text_breadth), "crypto_market_breadth nao deve conter emojis"
