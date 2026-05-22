# -*- coding: utf-8 -*-
import logging
import time
from typing import List, Dict, Any, Optional

logger = logging.getLogger("SimBroker")

class SimBroker:
    """
    Simulador de Corretora (Bybit Clone) para o Intelligence Lab.
    Gerencia banca, posições, taxas e protocolo de execução Sniper.
    """
    def __init__(self, initial_balance: float = 100.0):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.max_slots = 4
        self.positions = {} # {symbol: {data}}
        self.history = []
        self.taker_fee_pct = 0.06 / 100 # 0.06% Bybit Taker Fee
        self.leverage = 50
        self.order_size_pct = 0.10 # 10% da banca por ordem
        self.total_fees_paid = 0.0

    def open_position(self, symbol: str, side: str, price: float, time_ms: int, tactical_score: int = 0):
        """Tenta abrir uma nova posição respeitando o limite de slots."""
        if len(self.positions) >= self.max_slots:
            # logger.warning(f"🚫 [SIM-BROKER] Rejeitado {symbol}: Slots esgotados ({self.max_slots}/4)")
            return False

        if symbol in self.positions:
            return False

        # Cálculo da margem (10% do balanço atual)
        margin = self.balance * self.order_size_pct
        if margin < 1.0: # Margem mínima de segurança
            return False

        # Aplica taxa de entrada
        entry_fee = (margin * self.leverage) * self.taker_fee_pct
        self.balance -= entry_fee
        self.total_fees_paid += entry_fee

        self.positions[symbol] = {
            "symbol": symbol,
            "side": side,
            "entry_price": price,
            "entry_time": time_ms,
            "margin": margin,
            "leverage": self.leverage,
            "sl_roi": -70.0, # Fase SAFE inicial
            "max_roi": 0.0,
            "status": "OPEN",
            "tactical_score": tactical_score,
            "last_check_roi": 0.0
        }
        
        # logger.info(f"✅ [SIM-BROKER] OPEN {side} {symbol} @ {price} | Margin: ${margin:.2f}")
        return True

    def update(self, symbol: str, current_price: float, time_ms: int):
        """Atualiza o estado da posição e verifica gatilhos de fechamento."""
        if symbol not in self.positions:
            return None

        pos = self.positions[symbol]
        entry = pos["entry_price"]
        side = pos["side"]
        
        # Cálculo de ROI (50x)
        if side == "Long":
            roi = ((current_price - entry) / entry) * self.leverage * 100
        else:
            roi = ((entry - current_price) / entry) * self.leverage * 100

        # Anti-Massacre (Paper Mode)
        if roi <= -100.0: roi = -100.0
        
        pos["max_roi"] = max(pos["max_roi"], roi)
        pos["last_check_roi"] = roi

        # ESCADINHA DE ELITE (V110.21.0 Protocol)
        # 150% -> SL 110%
        if pos["max_roi"] >= 150.0:
            target_sl = 110.0
        # 110% -> SL 80%
        elif pos["max_roi"] >= 110.0:
            target_sl = 80.0
        # 70% -> SL 5% (Risk Zero)
        elif pos["max_roi"] >= 70.0:
            target_sl = 5.0
        else:
            target_sl = pos["sl_roi"]

        if target_sl > pos["sl_roi"]:
            pos["sl_roi"] = target_sl

        # Verificação de Fechamento
        should_close = False
        reason = ""
        
        # Hard Stop (-80%)
        if roi <= -80.0:
            should_close = True
            reason = "HARD_STOP"
            final_roi = -80.0
        # Stop Loss / Profit Lock atingido
        elif roi <= pos["sl_roi"]:
            should_close = True
            reason = "STOP_LOSS" if pos["sl_roi"] < 0 else "PROFIT_LOCK"
            final_roi = pos["sl_roi"]

        if should_close:
            return self.close_position(symbol, current_price, time_ms, final_roi, reason)
            
        return None

    def close_position(self, symbol: str, price: float, time_ms: int, final_roi: float, reason: str):
        """Fecha a posição, aplica taxas e limpa o slot."""
        if symbol not in self.positions:
            return None

        pos = self.positions.pop(symbol)
        
        # Cálculo do PnL Real em $
        pnl_cash = pos["margin"] * (final_roi / 100)
        
        # Aplica taxa de saída
        exit_fee = (pos["margin"] * self.leverage) * self.taker_fee_pct
        self.balance += pnl_cash - exit_fee
        self.total_fees_paid += exit_fee

        trade_result = {
            "symbol": symbol,
            "side": pos["side"],
            "entry_price": pos["entry_price"],
            "exit_price": price,
            "entry_time": pos["entry_time"],
            "exit_time": time_ms,
            "roi": round(final_roi, 2),
            "pnl": round(pnl_cash - exit_fee, 2),
            "pnl_pct": round(final_roi, 2),  # V110.41: ROI % para tooltips do Eagle Vision
            "fee": round(pos["margin"] * self.leverage * self.taker_fee_pct * 2, 4), # Total entry+exit
            "reason": reason,
            "max_roi": round(pos["max_roi"], 2),
            "duration_ms": time_ms - pos["entry_time"]  # V110.41: Duração para tooltips
        }
        
        self.history.append(trade_result)
        # logger.info(f"🛑 [SIM-BROKER] CLOSE {symbol} | ROI: {final_roi:.1f}% | PnL: ${trade_result['pnl']:.2f} | Reason: {reason}")
        return trade_result

    def get_summary(self):
        """Retorna o resumo da performance da banca."""
        total_pnl = self.balance - self.initial_balance
        wins = [t for t in self.history if t["pnl"] > 0]
        win_rate = (len(wins) / len(self.history) * 100) if self.history else 0
        
        return {
            "initial_balance": round(self.initial_balance, 2),
            "final_balance": round(self.balance, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round((total_pnl / self.initial_balance) * 100, 2),
            "trades_count": len(self.history),
            "win_rate": f"{win_rate:.1f}%",
            "win_rate_raw": float(win_rate), # [V110.63.6] Para uso tático sem string-parsing
            "total_fees": round(self.total_fees_paid, 2)
        }
