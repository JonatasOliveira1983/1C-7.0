import logging
import sqlite3
import os
from typing import List, Dict, Any, Optional
import math
from services.backtest.sim_broker import SimBroker

logger = logging.getLogger("BacktestEngine")

class BacktestEngine:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.leverage = 50
        self.initial_balance = 100.0
        
    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def calc_adx(self, highs, lows, closes, period=14):
        """Calcula o ADX (Average Directional Index) simplificado para 14 períodos."""
        if len(closes) < period * 2:
            return [20.0] * len(closes)

        tr_list = []
        plus_dm_list = []
        minus_dm_list = []

        for i in range(1, len(closes)):
            tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
            tr_list.append(tr)
            
            high_diff = highs[i] - highs[i-1]
            low_diff = lows[i-1] - lows[i]
            
            plus_dm = high_diff if (high_diff > low_diff and high_diff > 0) else 0
            minus_dm = low_diff if (low_diff > high_diff and low_diff > 0) else 0
            
            plus_dm_list.append(plus_dm)
            minus_dm_list.append(minus_dm)

        # Suavização inicial
        atr = sum(tr_list[:period]) / period
        plus_di_smooth = sum(plus_dm_list[:period]) / period
        minus_di_smooth = sum(minus_dm_list[:period]) / period
        
        dx_list = []
        for i in range(period, len(tr_list)):
            atr = (atr * (period - 1) + tr_list[i]) / period
            plus_di_smooth = (plus_di_smooth * (period - 1) + plus_dm_list[i]) / period
            minus_di_smooth = (minus_di_smooth * (period - 1) + minus_dm_list[i]) / period
            
            pdi = (plus_di_smooth / atr) * 100 if atr > 0 else 0
            mdi = (minus_di_smooth / atr) * 100 if atr > 0 else 0
            
            dx = (abs(pdi - mdi) / (pdi + mdi)) * 100 if (pdi + mdi) > 0 else 0
            dx_list.append(dx)

        # Média do DX para ADX
        if not dx_list: return [20.0] * len(closes)
        
        adx = sum(dx_list[:period]) / period
        adx_series = [20.0] * (period * 2)
        
        for i in range(period, len(dx_list)):
            adx = (adx * (period - 1) + dx_list[i]) / period
            adx_series.append(adx)
            
        # Ajusta tamanho da série
        while len(adx_series) < len(closes):
            adx_series.append(adx_series[-1])
            
        return adx_series

    def calc_pivot_zones(self, highs, lows, closes, lookback=50):
        """V110.41: Calcula zonas de Suporte/Resistência usando Pivot Points clássicos."""
        if len(closes) < lookback:
            return []
        
        # Usa os últimos N candles para calcular os pivots
        recent_high = max(highs[-lookback:])
        recent_low = min(lows[-lookback:])
        recent_close = closes[-1]
        
        pp = (recent_high + recent_low + recent_close) / 3
        r1 = (2 * pp) - recent_low
        r2 = pp + (recent_high - recent_low)
        s1 = (2 * pp) - recent_high
        s2 = pp - (recent_high - recent_low)
        
        return [
            {"price": round(r2, 6), "label": "R2", "type": "resistance"},
            {"price": round(r1, 6), "label": "R1", "type": "resistance"},
            {"price": round(pp, 6), "label": "PP", "type": "pivot"},
            {"price": round(s1, 6), "label": "S1", "type": "support"},
            {"price": round(s2, 6), "label": "S2", "type": "support"},
        ]

    def simulate(self, symbol: str, interval: str, initial_balance=100.0, toggles=None):
        """Simula a estratégia Sniper nas klines filtradas do banco local."""
        if toggles is None:
            toggles = {"lateral_guillotine": True, "sentinel": False}

        try:
            conn = self.get_db_connection()
            c = conn.cursor()
            c.execute('''
                SELECT * FROM klines 
                WHERE symbol = ? AND interval = ? 
                ORDER BY start_time ASC
            ''', (symbol, interval))
            conn.row_factory = sqlite3.Row # [V110.63.5] Ativar antes de consumir os dados
            rows = c.fetchall()
            conn.close()
        except sqlite3.OperationalError as e:
            logger.error(f"Erro no banco de dados: {e}")
            return {"error": "Banco de dados não inicializado. Execute o download de klines primeiro."}
        except Exception as e:
            logger.error(f"Erro inesperado no simulador: {e}")
            return {"error": f"Erro interno: {e}"}

        if len(rows) < 50:
            return {"error": "Dados insuficientes para calcular indicadores (mínimo 50 klines)."}

        # Extrair séries de forma segura (Float Enforcement)
        try:
            highs = [float(row['high']) for row in rows]
            lows = [float(row['low']) for row in rows]
            closes = [float(row['close']) for row in rows]
            times = [int(row['start_time']) for row in rows]
        except Exception as e:
            logger.error(f"Erro na conversão de dados para float: {e}")
            return {"error": "Dados do banco de dados malformados."}

        # Indicadores
        adx_series = self.calc_adx(highs, lows, closes)
        
        # Variáveis de Estado (Migrando para SimBroker)
        broker = SimBroker(initial_balance=initial_balance)
        
        # [V2.0] Métricas de Inteligência
        opportunity_legs = [] # [{'time', 'side', 'potential_roi', 'reason', 'price'}]
        total_volatility = 0.0
        
        # V110.41: Equity Curve - rastrear evolução da banca
        equity_curve = [{"time": int(times[0] / 1000), "value": round(initial_balance, 2)}]
        
        # Loop de Simulação
        for i in range(1, len(rows)):
            current_close = closes[i]
            current_high = highs[i]
            current_low = lows[i]
            current_adx = adx_series[i]
            current_time = times[i]
            
            # --- 0. MÉTRICAS DE VOLATILIDADE & POTENCIAL ---
            prev_close = closes[i-1]
            candle_vol = (current_high - current_low) / prev_close * 100
            total_volatility += candle_vol
            
            # Detectar "Pernadas de Ouro" (Pelo menos 1% de movimento na kline = 50% ROI)
            if candle_vol >= 0.2:
                leg_side = "LONG" if current_close > prev_close else "SHORT"
                potential_roi = candle_vol * self.leverage
                
                # Se não temos ordens abertas, registramos como oportunidade
                if not broker.positions:
                    reason = "ADX_LOW" if current_adx < 28 else "NO_BREAKOUT"
                    if potential_roi >= 50.0:
                        opportunity_legs.append({
                            "time": current_time,
                            "side": leg_side,
                            "potential_roi": round(potential_roi, 2),
                            "reason": reason,
                            "price": current_close
                        })

            # --- 1. GESTÃO DE TRADE ABERTO (Via SimBroker) ---
            if symbol in broker.positions:
                broker.update(symbol, current_close, current_time)
                continue

            # --- 2. FILTRO DE ENTRADA (Guilhotina Lateral) ---
            adx_threshold = 28 # V110.30.0 Standard
            if toggles.get("lateral_guillotine") and current_adx < adx_threshold:
                continue

            # --- 3. LÓGICA DE ENTRADA (Sinal Sniper V1.1) ---
            # Requisitos: ADX subindo + Rompimento da vela anterior
            adx_rising = current_adx > adx_series[i-1]
            
            if adx_rising:
                prev_high = highs[i-1]
                prev_low = lows[i-1]
                
                if current_close > prev_high:
                    broker.open_position(symbol, "Long", current_close, current_time)
                elif current_close < prev_low:
                    broker.open_position(symbol, "Short", current_close, current_time)

            # V110.41: Rastrear equity a cada candle (balanço + valor de posições abertas)
            unrealized = 0.0
            if symbol in broker.positions:
                pos = broker.positions[symbol]
                if pos["side"] == "Long":
                    unrealized = pos["margin"] * (((current_close - pos["entry_price"]) / pos["entry_price"]) * broker.leverage)
                else:
                    unrealized = pos["margin"] * (((pos["entry_price"] - current_close) / pos["entry_price"]) * broker.leverage)
            equity_curve.append({"time": int(current_time / 1000), "value": round(broker.balance + unrealized, 2)})

        # --- 4. CÁLCULO DE MÉTRICAS AVANÇADAS ---
        trades_history = broker.history
        winning_trades = [t for t in trades_history if t['pnl'] > 0]
        losing_trades = [t for t in trades_history if t['pnl'] <= 0]
        
        gross_profit = sum([t['pnl'] for t in winning_trades])
        gross_loss = abs(sum([t['pnl'] for t in losing_trades]))
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0)
        
        summary = broker.get_summary()
        avg_vol = total_volatility / len(rows) if rows else 0
        
        # Filtro de Insights (Ghost Strategy: Busca de Pernadas de 10% / Oportunidades Perdidas)
        ghost_insights = []
        for i in range(5, len(closes)):
            p_start = closes[i-3]
            p_end = closes[i]
            change = (p_end - p_start) / p_start * 100
            if change >= 2.0: # [V110.42] Pernada de 100% ROI Detectada (2% spread)
                ts_trigger = times[i-3]
                was_in_trade = any(t['entry_time'] <= ts_trigger <= (t.get('exit_time', 9999999999999)) for t in trades_history)
                if not was_in_trade:
                    ghost_insights.append({
                        "time": ts_trigger,
                        "side": "LONG",
                        "potential": round(change * self.leverage, 1),
                        "reason": "MOMENTUM_EXPLOSION",
                        "price": p_start
                    })

        # Formata Klines para a UI
        chart_klines = []
        dna_tags = []
        for i in range(len(rows)):
            k = {
                "time": int(times[i] / 1000), 
                "open": highs[i], # Simulação simplificada de OHLC se necessário
                "high": highs[i],
                "low": lows[i],
                "close": closes[i],
                "volume": 0.0,
                "adx": float(adx_series[i])
            }
            chart_klines.append(k)
            if k["adx"] > 40: dna_tags.append({"time": k["time"], "label": "TREND_MAX", "type": "DNA"})

        sr_zones = self.calc_pivot_zones(highs, lows, closes)

        # [V110.63.3] Blindagem Definitiva da Telemetria Tática
        tactical_events = []
        correlation_track = []
        correlation_avg = 0.85 # Default Seguro

        try:
            btc_klines = {}
            conn = self.get_db_connection()
            conn.row_factory = sqlite3.Row  # [V110.63.4] Suporte para acesso por nome de coluna
            c = conn.cursor()
            c.execute('SELECT start_time, close FROM klines WHERE symbol = "BTCUSDT" AND interval = ? ORDER BY start_time ASC', (interval,))
            btc_rows = c.fetchall()
            conn.close()
            
            # Converte explicitamente para float para evitar TypeError: str vs int
            btc_klines = {int(r['start_time']): float(r['close']) for r in btc_rows}

            if btc_klines:
                window = 20
                for i in range(window, len(times)):
                    t = times[i]
                    if t not in btc_klines: continue
                    
                    # Garantir que temos o BTC para todos os pontos da janela
                    asset_slice = closes[i-window:i]
                    btc_slice = []
                    valid_window = True
                    for j in range(i-window, i):
                        bt = times[j]
                        if bt in btc_klines:
                            btc_slice.append(btc_klines[bt])
                        else:
                            valid_window = False
                            break
                    
                    if not valid_window or len(btc_slice) < window: continue
                    
                    # Pearson math ultra-safe
                    try:
                        n = len(asset_slice)
                        ma = sum(asset_slice)/n
                        mb = sum(btc_slice)/n
                        num = sum((asset_slice[j]-ma)*(btc_slice[j]-mb) for j in range(n))
                        sum_sq_a = sum((asset_slice[j]-ma)**2 for j in range(n))
                        sum_sq_b = sum((btc_slice[j]-mb)**2 for j in range(n))
                        if sum_sq_a > 0.000001 and sum_sq_b > 0.000001:
                            den = math.sqrt(sum_sq_a * sum_sq_b)
                            corr = round(num/den, 4)
                            correlation_track.append({"time": int(t/1000), "value": corr})
                    except: pass

                    # Hedge Trigger Detection
                    if i > 3:
                        p1 = btc_klines.get(times[i-3], 0)
                        p2 = btc_klines.get(t, 0)
                        if p1 > 0 and (p2-p1)/p1 < -0.02:
                            tactical_events.append({"time": int(t/1000), "type": "HEDGE_ACTIVE", "label": "🛡️ HEDGE"})

                if correlation_track:
                    correlation_avg = round(sum(c['value'] for c in correlation_track)/len(correlation_track),4)
        except Exception as e:
            logger.error(f"Falha na telemetria tática (silenciada): {e}")

        return {
            "symbol": symbol,
            "interval": interval,
            "initial_balance": summary["initial_balance"],
            "final_balance": summary["final_balance"],
            "total_pnl": summary["total_pnl"],
            "total_pnl_pct": f"{summary['total_pnl_pct']}%",
            "win_rate": summary["win_rate"],
            "trades_count": summary["trades_count"],
            "profit_factor": profit_factor,
            "max_drawdown": f"{summary.get('max_drawdown', 0):.2f}%",
            "avg_candle_volatility": f"{avg_vol:.2f}%",
            "opportunity_legs": opportunity_legs[:20],
            "ghost_insights": ghost_insights[:10],
            "trades": trades_history,
            "klines": chart_klines,
            "dna_tags": dna_tags,
            "equity_curve": equity_curve,
            "support_resistance_zones": sr_zones,
            "tactical_intel": {
                "correlation_avg": correlation_avg,
                "correlation_track": correlation_track,
                "tactical_events": tactical_events,
                "sensor_biases": {
                    "macro_weight": 1.0,
                    "whale_weight": 1.1,
                    # [V110.63.6] Blindagem: Usar win_rate_raw float do SimBroker
                    "smc_weight": 0.5 if float(summary.get("win_rate_raw", 0)) < 40 else 1.0
                }
            }
        }


# Instância Global para o SQLite local
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
default_db = os.path.join(base_dir, "backtest_data.db")
backtest_engine = BacktestEngine(default_db)
