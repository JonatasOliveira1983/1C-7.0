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
import math
import asyncio
import logging
from decimal import Decimal, ROUND_HALF_UP
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
        
        # [V195] Cesta Canônica Soberana dos 30 Titãs de Elite 50x da OKX (Zero BTC para trade)
        self._titans_30_altcoins = [
            "SUI-USDT-SWAP", "SOL-USDT-SWAP", "ETH-USDT-SWAP", "XRP-USDT-SWAP", "NEAR-USDT-SWAP",
            "AVAX-USDT-SWAP", "APT-USDT-SWAP", "LINK-USDT-SWAP", "ARB-USDT-SWAP", "OP-USDT-SWAP",
            "INJ-USDT-SWAP", "TIA-USDT-SWAP", "SEI-USDT-SWAP", "AAVE-USDT-SWAP", "DOT-USDT-SWAP",
            "ADA-USDT-SWAP", "ENA-USDT-SWAP", "WLD-USDT-SWAP", "PENDLE-USDT-SWAP", "LTC-USDT-SWAP",
            "BCH-USDT-SWAP", "UNI-USDT-SWAP", "ATOM-USDT-SWAP", "FIL-USDT-SWAP", "CRV-USDT-SWAP",
            "SAND-USDT-SWAP", "HBAR-USDT-SWAP", "XLM-USDT-SWAP", "XPL-USDT-SWAP", "ZK-USDT-SWAP"
        ]

        # [V160] Cesta Canônica Imutável dos 10 Titãs de Elite Institucional da OKX
        self._titans_10 = [
            "BTC-USDT-SWAP", "ETH-USDT-SWAP", "SOL-USDT-SWAP", "NEAR-USDT-SWAP", "ZK-USDT-SWAP",
            "XRP-USDT-SWAP", "DOGE-USDT-SWAP", "SUI-USDT-SWAP", "LINK-USDT-SWAP", "XPL-USDT-SWAP"
        ]
        
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
                                vol_usd = (vol_ccy * last_px) if last_px > 0 else vol_ccy
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
                                "volume_24h_usd": round(vol_usd, 2),
                                "vol_ccy_24h": round(vol_ccy, 2),
                                "ts": float(item.get("ts", now * 1000))
                            }

                        if new_tickers:
                            self._tickers_cache = new_tickers
                            self._last_tickers_ts = now
                            return self._tickers_cache
            except Exception as e:
                logger.debug(f"[OKX-UNIVERSE] Erro ao obter tickers de {url}: {e}")

        return self._tickers_cache

    def get_max_leverage(self, symbol: str) -> float:
        """[V187.2] Retorna a alavancagem maxima real que a OKX autoriza para o contrato."""
        specs = self.get_specs(symbol)
        lev = float(specs.get("maxLeverage", 0.0) or 0.0)
        if lev > 0:
            return lev
        clean = symbol.upper().replace("-USDT-SWAP", "").replace("USDT", "")
        if clean in ("BTC", "ETH", "SOL", "XRP", "SUI", "AVAX"):
            return 100.0
        elif clean in ("DOGE", "PEPE", "SHIB", "ADA", "LINK", "NEAR", "APT"):
            return 50.0
        return 50.0

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
            "maxLeverage": 50.0,
            "updated_at": 0
        }

    def get_asset_dossier_sync(self, symbol: str) -> Dict[str, Any]:
        """
        [DOSSIÊ DO ATIVO OKX - SÍNCRONO]
        Retorna especificações de contrato em memória sem requisições HTTP adicionais.
        """
        inst_id = self.to_inst_id(symbol)
        clean = self.to_clean_pair(symbol)
        specs = self.get_specs(inst_id)
        base = inst_id.split("-")[0].upper()
        leverage = 30.0 if base in ("BTC", "ETH") else 15.0

        return {
            "symbol": inst_id,
            "pair": clean,
            "clean_sym": clean,
            "base_coin": base,
            "ctVal": specs.get("ctVal", 1.0),
            "tickSize": specs.get("tickSize", 0.0001),
            "lotSize": specs.get("lotSize", 1.0),
            "minSz": specs.get("minSz", 1.0),
            "leverage": leverage,
            "is_titan": inst_id in self._titans_30_altcoins or inst_id in self._titans_10
        }

    async def get_asset_dossier(self, symbol: str) -> Dict[str, Any]:
        """
        [DOSSIÊ DO ATIVO OKX - ENCRYPTOS SSOT]
        Retorna as especificações de contrato oficiais da OKX, regras de lote, precisão
        de tick e alavancagem calibrada para o par (15x nas altcoins, até 30x no BTC/ETH).
        """
        await self.sync_instruments()
        return self.get_asset_dossier_sync(symbol)

    @staticmethod
    def format_price_by_tick_custom(price: float, tick_size: float) -> float:
        """
        [PRECISION ENGINE CANÔNICO OKX]
        Normaliza o preço para o tickSize oficial do contrato (ex: 0.1 para BTC, 0.00000001 para PEPE).
        Previne erros de tick inválido e arredondamentos destrutivos em micro-caps.
        """
        if price <= 0:
            return price
        if not tick_size or tick_size <= 0:
            tick_size = 0.0001

        try:
            tick_str = f"{tick_size:.10f}".rstrip("0")
            if tick_str.endswith("."):
                tick_str += "0"
            tick_dec = Decimal(tick_str)
            price_dec = Decimal(str(price))
            rounded = (price_dec / tick_dec).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * tick_dec
            return float(rounded)
        except Exception:
            steps = round(price / tick_size)
            decimals = max(0, -int(math.floor(math.log10(tick_size)))) if tick_size < 1.0 else 1
            return round(steps * tick_size, decimals)

    def format_price_by_tick(self, symbol: str, price: float) -> float:
        """Formata o preço baseado no tickSize oficial do par nos 507 contratos OKX."""
        specs = self.get_specs(symbol)
        tick_sz = float(specs.get("tickSize", 0.0001))
        return self.format_price_by_tick_custom(price, tick_sz)

    def format_price_str(self, symbol: str, price: float) -> str:
        """Retorna representação string com o número correto de casas decimais."""
        specs = self.get_specs(symbol)
        tick_sz = float(specs.get("tickSize", 0.0001))
        decimals = max(0, -int(math.floor(math.log10(tick_sz)))) if tick_sz < 1.0 else 0
        norm_p = self.format_price_by_tick_custom(price, tick_sz)
        return f"{norm_p:.{decimals}f}"

    @staticmethod
    def quantize_order_contracts_custom(
        margin_usd: float,
        leverage: float,
        price: float,
        ct_val: float,
        lot_sz: float,
        min_sz: float,
        tick_sz: float
    ) -> Dict[str, Any]:
        """
        [QUANTIZADOR DE CONTRATOS OKX]
        Calcula o número de contratos válidos (sz) para a ordem:
        - Aplica ctVal (multiplicador do contrato)
        - Alinha com lotSz (passo de lote de contratos)
        - Valida minSz (tamanho mínimo exigido pela OKX)
        """
        if price <= 0 or ct_val <= 0 or margin_usd <= 0 or leverage <= 0:
            return {
                "contracts": 0.0,
                "notional_usd": 0.0,
                "effective_margin": 0.0,
                "is_valid": False,
                "error": "INVALID_INPUTS"
            }

        notional_target = margin_usd * leverage
        contract_cost_usd = price * ct_val

        if contract_cost_usd <= 0:
            return {
                "contracts": 0.0,
                "notional_usd": 0.0,
                "effective_margin": 0.0,
                "is_valid": False,
                "error": "INVALID_CONTRACT_COST"
            }

        raw_contracts = notional_target / contract_cost_usd

        if lot_sz <= 0:
            lot_sz = 1.0

        contract_steps = round(raw_contracts / lot_sz)
        contracts = round(contract_steps * lot_sz, 6)

        effective_notional = round(contracts * contract_cost_usd, 2)
        effective_margin = round(effective_notional / leverage, 2) if leverage > 0 else 0.0

        is_valid = contracts >= min_sz and contracts > 0

        if effective_margin > (margin_usd * 1.5):
            is_valid = False
            error = "MARGIN_OVERFLOW"
        elif contracts < min_sz:
            is_valid = False
            error = "BELOW_MIN_SIZE"
        else:
            error = None

        return {
            "contracts": contracts,
            "notional_usd": effective_notional,
            "effective_margin": effective_margin,
            "ctVal": ct_val,
            "lotSize": lot_sz,
            "minSz": min_sz,
            "tickSize": tick_sz,
            "is_valid": is_valid,
            "error": error
        }

    def quantize_order_contracts(
        self,
        symbol: str,
        margin_usd: float,
        leverage: float,
        price: float
    ) -> Dict[str, Any]:
        """Calcula contratos válidos para qualquer par do catálogo de 507 ativos."""
        specs = self.get_specs(symbol)
        ct_val = float(specs.get("ctVal", 1.0))
        lot_sz = float(specs.get("lotSize", 1.0))
        min_sz = float(specs.get("minSz", 1.0))
        tick_sz = float(specs.get("tickSize", 0.0001))
        return self.quantize_order_contracts_custom(
            margin_usd=margin_usd,
            leverage=leverage,
            price=price,
            ct_val=ct_val,
            lot_sz=lot_sz,
            min_sz=min_sz,
            tick_sz=tick_sz
        )

    async def get_institutional_universe(
        self,
        limit: int = 30,
        min_volume_usd: float = 15_000_000.0,
        min_price: float = 0.01,
        exclude_btc: bool = True
    ) -> List[Dict[str, Any]]:
        """
        [V178] UNIVERSO INSTITUCIONAL DE ELITE (507 PARES OKX):
        Fonte ÚNICA de verdade para Cockpit, Laya 360 e Motor Autônomo.
        - Filtro 1: Volume real 24h >= $15M USD (apenas ativos de alta liquidez institucional)
        - Filtro 2: Preço mínimo >= $0.01 (veto a satoshis e memecoins de microcentavos como PUMP)
        - Filtro 3: Governança estrita anti-memecoins, ações e commodities sintéticas
        - Ordenação: Maior Volume Institucional 24h com desempate por amplitude direcional (|change_24h|)
        """
        now = time.time()
        if hasattr(self, "_inst_univ_cache") and self._inst_univ_cache and (now - getattr(self, "_last_inst_univ_ts", 0.0) < 15.0):
            return self._inst_univ_cache[:limit]

        await self.sync_instruments()
        await self.sync_tickers()

        FORBIDDEN_BASE = {
            "BTC", "DOGE", "SHIB", "PEPE", "FLOKI", "BONK", "WIF", "MEME", "BOME", "NEIRO", "PUMP", "LUNA", "USTC",
            "PENGU", "TRUTH", "WAL", "TURBO", "BRETT", "POPCAT", "MOG", "CAT", "FARTCOIN", "USELESS", "CASHCAT",
            "MUBARAK", "TRUMP", "WLFI", "RSR", "ONE", "RVN", "STRK",
            "NVDA", "AAPL", "TSLA", "MSFT", "AMZN", "GOOG", "META", "XAU", "XAG", "XCU", "CL", "BRENT", "NG", "MRVL", "SPCX", "DJI", "SPX", "NDX", "QQQ"
        }

        candidates = []
        for inst_id, t in self._tickers_cache.items():
            if not inst_id.endswith("-USDT-SWAP"):
                continue
            if exclude_btc and inst_id.startswith("BTC"):
                continue
            base = inst_id.split("-")[0].upper()
            if base in FORBIDDEN_BASE or "SATS" in base:
                continue

            last_px = float(t.get("last", 0.0) or 0.0)
            if last_px < min_price:
                continue

            vol_usd = float(t.get("volume_24h_usd", 0.0) or t.get("volCcy24h", 0.0) or 0.0)
            if vol_usd < min_volume_usd:
                continue

            s = self._instruments_cache.get(inst_id)
            pair_name = s["pair"] if s else inst_id.replace("-USDT-SWAP", "USDT")
            chg = float(t.get("change24h_pct", 0.0) or t.get("change_24h", 0.0) or 0.0)

            candidates.append({
                "symbol": inst_id,
                "pair": pair_name,
                "clean_sym": pair_name,
                "price": last_px,
                "high_24h": float(t.get("high24h", last_px) or last_px),
                "low_24h": float(t.get("low24h", last_px) or last_px),
                "change_24h": round(chg, 2),
                "volume_24h_usd": vol_usd,
                "ctVal": s.get("ctVal", 1.0) if s else 1.0,
                "tickSize": s.get("tickSize", 0.0001) if s else 0.0001,
                "lotSize": s.get("lotSize", 1.0) if s else 1.0,
                "minSz": s.get("minSz", 1.0) if s else 1.0,
                "is_core": True,
                "is_institutional": True
            })

        # Ordena por Volume Institucional Real em USD com desempate por amplitude
        candidates.sort(key=lambda x: (x["volume_24h_usd"], abs(x["change_24h"])), reverse=True)

        # Garante preenchimento com a cesta dos 30 Titãs 50x se necessário
        if len(candidates) < limit:
            seen_symbols = {c["symbol"] for c in candidates}
            for titan_sym in self._titans_30_altcoins:
                if titan_sym not in seen_symbols and len(candidates) < limit:
                    s = self._instruments_cache.get(titan_sym)
                    t = self._tickers_cache.get(titan_sym, {})
                    last_px = float(t.get("last", 0.0) or 1.0)
                    pair_name = s["pair"] if s else titan_sym.replace("-USDT-SWAP", "USDT")
                    chg = float(t.get("change24h_pct", 0.0) or 0.0)
                    candidates.append({
                        "symbol": titan_sym,
                        "pair": pair_name,
                        "clean_sym": pair_name,
                        "price": last_px,
                        "high_24h": float(t.get("high24h", last_px) or last_px),
                        "low_24h": float(t.get("low24h", last_px) or last_px),
                        "change_24h": round(chg, 2),
                        "volume_24h_usd": float(t.get("volume_24h_usd", 50_000_000.0) or 50_000_000.0),
                        "ctVal": s.get("ctVal", 1.0) if s else 1.0,
                        "tickSize": s.get("tickSize", 0.0001) if s else 0.0001,
                        "lotSize": s.get("lotSize", 1.0) if s else 1.0,
                        "minSz": s.get("minSz", 1.0) if s else 1.0,
                        "is_core": True,
                        "is_institutional": True
                    })
                    seen_symbols.add(titan_sym)

        self._inst_univ_cache = candidates
        self._last_inst_univ_ts = now
        return candidates[:limit]

    async def get_tradable_universe(
        self,
        limit: int = 30,
        min_volume_usd: float = 15_000_000.0,
        exclude_btc: bool = True
    ) -> List[Dict[str, Any]]:
        """Retorna a cesta canônica dos 30 Titãs com specs e tickers atualizados."""
        await self.sync_instruments()
        await self.sync_tickers()
        out = []
        for sym in self._titans_30_altcoins[:limit]:
            if exclude_btc and sym.startswith("BTC"):
                continue
            s = self._instruments_cache.get(sym, {})
            t = self._tickers_cache.get(sym, {})
            last_px = float(t.get("last", 0.0) or 1.0)
            pair_name = s.get("pair") or sym.replace("-USDT-SWAP", "USDT")
            out.append({
                "symbol": sym,
                "pair": pair_name,
                "clean_sym": pair_name,
                "price": last_px,
                "high_24h": float(t.get("high24h", last_px) or last_px),
                "low_24h": float(t.get("low24h", last_px) or last_px),
                "change_24h": round(float(t.get("change24h_pct", 0.0) or 0.0), 2),
                "volume_24h_usd": float(t.get("volume_24h_usd", 50_000_000.0) or 50_000_000.0),
                "ctVal": s.get("ctVal", 1.0) if s else 1.0,
                "tickSize": s.get("tickSize", 0.0001) if s else 0.0001,
                "lotSize": s.get("lotSize", 1.0) if s else 1.0,
                "minSz": s.get("minSz", 1.0) if s else 1.0,
                "is_core": True,
                "is_institutional": True
            })
        return out


okx_universe_service = OKXUniverseService()


def format_price_by_tick(price: float, symbol: str) -> float:
    """Helper funcional para formatar preço de acordo com o tickSize do par."""
    return okx_universe_service.format_price_by_tick(symbol, price)


def quantize_order_contracts(
    margin_usd: float,
    price: float,
    symbol: str,
    leverage: float = 15.0
) -> Dict[str, Any]:
    """Helper funcional para quantizar contratos baseado em margin_usd, price, leverage e ctVal."""
    return okx_universe_service.quantize_order_contracts(symbol, margin_usd, leverage, price)
