import sys, os
sys.path.insert(0, os.path.abspath("backend"))
import pytest
from app.services.laya_router_service import laya_router_service


def test_veto_falso_canal_alta_micro_inclinacao():
    """
    [V202-LINK-PRECISION]
    Garante que micro-afastamento de medias (+0.01% como ocorreu na LINK)
    NUNCA seja classificado como Canal de Alta Soberano (LONG_ONLY).
    Exige inclinacao real (diff_pct >= +0.35%) para autorizar regime de alta.
    """
    # Simulando candles 2H onde SMA8 fica em 10.8515 e SMA21 em 10.8505 (+0.01% dif)
    klines_2h = []
    for i in range(25):
        klines_2h.append({
            "ts": 1700000000 + i * 7200,
            "open": 10.85,
            "high": 10.86,
            "low": 10.84,
            "close": 10.851,
            "vol": 1000
        })
    
    # Com BTC em NEUTRAL ou DRAINAGE
    regime = laya_router_service.enforce_2h_directional_regime("LINK", klines_2h, btc_macro_direction="NEUTRAL")
    assert regime["regime"] != "LONG_ONLY", "Micro-afastamento (+0.01%) nao pode ser classificado como LONG_ONLY"
    assert regime.get("long_vetoed") is True, "LONG deve ser vetado em consolidao plana"


def test_veto_long_altcoin_se_btc_nao_for_bull_estrito():
    """
    [V202-LINK-PRECISION]
    Garante que compras de altcoin so sao autorizadas se o Bitcoin
    estiver em regime BULL confirmado (ou se a altcoin tiver alt_pump_ignition).
    Se o BTC for BEAR ou NEUTRAL, LONG de altcoin e vetado compulsoriamente.
    """
    # Candles com alta de +0.80% (SMA8 > SMA21)
    klines_2h = []
    curr = 10.0
    for i in range(25):
        curr += 0.05
        klines_2h.append({
            "ts": 1700000000 + i * 7200,
            "open": curr - 0.02,
            "high": curr + 0.03,
            "low": curr - 0.03,
            "close": curr,
            "vol": 2000
        })
    
    # Se BTC estiver em BEAR
    regime_bear = laya_router_service.enforce_2h_directional_regime("LINK", klines_2h, btc_macro_direction="BEAR")
    assert regime_bear.get("long_vetoed") is True
    assert regime_bear["regime"] != "LONG_ONLY"

    # Se BTC estiver em NEUTRAL (sem forca compradora)
    regime_neutral = laya_router_service.enforce_2h_directional_regime("LINK", klines_2h, btc_macro_direction="NEUTRAL")
    assert regime_neutral.get("long_vetoed") is True, "BTC neutro/sem fluxo comprador veta LONG em altcoins correlacionadas"
