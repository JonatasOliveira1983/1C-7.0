# -*- coding: utf-8 -*-
"""
1CRYPTEN — OKX Market Universe & Universal Instrument Catalog (V155)
===================================================================
Mapeamento universal, dinâmico e exato de 100% dos pares perpétuos da OKX (USDT-SWAP).
Fornece à Laya Soberana e ao Cockpit:
1. Catálogo oficial de contratos (ctVal, tickSize, lotSize, minSz, alavancagem máxima).
2. Telemetria de preços de mercado em tempo real (last, high24h, low24h, volume 24h).
3. Seleção autônoma dos pares com maior liquidez e volatilidade institucional.
"""
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional
import httpx

logger = logging.getLogger("OKXUniverseService")


class OKXUniverseService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(OKXUniverseService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._instruments_cache: Dict[str, Dict[str, Any]] = {}  # instId -> specs
        self._pair_to_inst_id: Dict[str, str] = {}               # BTCUSDT -> BTC-USDT-SWAP
        self._tickers_cache: Dict[str, Dict[str, Any]] = {}      # instId -> ticker data
        self._last_instruments_ts: float = 0.0
        self._last_tickers_ts: float = 0.0
        self._lock = asyncio.Lock()
        
        # [V158] Cesta Canônica de 50 Ativos de Elite Institucional da OKX (Zero Memecoins, Zero Pó)
        self._core_assets = [
            # 1. Layer 1 Consagradas & Bluechips (15)
            "ETH-USDT-SWAP", "SOL-USDT-SWAP", "AVAX-USDT-SWAP", "SUI-USDT-SWAP", "NEAR-USDT-SWAP",
            "ADA-USDT-SWAP", "XRP-USDT-SWAP", "DOT-USDT-SWAP", "APT-USDT-SWAP", "SEI-USDT-SWAP",
            "HBAR-USDT-SWAP", "ALGO-USDT-SWAP", "TON-USDT-SWAP", "ATOM-USDT-SWAP", "LTC-USDT-SWAP",
            # 2. Layer 2 & Infraestrutura de Execução (8)
            "ARB-USDT-SWAP", "OP-USDT-SWAP", "POL-USDT-SWAP", "XPL-USDT-SWAP", "MNT-USDT-SWAP",
            "METIS-USDT-SWAP", "BLAST-USDT-SWAP", "ZK-USDT-SWAP",
            # 3. DeFi, Oráculos & Liquidez (12)
            "LINK-USDT-SWAP", "UNI-USDT-SWAP", "AAVE-USDT-SWAP", "MKR-USDT-SWAP", "SNX-USDT-SWAP",
            "CRV-USDT-SWAP", "LDO-USDT-SWAP", "PYTH-USDT-SWAP", "ONDO-USDT-SWAP", "INJ-USDT-SWAP",
            "PENDLE-USDT-SWAP", "DYDX-USDT-SWAP",
            # 4. Inteligência Artificial, DePIN & Big Data (10)
            "RENDER-USDT-SWAP", "FET-USDT-SWAP", "GRASS-USDT-SWAP", "FIL-USDT-SWAP", "TIA-USDT-SWAP",
            "ICP-USDT-SWAP", "AR-USDT-SWAP", "THETA-USDT-SWAP", "JASMY-USDT-SWAP", "AKT-USDT-SWAP",
            # 5. Gaming, Metaverso & Web3 Institucional (5)
            "SAND-USDT-SWAP", "MANA-USDT-SWAP", "AXS-USDT-SWAP", "GALA-USDT-SWAP", "CHZ-USDT-SWAP"
        ]

    @staticmethod
    def to_inst_id(symbol: str) -> str:
        """Converte qualquer formato (ex: BTCUSDT, BTC) para o instId canônico OKX (ex: BTC-USDT-SWAP)."""
        if not symbol:
            return ""
        s = symbol.strip().upper()
        if s.endswith(".P"):
            s = s[:-2]
        if s.endswith("-SWAP"):
            return s
        if "-" in s:
            parts = s.split("-")
            base = parts[0]
            quote = parts[1] if len(parts) > 1 else "USDT"
            return f"{base}-{quote}-SWAP"
        if s.endswith("USDT"):
            base = s[:-4]
            return f"{base}-USDT-SWAP"
        if s.endswith("USDC"):
            base = s[:-4]
            return f"{base}-USDC-SWAP"
        return f"{s}-USDT-SWAP"

    @staticmethod
    def to_clean_pair(symbol: str) -> str:
        """Converte qualquer formato para par limpo (ex: BTC-USDT-SWAP -> BTCUSDT)."""
        if not symbol:
            return ""
        s = symbol.strip().upper()
        if s.endswith(".P"):
            s = s[:-2]
        return s.replace("-USDT-SWAP", "USDT").replace("-USDC-SWAP", "USDC").replace("-SWAP", "").replace("-", "")

    async def sync_instruments(self, force: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Carrega ou atualiza em lote todos os instrumentos USDT-SWAP ativos na OKX.
        TTL de 3600 segundos (1 hora).
        """
        now = time.time()
        if not force and self._instruments_cache and (now - self._last_instruments_ts < 3600):
            return self._instruments_cache

        async with self._lock:
            # Dupla checagem sob lock
            if not force and self._instruments_cache and (now - self._last_instruments_ts < 3600):
                return self._instruments_cache

            endpoints = [
                "https://www.okx.com/api/v5/public/instruments?instType=SWAP",
                "https://aws.okx.com/api/v5/public/instruments?instType=SWAP"
            ]
            for url in endpoints:
                try:
                    async with httpx.AsyncClient(timeout=8.0) as client:
                        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (1Crypten Institutional Engine)"})
                        if resp.status_code == 200:
                            data = resp.json().get("data", [])
                            new_cache = {}
                            pair_map = {}
                            for item in data:
                                if item.get("state") != "live" or item.get("settleCcy") != "USDT":
                                    continue
                                inst_id = item.get("instId")
                                if not inst_id:
                                    continue
                                clean_pair = self.to_clean_pair(inst_id)
                                try:
                                    ct_val = float(item.get("ctVal", "1.0"))
                                except (ValueError, TypeError):
                                    ct_val = 1.0
                                try:
                                    tick_sz = float(item.get("tickSz", "0.001"))
                                except (ValueError, TypeError):
                                    tick_sz = 0.001
                                try:
                                    lot_sz = float(item.get("lotSz", "1.0"))
                                except (ValueError, TypeError):
                                    lot_sz = 1.0
                                try:
                                    min_sz = float(item.get("minSz", "1.0"))
                                except (ValueError, TypeError):
                                    min_sz = 1.0

                                spec = {
                                    "instId": inst_id,
                                    "pair": clean_pair,
                                    "ctVal": ct_val,
                                    "ctValCcy": item.get("ctValCcy", ""),
                                    "tickSize": tick_sz,
                                    "lotSize": lot_sz,
                                    "minSz": min_sz,
                                    "maxLeverage": float(item.get("lever", "15.0") or 15.0),
                                    "updated_at": now
                                }
                                new_cache[inst_id] = spec
                                pair_map[clean_pair] = inst_id

                            if new_cache:
                                self._instruments_cache = new_cache
                                self._pair_to_inst_id = pair_map
                                self._last_instruments_ts = now
                                logger.info(f"🌐 [OKX-UNIVERSE] Catálogo carregado com sucesso: {len(new_cache)} contratos USDT-SWAP mapeados.")
                                return self._instruments_cache
                except Exception as e:
                    logger.debug(f"[OKX-UNIVERSE] Falha ao carregar instrumentos de {url}: {e}")

        # Se falhou conexão externa e temos cache anterior, preserva
        return self._instruments_cache

    async def sync_tickers(self, force: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Atualiza todos os tickers de mercado da OKX em tempo real.
        TTL de 3.0 segundos.
        """
        now = time.time()
        if not force and self._tickers_cache and (now - self._last_tickers_ts < 3.0):
            return self._tickers_cache

        endpoints = [
            "https://www.okx.com/api/v5/market/tickers?instType=SWAP",
            "https://aws.okx.com/api/v5/market/tickers?instType=SWAP"
        ]
        for url in endpoints:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (1Crypten Ticker Poller)"})
                    if resp.status_code == 200:
                        data = resp.json().get("data", [])
                        new_tickers = {}
                        for item in data:
                            inst_id = item.get("instId", "")
                            if not inst_id.endswith("-USDT-SWAP"):
                                continue
                            try:
                                last_px = float(item.get("last", 0.0) or 0.0)
                                high_24 = float(item.get("high24h", 0.0) or last_px)
                                low_24 = float(item.get("low24h", 0.0) or last_px)
                                open_24 = float(item.get("open24h", 0.0) or item.get("sodUtc0", 0.0) or last_px)
                                vol_ccy = float(item.get("volCcy24h", 0.0) or 0.0)
                                chg_pct = ((last_px - open_24) / open_24 * 100.0) if open_24 > 0 else 0.0
                            except (ValueError, TypeError):
                                continue

                            new_tickers[inst_id] = {
                                "instId": inst_id,
                                "last": last_px,
                                "high24h": high_24,
                                "low24h": low_24,
                                "open24h": open_24,
                                "change24h_pct": round(chg_pct, 2),
                                "volume_24h_usd": round(vol_ccy, 2),
                                "ts": float(item.get("ts", now * 1000))
                            }

                        if new_tickers:
                            self._tickers_cache = new_tickers
                            self._last_tickers_ts = now
                            return self._tickers_cache
            except Exception as e:
                logger.debug(f"[OKX-UNIVERSE] Erro ao obter tickers de {url}: {e}")

        return self._tickers_cache

    def get_specs(self, symbol: str) -> Dict[str, Any]:
        """Retorna as especificações de contrato reais de qualquer moeda."""
        inst_id = self.to_inst_id(symbol)
        if inst_id in self._instruments_cache:
            return self._instruments_cache[inst_id]

        clean_pair = self.to_clean_pair(symbol)
        matched_id = self._pair_to_inst_id.get(clean_pair)
        if matched_id and matched_id in self._instruments_cache:
            return self._instruments_cache[matched_id]

        # Especificação padrão segura
        return {
            "instId": inst_id,
            "pair": clean_pair,
            "ctVal": 1.0,
            "ctValCcy": "",
            "tickSize": 0.001,
            "lotSize": 1.0,
            "minSz": 1.0,
            "maxLeverage": 15.0,
            "updated_at": 0
        }

    async def get_tradable_universe(self, limit: int = 50, min_volume_usd: float = 3_000_000.0) -> List[Dict[str, Any]]:
        """
        [V158] Retorna a cesta oficial de 50 ativos de elite institucional da OKX.
        Combina o catálogo oficial com os preços em tempo real, filtrando 100% das memecoins e tokens de pó.
        """
        await self.sync_instruments()
        await self.sync_tickers()

        universe = []
        # Adiciona primeiro os ativos core garantidos para nunca faltar dados dos pilares
        seen = set()
        for core_id in self._core_assets:
            if core_id in self._tickers_cache and core_id in self._instruments_cache:
                t = self._tickers_cache[core_id]
                s = self._instruments_cache[core_id]
                if t.get("last", 0.0) > 0:
                    seen.add(core_id)
                    universe.append({
                        "symbol": core_id,
                        "pair": s["pair"],
                        "clean_sym": s["pair"],
                        "price": t["last"],
                        "high_24h": t["high24h"],
                        "low_24h": t["low24h"],
                        "change_24h": t["change24h_pct"],
                        "volume_24h_usd": t["volume_24h_usd"],
                        "ctVal": s["ctVal"],
                        "tickSize": s["tickSize"],
                        "lotSize": s["lotSize"],
                        "minSz": s["minSz"],
                        "is_core": True
                    })

        # Adiciona os demais ativos com maior volume 24h apenas se forem institucionais
        other_tickers = [
            t for inst_id, t in self._tickers_cache.items()
            if inst_id not in seen and inst_id in self._instruments_cache and t.get("last", 0.0) > 0
        ]
        other_tickers.sort(key=lambda x: x.get("volume_24h_usd", 0.0), reverse=True)

        # Governança: Filtra Memecoins, BTC benchmark, tokens de pó e derivativos de ações/commodities
        FORBIDDEN_BASE = {
            "BTC", "DOGE", "SHIB", "PEPE", "FLOKI", "BONK", "WIF", "MEME", "BOME", "NEIRO", "PUMP", "LUNA", "USTC",
            "PENGU", "TRUTH", "WAL", "TURBO", "BRETT", "POPCAT", "MOG", "CAT", "FARTCOIN", "USELESS", "CASHCAT",
            "MUBARAK", "TRUMP", "WLFI", "RSR", "ONE", "RVN", "STRK",
            "NVDA", "AAPL", "TSLA", "MSFT", "AMZN", "GOOG", "META", "XAU", "XAG", "XCU", "CL", "BRENT", "NG", "MRVL", "SPCX", "DJI", "SPX", "NDX", "QQQ"
        }

        for t in other_tickers:
            if len(universe) >= limit:
                break
            inst_id = t["instId"]
            base_coin = inst_id.split("-")[0].upper()
            if base_coin in FORBIDDEN_BASE or "SATS" in base_coin or t.get("last", 0.0) < 0.05:
                continue

            s = self._instruments_cache[inst_id]
            if t.get("volume_24h_usd", 0.0) < min_volume_usd:
                continue
            universe.append({
                "symbol": inst_id,
                "pair": s["pair"],
                "clean_sym": s["pair"],
                "price": t["last"],
                "high_24h": t["high24h"],
                "low_24h": t["low24h"],
                "change_24h": t["change24h_pct"],
                "volume_24h_usd": t["volume_24h_usd"],
                "ctVal": s["ctVal"],
                "tickSize": s["tickSize"],
                "lotSize": s["lotSize"],
                "minSz": s["minSz"],
                "is_core": False
            })

        # Ordena a cesta de ativos por volume e relevância de mercado
        universe.sort(key=lambda x: x.get("volume_24h_usd", 0.0), reverse=True)
        return universe[:limit]


okx_universe_service = OKXUniverseService()
