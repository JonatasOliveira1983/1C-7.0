# -*- coding: utf-8 -*-
"""
1CRYPTEN — Market Intel Endpoints (V163)
=======================================
Endpoints inspirados na proposta do eAssets.ai e metodologia Encryptos:
1. /api/v1/market/screener-matrix: Varredura universal de 507 pares da OKX ou Top 30 Titãs.
2. /api/v1/market/ai-context: Exportador semântico estruturado para consumo por IAs e Agentes.
"""

from fastapi import APIRouter, Query
from typing import Dict, Any, List, Optional
import time

from app.services.market_intel_engine import market_intel_engine
from app.services.okx_universe_service import OKXUniverseService
from app.services.laya_router_service import laya_router_service

router = APIRouter()
universe_service = OKXUniverseService()


@router.get("/screener-matrix", response_model=Dict[str, Any])
async def get_screener_matrix(
    universe: str = Query("all", description="Modo de varredura: 'all' (507 pares OKX) ou 'titans' (Top 30 Altcoins)"),
    min_volume: float = Query(500_000.0, description="Volume mínimo 24h em USD para filtrar pares zumbis")
):
    """
    Retorna a matriz em tempo real dos ativos monitorados.
    No modo 'all' (Encryptos), varre os 507 contratos perpétuos da OKX e detecta a aceleração de robôs.
    """
    u_val = str(universe.default if hasattr(universe, "default") else universe).lower()
    mv_val = float(min_volume.default if hasattr(min_volume, "default") else min_volume)

    btc_macro = laya_router_service.get_pulse().get("btc_climate", {})
    btc_climate = btc_macro.get("regime", "ALTCOIN_EXPANSION")
    btc_dominance = btc_macro.get("dominance", 57.5)

    if u_val == "titans":
        tradable = await universe_service.get_tradable_universe(limit=30, exclude_btc=True)
        matrix_rows = []
        for item in tradable:
            symbol = item.get("symbol", "")
            last_price = float(item.get("price", 0.0) or 0.0)
            high24h = float(item.get("high_24h", last_price * 1.05) or (last_price * 1.05))
            low24h = float(item.get("low_24h", last_price * 0.95) or (last_price * 0.95))
            open24h = float(item.get("open24h", last_price) or last_price)
            vol24h = float(item.get("volume_24h_usd", 0.0) or 0.0)

            row = market_intel_engine.evaluate_single_asset_intel(
                symbol=symbol,
                last_price=last_price,
                open24h=open24h,
                high24h=high24h,
                low24h=low24h,
                vol24h=vol24h,
                btc_climate=btc_climate
            )
            matrix_rows.append(row)
        matrix_rows.sort(key=lambda x: (x.get("1c_exp", 0.0), x.get("vol_ccy_24h", 0.0)), reverse=True)
    else:
        # Modo 'all': Varredura Universal de 507 Pares da OKX
        tickers = await universe_service.sync_tickers()
        matrix_rows = market_intel_engine.scan_universal_market(
            tickers_cache=tickers,
            min_volume_usd=min_volume,
            exclude_btc=True,
            btc_climate=btc_climate
        )

    # Estatísticas de robôs institucionais
    ignition_count = sum(1 for r in matrix_rows if r.get("bot_ignition", False))

    return {
        "status": "SUCCESS",
        "timestamp": time.time(),
        "universe_mode": universe.lower(),
        "btc_climate": btc_climate,
        "btc_dominance": btc_dominance,
        "total_scanned": len(matrix_rows),
        "bot_ignitions_detected": ignition_count,
        "data": matrix_rows
    }


@router.get("/ai-context", response_model=Dict[str, Any])
async def get_ai_market_context(
    universe: str = Query("all", description="Universo a exportar: 'all' ou 'titans'"),
    top_limit: int = Query(8, description="Número de ativos mais explosivos a incluir no resumo executivo")
):
    """
    Retorna o payload semântico normalizado do mercado pronto para ser copiado ou
    injetado diretamente em LLMs (Hermes, Claude, GPT, Gemini).
    """
    u_val = str(universe.default if hasattr(universe, "default") else universe)
    tl_val = int(top_limit.default if hasattr(top_limit, "default") else top_limit)
    screener = await get_screener_matrix(universe=u_val, min_volume=500_000.0)
    matrix_data = screener.get("data", [])
    btc_climate = screener.get("btc_climate", "ALTCOIN_EXPANSION")
    btc_dominance = screener.get("btc_dominance", 57.5)

    ai_payload = market_intel_engine.format_ai_market_context(
        btc_climate=btc_climate,
        btc_dominance=btc_dominance,
        matrix_assets=matrix_data,
        top_limit=tl_val
    )

    return {
        "status": "SUCCESS",
        "context": ai_payload
    }


@router.get("/contract-specs", response_model=Dict[str, Any])
async def get_contract_specs(
    symbol: str = Query(..., description="Símbolo base (ex: BTCUSDT, PEPEUSDT ou PEPE-USDT-SWAP)")
):
    """
    Retorna as especificações de precisão canônicas da OKX para o par (tickSz, lotSz, minSz, ctVal),
    além de exemplos de preços formatados e quantização de contratos.
    """
    from app.services.okx_universe_service import okx_universe_service
    
    specs = okx_universe_service.get_specs(symbol)
    sample_price = 0.00001 if "PEPE" in symbol.upper() or "SHIB" in symbol.upper() else 1.0
    sample_quantization = okx_universe_service.quantize_order_contracts(
        symbol=symbol,
        margin_usd=150.0,
        leverage=15.0,
        price=sample_price
    )
    
    return {
        "status": "SUCCESS",
        "symbol": symbol,
        "inst_id": specs.get("inst_id"),
        "tick_sz": specs.get("tick_sz"),
        "lot_sz": specs.get("lot_sz"),
        "min_sz": specs.get("min_sz"),
        "ct_val": specs.get("ct_val"),
        "ct_mult": specs.get("ct_mult"),
        "sample_quantized_contracts_150usd": sample_quantization,
        "raw_specs": specs
    }
