import pytest
from app.services.laya_router_service import laya_router_service
from services.sandbox_service import sandbox_service
from services.order_projection_service import proj_service

def test_h1_breakout_short_distant_support_capped():
    """
    Testa o cenário SEI: rompimento de baixa com suporte anterior muito distante.
    O stop loss jamais deve ficar no suporte antigo (ex: 0.0706), e sim limitado
    estritamente a no máximo 1.2% de distância do preço de entrada (-18% ROI em 15x).
    """
    current_price = 0.06149
    acc_range = {
        "is_consolidating": True,
        "support_h1": 0.0702,  # Suporte anterior 14.8% acima do preço atual!
        "resistance_h1": 0.0750
    }
    atr_pct = 2.5
    lsr = 1.40
    oi_delta_pct = 1.0
    funding_rate = 0.0001
    btc_trend_bias = -0.2

    res = laya_router_service.evaluate_h1_breakout(
        symbol="SEI-USDT-SWAP",
        current_price=current_price,
        acc_range=acc_range,
        lsr=lsr,
        oi_delta_pct=oi_delta_pct,
        btc_trend_bias=btc_trend_bias,
        funding_rate=funding_rate,
        atr_pct=atr_pct
    )

    assert res["qualifies"] is True
    assert res["direction"] == "SHORT"
    stop_loss = res["stop_loss"]
    assert stop_loss > current_price
    
    # Distância percentual do stop não pode ultrapassar 1.2%
    stop_dist = (stop_loss - current_price) / current_price
    assert stop_dist <= 0.0125
    
    # Em 15x de alavancagem, o stop ROI não pode ser pior do que -18.75%
    roi = proj_service.calculate_roi(current_price, stop_loss, "SHORT", 15.0)
    assert roi >= -18.75
    assert roi <= -10.0


def test_h1_breakout_long_distant_resistance_capped():
    """
    Testa rompimento de alta com resistência muito distante.
    O stop loss deve ser cravado com teto de 1.2% no preço.
    """
    current_price = 100.0
    acc_range = {
        "is_consolidating": True,
        "support_h1": 75.0,
        "resistance_h1": 80.0  # Resistência antiga 20% abaixo!
    }
    atr_pct = 2.5
    lsr = 0.90
    oi_delta_pct = 1.2
    funding_rate = 0.0001
    btc_trend_bias = 0.1

    res = laya_router_service.evaluate_h1_breakout(
        symbol="ETH-USDT-SWAP",
        current_price=current_price,
        acc_range=acc_range,
        lsr=lsr,
        oi_delta_pct=oi_delta_pct,
        btc_trend_bias=btc_trend_bias,
        funding_rate=funding_rate,
        atr_pct=atr_pct
    )

    assert res["qualifies"] is True
    assert res["direction"] == "LONG"
    stop_loss = res["stop_loss"]
    assert stop_loss < current_price

    stop_dist = (current_price - stop_loss) / current_price
    assert stop_dist <= 0.0125

    roi = proj_service.calculate_roi(current_price, stop_loss, "LONG", 15.0)
    assert roi >= -18.75
    assert roi <= -10.0


def test_dvwap_reversion_stop_capping():
    """
    Testa reversão à VWAP com stop limitado a 1.2% de preço.
    """
    current_price = 50.0
    vwap = 48.0
    acc_range = {
        "is_consolidating": True,
        "support_h1": 45.0,
        "resistance_h1": 58.0  # Resistência distante
    }
    atr_pct = 1.5
    lsr = 1.30
    funding_rate = 0.0001
    btc_trend_bias = -0.1

    res = laya_router_service.evaluate_dvwap_reversion(
        symbol="SOL-USDT-SWAP",
        current_price=current_price,
        vwap=vwap,
        acc_range=acc_range,
        lsr=lsr,
        btc_trend_bias=btc_trend_bias,
        funding_rate=funding_rate,
        atr_pct=atr_pct
    )

    assert res["qualifies"] is True
    assert res["direction"] == "SHORT"
    stop_dist = (res["stop_loss"] - current_price) / current_price
    assert stop_dist <= 0.0125


@pytest.mark.asyncio
async def test_sandbox_adaptive_stop_limits():
    """
    Verifica se o cálculo de stop adaptativo do sandbox respeita o limite de -18% ROI.
    """
    meta = {"leverage": 15.0, "tickSize": 0.0001}
    # Forçar fallback fixo
    res = await sandbox_service._calculate_adaptive_stop(
        symbol="TEST-USDT-SWAP",
        entry_price=10.0,
        side="LONG",
        contract_meta=meta,
        is_ranging=False
    )

    # Fallback deve ser exatamente -15.0% ROI (1.0% de preço)
    assert -18.5 <= res["stop_roi"] <= -14.5
    assert res["stop_price"] < 10.0


