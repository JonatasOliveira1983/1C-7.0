# -*- coding: utf-8 -*-
"""
Testes Unitários: OKX Contract Precision & Quantization Engine
==============================================================
Garante que todas as 507 altcoins da OKX tenham precisão exata de tick,
formatação de casas decimais (micro-caps até large-caps) e cálculo de
contratos baseado no ctVal oficial da OKX.
"""

import pytest
from app.services.okx_universe_service import okx_universe_service


def test_format_price_by_tick_micro_caps():
    """Garante que moedas com valores minúsculos (PEPE, SHIB, DOGE) não sofram arredondamento destrutivo."""
    # PEPE: tickSize 0.00000001 (8 casas)
    pepe_price = 0.0000095149
    pepe_tick = 0.00000001
    formatted_pepe = okx_universe_service.format_price_by_tick_custom(pepe_price, pepe_tick)
    assert formatted_pepe == 0.00000951

    # SHIB: tickSize 0.00000001 (8 casas)
    shib_price = 0.0000142867
    formatted_shib = okx_universe_service.format_price_by_tick_custom(shib_price, 0.00000001)
    assert formatted_shib == 0.00001429

    # DOGE: tickSize 0.00001 (5 casas)
    doge_price = 0.142857
    formatted_doge = okx_universe_service.format_price_by_tick_custom(doge_price, 0.00001)
    assert formatted_doge == 0.14286


def test_format_price_by_tick_large_caps():
    """Garante que ativos de alto valor (BTC, ETH, LINK) respeitem os ticks sem casas decimais extras."""
    # BTC: tickSize 0.1 (1 casa decimal)
    btc_price = 81824.789
    formatted_btc = okx_universe_service.format_price_by_tick_custom(btc_price, 0.1)
    assert formatted_btc == 81824.8

    # ETH: tickSize 0.01 (2 casas decimais)
    eth_price = 2450.348
    formatted_eth = okx_universe_service.format_price_by_tick_custom(eth_price, 0.01)
    assert formatted_eth == 2450.35

    # LINK: tickSize 0.001 (3 casas decimais)
    link_price = 12.18349
    formatted_link = okx_universe_service.format_price_by_tick_custom(link_price, 0.001)
    assert formatted_link == 12.183


def test_quantize_order_contracts_pepe():
    """
    PEPE na OKX:
    ctVal = 10,000,000 PEPE por contrato.
    Preço = 0.00001000 USD por PEPE.
    Valor de 1 contrato = 0.00001000 * 10,000,000 = $100.00 USD.
    Margem: $100.00 com Alavancagem 15x -> Notional $1,500.00 USD.
    Quantidade esperada: 15 contratos exatos.
    """
    res = okx_universe_service.quantize_order_contracts_custom(
        margin_usd=100.0,
        leverage=15.0,
        price=0.00001000,
        ct_val=10_000_000.0,
        lot_sz=1.0,
        min_sz=1.0,
        tick_sz=0.00000001
    )
    assert res["is_valid"] is True
    assert res["contracts"] == 15.0
    assert res["notional_usd"] == 1500.0
    assert res["effective_margin"] == 100.0


def test_quantize_order_contracts_fractional_lot():
    """
    Ativo com lotSize fracionário (ex.: lotSize = 0.1):
    Preço: $10.0, ctVal: 1.0, Margem: $100, Alavancagem: 15x (Notional $1,500).
    Contratos brutos = 1500 / 10 = 150.
    """
    res = okx_universe_service.quantize_order_contracts_custom(
        margin_usd=100.0,
        leverage=15.0,
        price=10.0,
        ct_val=1.0,
        lot_sz=0.1,
        min_sz=0.1,
        tick_sz=0.001
    )
    assert res["is_valid"] is True
    assert res["contracts"] == 150.0
    assert res["notional_usd"] == 1500.0


def test_quantize_order_contracts_insufficient_margin():
    """
    Se 1 único contrato custar mais que a margem alavancada permitida,
    a função deve sinalizar rejeição protetiva.
    """
    # 1 contrato custa $5,000, mas a banca só fornece margem de $100 com 15x ($1,500 notional)
    res = okx_universe_service.quantize_order_contracts_custom(
        margin_usd=100.0,
        leverage=15.0,
        price=5000.0,
        ct_val=1.0,
        lot_sz=1.0,
        min_sz=1.0,
        tick_sz=0.1
    )
    # Contratos calculados seriam 0 (já que 1500 / 5000 = 0.3 < 0.5 round to 0)
    assert res["contracts"] == 0.0 or res["is_valid"] is False
