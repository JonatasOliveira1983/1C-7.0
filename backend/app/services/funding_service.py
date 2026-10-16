# -*- coding: utf-8 -*-
"""
OKX Funding Rate & Cashflow Service
Monitora em tempo real as taxas de financiamento da OKX para todos os pares em custódia.
Calcula o impacto financeiro exato (custo pago ou receita recebida) a cada ciclo de 8h e em 24h.
"""
import time
import asyncio
import logging
from typing import Dict, Any, List, Optional
import httpx

logger = logging.getLogger("1CRYPTEN-FUNDING")


class FundingService:
    def __init__(self):
        self._funding_cache: Dict[str, Dict[str, Any]] = {}  # { symbol: { rate, time, ts } }
        self._cache_ttl = 60.0  # 60 segundos de TTL para respeitar rate limits

    def _normalize_inst_id(self, symbol: str) -> str:
        """Converte qualquer símbolo para o formato oficial da OKX: EX: BTC-USDT-SWAP."""
        sym = str(symbol or "").upper().strip()
        if sym.endswith("-SWAP"):
            return sym
        clean = sym.replace("-", "").replace("USDT", "")
        return f"{clean}-USDT-SWAP"

    async def get_funding_rate_details(self, symbol: str) -> Dict[str, Any]:
        """
        Consulta taxa de financiamento atual da OKX e timestamp da próxima liquidação.
        Usa cache de 60s para resposta instantânea.
        """
        inst_id = self._normalize_inst_id(symbol)
        now = time.time()
        
        cached = self._funding_cache.get(inst_id)
        if cached and (now - cached.get("ts", 0)) < self._cache_ttl:
            return cached["data"]

        url = f"https://www.okx.com/api/v5/public/funding-rate?instId={inst_id}"
        fallback_urls = [
            url,
            f"https://aws.okx.com/api/v5/public/funding-rate?instId={inst_id}"
        ]

        rate = 0.0001  # Default 0.01%
        funding_time = int((now + 28800) * 1000)

        for u in fallback_urls:
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    resp = await client.get(u)
                    if resp.status_code == 200:
                        payload = resp.json()
                        data = payload.get("data", [])
                        if data:
                            row = data[0]
                            rate = float(row.get("fundingRate") or 0.0)
                            funding_time = int(row.get("fundingTime") or 0)
                            break
            except Exception as e:
                logger.debug(f"[FUNDING-FETCH] Erro ao consultar {inst_id} em {u}: {e}")

        res = {
            "symbol": inst_id,
            "funding_rate": rate,
            "funding_rate_pct": round(rate * 100.0, 4),
            "funding_time": funding_time,
            "next_funding_in_s": max(0, int((funding_time / 1000.0) - now)) if funding_time > 0 else 0
        }
        self._funding_cache[inst_id] = {"data": res, "ts": now}
        return res

    def calculate_position_funding(
        self,
        symbol: str,
        side: str,
        margin: float,
        leverage: float,
        rate_override: Optional[float] = None,
        funding_time_override: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Calcula o impacto financeiro do Funding Rate na posição:
        Nocional = Margem * Alavancagem
        Regra OKX:
        - Taxa positiva (> 0): Longs pagam Shorts.
          -> Se lado for LONG: paga taxa (- USD)
          -> Se lado for SHORT: recebe taxa (+ USD)
        - Taxa negativa (< 0): Shorts pagam Longs.
          -> Se lado for LONG: recebe taxa (+ USD)
          -> Se lado for SHORT: paga taxa (- USD)
        """
        inst_id = self._normalize_inst_id(symbol)
        now = time.time()

        if rate_override is not None:
            rate = float(rate_override)
            funding_time = funding_time_override or int((now + 28800) * 1000)
        else:
            cached = self._funding_cache.get(inst_id)
            if cached:
                rate = cached["data"]["funding_rate"]
                funding_time = cached["data"]["funding_time"]
            else:
                rate = 0.00005
                funding_time = int((now + 28800) * 1000)

        notional_usd = round(float(margin) * float(leverage), 2)
        side_norm = str(side or "LONG").upper().strip()
        is_long = side_norm in ("LONG", "BUY")

        # Custo por ciclo de 8h (valor com sinal: positivo = lucro/receita, negativo = custo/pagamento)
        if is_long:
            cost_per_cycle = -(notional_usd * rate)
        else:
            cost_per_cycle = +(notional_usd * rate)

        cost_per_cycle = round(cost_per_cycle, 2)
        cost_24h = round(cost_per_cycle * 3.0, 2)

        action = "RECEBE" if cost_per_cycle > 0 else ("PAGA" if cost_per_cycle < 0 else "NEUTRO")
        next_in_s = max(0, int((funding_time / 1000.0) - now)) if funding_time > 0 else 0

        # Formatação amigável de contagem regressiva HH:MM:SS
        hours = next_in_s // 3600
        mins = (next_in_s % 3600) // 60
        secs = next_in_s % 60
        countdown_str = f"{hours:02d}h {mins:02d}m {secs:02d}s"

        return {
            "symbol": inst_id,
            "side": "LONG" if is_long else "SHORT",
            "notional_usd": notional_usd,
            "funding_rate": rate,
            "funding_rate_pct": round(rate * 100.0, 4),
            "action": action,
            "cost_per_cycle_usd": cost_per_cycle,
            "cost_24h_usd": cost_24h,
            "funding_time": funding_time,
            "next_funding_in_s": next_in_s,
            "countdown_str": countdown_str
        }

    def calculate_fleet_funding_summary(self, slots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula o somatório de custos e receitas de financiamento para todas as posições ativas."""
        total_cycle = 0.0
        total_24h = 0.0
        paying_count = 0
        receiving_count = 0
        min_funding_time = 0
        now = time.time()

        for s in slots:
            sym = s.get("symbol")
            if not sym:
                continue
            side = s.get("direction") or s.get("side") or "LONG"
            margin = float(s.get("entry_margin") or (s.get("contract_meta") or {}).get("margin") or 200.0)
            leverage = float(s.get("leverage") or (s.get("contract_meta") or {}).get("leverage") or 15.0)
            
            rate_override = s.get("funding_rate")
            time_override = s.get("funding_time")

            res = self.calculate_position_funding(
                symbol=sym,
                side=side,
                margin=margin,
                leverage=leverage,
                rate_override=rate_override,
                funding_time_override=time_override
            )

            total_cycle += res["cost_per_cycle_usd"]
            total_24h += res["cost_24h_usd"]
            if res["action"] == "RECEBE":
                receiving_count += 1
            elif res["action"] == "PAGA":
                paying_count += 1

            ftime = res["funding_time"]
            if ftime > 0 and (min_funding_time == 0 or ftime < min_funding_time):
                min_funding_time = ftime

        total_cycle = round(total_cycle, 2)
        total_24h = round(total_24h, 2)

        next_in_s = max(0, int((min_funding_time / 1000.0) - now)) if min_funding_time > 0 else 0
        hours = next_in_s // 3600
        mins = (next_in_s % 3600) // 60
        secs = next_in_s % 60
        countdown_str = f"{hours:02d}h {mins:02d}m {secs:02d}s"

        status = "RECEITA_PASSIVA" if total_cycle > 0 else ("CUSTO_FINANCIAMENTO" if total_cycle < 0 else "NEUTRO")

        return {
            "total_cost_per_cycle_usd": total_cycle,
            "total_cost_24h_usd": total_24h,
            "status": status,
            "paying_slots_count": paying_count,
            "receiving_slots_count": receiving_count,
            "active_positions_count": len(slots),
            "next_funding_time_ms": min_funding_time,
            "next_funding_in_s": next_in_s,
            "countdown_str": countdown_str
        }


funding_service = FundingService()