def test_laya_min_entry_score_sniper():
    """Garante que a régua de entrada mínima está em 90 para eliminar overtrading e taxas."""
    assert laya_router_service.MIN_ENTRY_SCORE == 90


def test_quarantine_blocks_reentry():
    """Garante que um ativo com stop loss fica em quarentena canônica de 2 horas (7200s)."""
    import time
    sym = "TESTLINK"
    laya_router_service.record_stop_loss(sym, direction="LONG", cooldown_seconds=7200)
    assert laya_router_service.is_symbol_in_cooldown(sym) is True
    assert laya_router_service.is_symbol_in_cooldown("TESTLINK-USDT-SWAP") is True


def test_range_boundary_does_not_trigger_on_channel_middle():
    """
    Testa que o miolo do canal (ex: range_pos 50%) NUNCA qualifica como
    absorção no suporte ou exaustão na resistência.
    """
    # Canal de 3% (100.0 vs 98.5 a 101.5): preço exatamente no meio (100.0)
    current_price = 100.0
    acc_range = {
        "is_consolidating": True,
        "support_h1": 98.5,
        "resistance_h1": 101.5
    }
    res = laya_router_service.evaluate_range_boundary_reversal(
        symbol="TEST-USDT-SWAP",
        current_price=current_price,
        acc_range=acc_range,
        lsr=1.0,
        oi_delta_pct=0.0,
        btc_trend_bias=0.0,
        funding_rate=0.0,
        atr_pct=1.5
    )
    assert res["qualifies"] is False
    assert res["direction"] == "HOLD"
    assert "MEIO DE CANAL" in res["rationale"] or "MIOLO" in res["rationale"]


def test_short_symmetry_at_resistance():
    """
    Garante que setups de SHORT na resistência H1 conseguem atingir score >= 90
    em condições neutras/favoráveis (LSR neutro 1.0 e BTC estável/fraco),
    eliminando a assimetria que forçava 100% dos trades a serem LONG.
    """
    current_price = 101.6
    acc_range = {
        "is_consolidating": True,
        "support_h1": 98.0,
        "resistance_h1": 102.0
    }
    res = laya_router_service.evaluate_range_boundary_reversal(
        symbol="TEST-USDT-SWAP",
        current_price=current_price,
        acc_range=acc_range,
        lsr=1.0,
        oi_delta_pct=0.2,
        btc_trend_bias=-0.1,
        funding_rate=0.0,
        atr_pct=1.5
    )
    assert res["qualifies"] is True

def test_altcoin_short_vetoed_when_btc_bullish_and_dominance_high():
    """
    [RED PHASE TDD]
    Garante que se a dominância do BTC estiver alta (>= 59.0% ou subindo) e o BTC estiver positivo (> 0.0%),
    QUALQUER setup de SHORT em Altcoin seja terminantemente vetado pelo Farol Macro / BTC.D.
    """
    from app.services.laya_btc_specialist_service import laya_btc_specialist
    climate = laya_btc_specialist.classify_altcoin_climate(
        btc_change_24h=0.5,
        btc_trend_bias=0.5,
        btc_dominance=60.1,
        dominance_trend="STABLE"
    )
    assert climate["altcoin_short_allowed"] is False
    assert climate["climate"] == "BTC_DRAINAGE"

    acc_range = {
        "is_consolidating": True,
        "support_h1": 90.0,
        "resistance_h1": 100.0
    }
    btc_intel = {
        "altcoin_climate": climate["climate"],
        "altcoin_long_allowed": climate["altcoin_long_allowed"],
        "altcoin_short_allowed": climate["altcoin_short_allowed"],
        "btc_dominance": 60.1
    }
    multi_eval = laya_router_service.evaluate_multi_setup_opportunity(
        symbol="XRPUSDT",
        current_price=99.0, # 90% do range (resistência)
        acc_range=acc_range,
        vwap=95.0,
        bb_width_pct=5.0,
        lsr=1.0,
        oi_delta_pct=0.0,
        btc_trend_bias=1.2,
        funding_rate=0.0,
        atr_pct=1.0,
        btc_intel=btc_intel
    )
    assert multi_eval["qualifies"] is False
    assert multi_eval["direction"] == "HOLD"


