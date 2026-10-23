# -*- coding: utf-8 -*-
"""
TDD Tests: MarketIntelEngine (1C-EXP, 1C-RANGE & AI-Ready Export)
Inspirado no benchmark eAssets.ai e integrado à Laya Soberana V162.
"""
import pytest
from backend.app.services.market_intel_engine import MarketIntelEngine


@pytest.fixture
def intel_engine():
    return MarketIntelEngine()


def test_calculate_1c_range_levels(intel_engine):
    """
    Testa o cálculo do nível de canal 1C-RANGE (0% a 100%):
    - Preço no suporte -> 0.0%
    - Preço na resistência -> 100.0%
    - Preço no centro -> 50.0%
    - Preço abaixo do suporte -> negativo (rompimento para baixo)
    - Preço acima da resistência -> > 100.0% (rompimento para cima)
    """
    support = 100.0
    resistance = 110.0

    # No centro
    range_mid = intel_engine.calculate_1c_range(current_price=105.0, support=support, resistance=resistance)
    assert range_mid == pytest.approx(50.0, abs=0.1)

    # No piso
    range_floor = intel_engine.calculate_1c_range(current_price=100.0, support=support, resistance=resistance)
    assert range_floor == pytest.approx(0.0, abs=0.1)

    # No teto
    range_ceil = intel_engine.calculate_1c_range(current_price=110.0, support=support, resistance=resistance)
    assert range_ceil == pytest.approx(100.0, abs=0.1)

    # Rompimento LONG
    range_break_up = intel_engine.calculate_1c_range(current_price=112.0, support=support, resistance=resistance)
    assert range_break_up > 100.0

    # Rompimento SHORT
    range_break_down = intel_engine.calculate_1c_range(current_price=98.0, support=support, resistance=resistance)
    assert range_break_down < 0.0


def test_calculate_1c_exp_score(intel_engine):
    """
    Testa o score 1C-EXP (0 a 100):
    - Alta compressão (bb_width baixo) + volume crescendo + OI positivo -> EXP alto (> 75)
    - Mercado dilatado/sem compressão -> EXP baixo (< 35)
    """
    # Cenário de compressão elástica pré-rompimento
    high_exp = intel_engine.calculate_1c_exp(
        bb_width_pct=4.2,      # Bandas estreitas (< 6.5%)
        vol_rel_5m=1.8,        # Volume 1.8x acima da média
        oi_delta_pct=2.5,      # Capital novo entrando
        adx=18.0               # Fase de acumulação/compressão
    )
    assert high_exp >= 75.0, f"Deveria ter alto EXP de explosão, obteve: {high_exp}"

    # Cenário de mercado relaxado/sem ignição
    low_exp = intel_engine.calculate_1c_exp(
        bb_width_pct=14.5,     # Bandas largas
        vol_rel_5m=0.7,        # Volume fraco
        oi_delta_pct=-1.2,     # Desalavancagem
        adx=35.0
    )
    assert low_exp < 35.0, f"Deveria ter baixo EXP, obteve: {low_exp}"


def test_ai_context_serialization(intel_engine):
    """
    Testa se o exportador semântico para IA gera um formato limpo,
    legível por máquinas e sem aninhamentos complexos inúteis.
    """
    mock_assets = [
        {
            "symbol": "SOL-USDT-SWAP",
            "price": 185.50,
            "change_24h": 4.25,
            "1c_exp": 84.0,
            "1c_range": 98.2,
            "lsr": 0.85,
            "funding_rate": 0.0001,
            "setup": "H1_BREAKOUT_LONG",
            "action": "LONG"
        },
        {
            "symbol": "AVAX-USDT-SWAP",
            "price": 28.10,
            "change_24h": -1.2,
            "1c_exp": 32.0,
            "1c_range": 12.0,
            "lsr": 1.65,
            "funding_rate": 0.0003,
            "setup": "RANGE_FLOOR_REVERSAL",
            "action": "LONG"
        }
    ]

    context = intel_engine.format_ai_market_context(
        btc_climate="ALTCOIN_EXPANSION",
        btc_dominance=56.2,
        matrix_assets=mock_assets
    )

    assert "macro_climate" in context
    assert context["macro_climate"]["regime"] == "ALTCOIN_EXPANSION"
    assert "top_explosive_assets" in context
    assert len(context["top_explosive_assets"]) > 0
    assert context["top_explosive_assets"][0]["symbol"] == "SOL-USDT-SWAP"
    assert "summary_prompt" in context
    assert "SOL-USDT-SWAP" in context["summary_prompt"]


def test_universal_market_scan_filtering(intel_engine):
    """
    Testa a varredura universal sobre o universo total de 507 pares da OKX:
    - Filtra pares zumbis (volume < min_volume_usd)
    - Exclui pares não perpétuos ou pares BTC se exclude_btc=True
    - Retorna ativos ordenados por ignição de robôs (1c_exp)
    """
    mock_tickers = {
        "ETH-USDT-SWAP": {"last": 2650.0, "high24h": 2700.0, "low24h": 2580.0, "open24h": 2600.0, "volume_24h_usd": 120_000_000.0},
        "BTC-USDT-SWAP": {"last": 65000.0, "high24h": 66000.0, "low24h": 64000.0, "open24h": 64500.0, "volume_24h_usd": 800_000_000.0},
        "ZOMBIE-USDT-SWAP": {"last": 0.05, "high24h": 0.051, "low24h": 0.049, "open24h": 0.05, "volume_24h_usd": 40_000.0}, # Abaixo de 500k
        "EXPLOSIVE-USDT-SWAP": {"last": 1.25, "high24h": 1.26, "low24h": 1.24, "open24h": 1.20, "volume_24h_usd": 45_000_000.0}, # Compressão estreita + volume
    }

    results = intel_engine.scan_universal_market(
        tickers_cache=mock_tickers,
        min_volume_usd=500_000.0,
        exclude_btc=True
    )

    symbols = [r["symbol"] for r in results]
    assert "ETH-USDT-SWAP" in symbols
    assert "EXPLOSIVE-USDT-SWAP" in symbols
    assert "BTC-USDT-SWAP" not in symbols, "BTC deve ser excluído da lista de execução direta"
    assert "ZOMBIE-USDT-SWAP" not in symbols, "Pares sem liquidez institucional devem ser expurgados"
    assert len(results) == 2


def test_bot_ignition_flag(intel_engine):
    """
    Testa se o detector de robôs institucionais rotula corretamente:
    - Ativo com 1C-EXP >= 70 e volume expressivo -> bot_ignition = True
    - Ativo sem aceleração -> bot_ignition = False
    """
    active_row = intel_engine.evaluate_single_asset_intel(
        symbol="TIA-USDT-SWAP",
        last_price=6.50,
        open24h=6.10,
        high24h=6.60,
        low24h=6.45,
        vol24h=80_000_000.0
    )
    assert active_row["1c_exp"] >= 70.0
    assert active_row["bot_ignition"] is True
    assert "IGNIÇÃO" in active_row["bot_status"] or "EXPANSÃO" in active_row["bot_status"]

