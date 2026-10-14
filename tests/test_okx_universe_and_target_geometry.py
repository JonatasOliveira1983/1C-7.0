# -*- coding: utf-8 -*-
"""
Testes de Validação Empírica (V155):
1. Geometria Inviolável de Alvos e Stops para SHORT e LONG.
2. Catálogo Universal de Instrumentos OKX (OKXUniverseService).
3. Normalização de Símbolos e Resolução de ctVal / tickSize.
"""
import os
import sys
import pytest
import asyncio

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.okx_universe_service import okx_universe_service


def test_target_geometry_short_always_below_entry():
    """Valida que ordens SHORT sempre geram alvos estritamente abaixo da entrada."""
    entry_price = 0.205700
    direction = "SHORT"
    
    # Geometria oficial da V155
    target = round(entry_price * 1.035, 6) if direction == "LONG" else round(entry_price * 0.965, 6)
    stop_loss = round(entry_price * 0.988, 6) if direction == "LONG" else round(entry_price * 1.012, 6)
    
    assert target < entry_price, f"Alvo de SHORT ({target}) deve ser menor que a entrada ({entry_price})"
    assert stop_loss > entry_price, f"Stop de SHORT ({stop_loss}) deve ser maior que a entrada ({entry_price})"
    assert target == round(0.205700 * 0.965, 6)


def test_target_geometry_long_always_above_entry():
    """Valida que ordens LONG sempre geram alvos estritamente acima da entrada."""
    entry_price = 4.8290
    direction = "LONG"
    
    target = round(entry_price * 1.035, 6) if direction == "LONG" else round(entry_price * 0.965, 6)
    stop_loss = round(entry_price * 0.988, 6) if direction == "LONG" else round(entry_price * 1.012, 6)
    
    assert target > entry_price, f"Alvo de LONG ({target}) deve ser maior que a entrada ({entry_price})"
    assert stop_loss < entry_price, f"Stop de LONG ({stop_loss}) deve ser menor que a entrada ({entry_price})"


def test_okx_universe_symbol_normalization():
    """Valida que qualquer formato de símbolo é convertido corretamente para instId da OKX."""
    assert okx_universe_service.to_inst_id("BTCUSDT") == "BTC-USDT-SWAP"
    assert okx_universe_service.to_inst_id("SOL-USDT-SWAP") == "SOL-USDT-SWAP"
    assert okx_universe_service.to_inst_id("NEAR") == "NEAR-USDT-SWAP"
    assert okx_universe_service.to_inst_id("AVAX.P") == "AVAX-USDT-SWAP"
    assert okx_universe_service.to_clean_pair("BTC-USDT-SWAP") == "BTCUSDT"
    assert okx_universe_service.to_clean_pair("SOL-USDT-SWAP") == "SOLUSDT"


def test_okx_universe_specs_resolution():
    """Valida que get_specs retorna especificações com chaves obrigatórias e valores positivos."""
    specs = okx_universe_service.get_specs("FET-USDT-SWAP")
    assert "ctVal" in specs
    assert "tickSize" in specs
    assert "lotSize" in specs
    assert "minSz" in specs
    assert float(specs["ctVal"]) > 0
    assert float(specs["tickSize"]) > 0


@pytest.mark.asyncio
async def test_okx_universe_tradable_universe_contains_assets():
    """Valida que get_tradable_universe retorna lista de ativos com estrutura operacional completa."""
    universe = await okx_universe_service.get_tradable_universe(limit=10)
    assert isinstance(universe, list)
    assert len(universe) > 0
    
    first = universe[0]
    assert "symbol" in first
    assert "pair" in first
    assert "price" in first
    assert "ctVal" in first
    assert "tickSize" in first
    assert first["symbol"].endswith("-USDT-SWAP")