def test_global_circuit_breaker():
    """
    [RED PHASE TDD]
    Garante que se ocorrerem 3 stops consecutivos em <= 90 minutos (5400s),
    o Circuit Breaker Global seja ativado e congele todas as novas entradas por 45 minutos (2700s).
    """
    import time
    now = time.time()
    laya_router_service._global_stop_history = []
    laya_router_service._global_circuit_breaker_until = 0.0

    # 1. Registra 2 stops: ainda não deve travar o sistema globalmente
    laya_router_service.record_stop_loss("SEIUSDT", direction="LONG", cooldown_seconds=7200)
    laya_router_service.record_stop_loss("TIAUSDT", direction="LONG", cooldown_seconds=7200)
    assert laya_router_service.is_global_circuit_breaker_active() is False

    # 2. Registra o 3º stop no intervalo de 90 min: DEVE ATIVAR O CIRCUIT BREAKER GLOBAL
    laya_router_service.record_stop_loss("POLUSDT", direction="SHORT", cooldown_seconds=7200)
    assert laya_router_service.is_global_circuit_breaker_active() is True
    assert laya_router_service._global_circuit_breaker_until >= now + 2600

    # 3. Limpeza para não afetar testes subsequentes
    laya_router_service._global_stop_history = []
    laya_router_service._global_circuit_breaker_until = 0.0


def test_cluster_correlation_cap():
    """
    [RED PHASE TDD - TAREFA 2]
    Garante que a Laya descorrelacione a carteira entre os 4 slots:
    1. Máximo de 2 ativos simultâneos do mesmo cluster setorial (ex: L1_BLUECHIP).
    2. Se 2 ativos do mesmo cluster já estiverem ativos (ex: ETH e SOL), o 3º (ex: AVAX) é vetado.
    """
    active_symbols = ["ETH-USDT-SWAP", "SOL-USDT-SWAP"]
    # get_symbol_sector_cluster deve identificar o cluster correto
    assert laya_router_service.get_symbol_sector_cluster("ETHUSDT") == "L1_BLUECHIP"
    assert laya_router_service.get_symbol_sector_cluster("SOLUSDT") == "L1_BLUECHIP"
    assert laya_router_service.get_symbol_sector_cluster("AVAXUSDT") == "L1_BLUECHIP"
    assert laya_router_service.get_symbol_sector_cluster("RENDERUSDT") == "AI_DEPIN"

    # Se ETH e SOL já estão ativos, AVAX deve violar o teto de cluster (máximo 2 por setor)
    assert laya_router_service.is_cluster_limit_reached("AVAXUSDT", active_symbols) is True
    # RENDER é de outro cluster (AI_DEPIN), logo deve ser permitido
    assert laya_router_service.is_cluster_limit_reached("RENDERUSDT", active_symbols) is False


def test_cvd_absorption_veto():
    """
    [RED PHASE TDD - TAREFA 3]
    Garante que se o candle recente de 5m apresentar agressão vendedora desbalanceada
    (ex: taker_sell_ratio >= 1.40 — faca caindo sem absorção), o trade de LONG no suporte seja vetado.
    Da mesma forma, se o topo apresentar agressão compradora forte (taker_buy_ratio >= 1.40), o SHORT seja vetado.
    """
    acc_range = {
        "is_consolidating": True,
        "support_h1": 100.0,
        "resistance_h1": 110.0
    }
    # Caso 1: Preço no suporte (101.0), mas com agressão vendedora violenta (taker_sell_ratio = 1.6)
    res_long_vetoed = laya_router_service.evaluate_range_boundary_reversal(
        symbol="DOTUSDT",
        current_price=101.0,
        acc_range=acc_range,
        lsr=1.0,
        oi_delta_pct=0.2,
        btc_trend_bias=0.0,
        funding_rate=0.0,
        atr_pct=1.5,
        taker_sell_ratio=1.6 # Faca caindo
    )
    assert res_long_vetoed["qualifies"] is False
    assert res_long_vetoed["direction"] == "HOLD"
    assert "FACA CAINDO" in res_long_vetoed["rationale"] or "AGRESSÃO VENDEDORA" in res_long_vetoed["rationale"]

    # Caso 2: Preço no suporte (101.0), com absorção real (taker_sell_ratio equilibrado/baixo <= 1.2)
    res_long_ok = laya_router_service.evaluate_range_boundary_reversal(
        symbol="DOTUSDT",
        current_price=101.0,
        acc_range=acc_range,
        lsr=1.0,
        oi_delta_pct=0.2,
        btc_trend_bias=0.0,
        funding_rate=0.0,
        atr_pct=1.5,
        taker_sell_ratio=1.0 # Absorção equilibrada
    )
    assert res_long_ok["qualifies"] is True
    assert res_long_ok["direction"] == "LONG"


