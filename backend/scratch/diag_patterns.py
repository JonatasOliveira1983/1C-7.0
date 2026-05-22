import sqlite3
import pandas as pd
import os
import math
from typing import List, Dict, Tuple

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backtest_data.db")
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diag_patterns_res.txt")

# --- MOLA ---
def detect_mola_events(df):
    events = []
    if len(df) < 100: return events
    closes = df['close'].tolist()
    def get_std_dev(data):
        if not data: return 0
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        return math.sqrt(variance)
    for i in range(100, len(df)):
        short = closes[i-20:i]
        long = closes[i-100:i]
        std_short = get_std_dev(short)
        std_long = get_std_dev(long)
        if std_long > 0:
            compression = std_short / std_long
            if compression < 0.4:
                events.append({
                    "timestamp": df.index[i].timestamp() if hasattr(df.index[i], 'timestamp') else df.index[i],
                    "compression": round(compression, 3),
                    "price": closes[i]
                })
    return events

# --- 1-2-3 ---
def detect_123_pattern_pure(klines, find_all=True):
    if not klines or len(klines) < 15:
        return []
    
    try:
        c = klines[::-1] if isinstance(klines[0], (list, tuple)) else klines
    except (IndexError, TypeError):
        c = klines
    
    highs = []
    lows = []
    for x in c:
        try:
            highs.append(float(x[2]))
            lows.append(float(x[3]))
        except (IndexError, ValueError, TypeError):
            continue

    if len(lows) < 15: return []
    
    detected_patterns = []
    for i in range(15, len(lows) - 5):
        # --- LONG SCAN ---
        if lows[i] == min(lows[i-12:i+4]):
            p2_low = lows[i]
            p2_idx = i
            search_p1 = lows[max(0, p2_idx-15):p2_idx]
            if search_p1:
                p1_low = min(search_p1)
                p1_idx = max(0, p2_idx-15) + search_p1.index(p1_low)
                if p2_low < p1_low:
                    search_p3 = lows[p2_idx+1:p2_idx+12]
                    if search_p3:
                        p3_low = min(search_p3)
                        p3_idx = p2_idx + 1 + search_p3.index(p3_low)
                        if p3_low > p2_low:
                            trigger_price = max(highs[p2_idx:p3_idx+1])
                            detected_patterns.append({
                                "detected": True, "side": "buy",
                                "points": {"1": {"idx": p1_idx, "price": p1_low}, "2": {"idx": p2_idx, "price": p2_low}, "3": {"idx": p3_idx, "price": p3_low}},
                                "trigger_price": trigger_price
                            })
        # --- SHORT SCAN ---
        if highs[i] == max(highs[i-12:i+4]):
            p2_high = highs[i]
            p2_idx = i
            search_p1_h = highs[max(0, p2_idx-15):p2_idx]
            if search_p1_h:
                p1_high = max(search_p1_h)
                p1_idx = max(0, p2_idx-15) + search_p1_h.index(p1_high)
                if p2_high > p1_high:
                    search_p3_h = highs[p2_idx+1:p2_idx+12]
                    if search_p3_h:
                        p3_high = max(search_p3_h)
                        p3_idx = p2_idx + 1 + search_p3_h.index(p3_high)
                        if p3_high < p2_high:
                            trigger_price = min(lows[p2_idx:p3_idx+1])
                            detected_patterns.append({
                                "detected": True, "side": "sell",
                                "points": {"1": {"idx": p1_idx, "price": p1_high}, "2": {"idx": p2_idx, "price": p2_high}, "3": {"idx": p3_idx, "price": p3_high}},
                                "trigger_price": trigger_price
                            })
    return detected_patterns


# --- ABCD ---
class HarmonicABCDStrategy:
    def __init__(self, pivot_strength=2, rsi_period=14, ma_period=21):
        self.pivot_strength = pivot_strength
        self.rsi_period = rsi_period
        self.ma_period = ma_period

    def calculate_sma(self, closes: List[float], period: int) -> List[float]:
        if len(closes) < period:
            return [0.0] * len(closes)
        sma = [0.0] * (period - 1)
        for i in range(period - 1, len(closes)):
            avg = sum(closes[i - period + 1 : i + 1]) / period
            sma.append(avg)
        return sma

    def calculate_rsi(self, closes: List[float], period: int = 14) -> List[float]:
        if len(closes) < period + 1:
            return [0.0] * len(closes)
        rsi = [0.0] * len(closes)
        gains = []
        losses = []
        for i in range(1, len(closes)):
            change = closes[i] - closes[i - 1]
            gains.append(max(0, change))
            losses.append(max(0, -change))
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        if avg_loss == 0:
            rsi[period] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi[period] = 100.0 - (100.0 / (1.0 + rs))
        for i in range(period + 1, len(closes)):
            change = closes[i] - closes[i - 1]
            gain = max(0, change)
            loss = max(0, -change)
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period
            if avg_loss == 0:
                rsi[i] = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi[i] = 100.0 - (100.0 / (1.0 + rs))
        return rsi

    def find_pivots(self, highs: List[float], lows: List[float]) -> Tuple[List[Dict], List[Dict]]:
        pivot_highs = []
        pivot_lows = []
        strength = self.pivot_strength
        for i in range(strength, len(highs) - strength):
            is_high = True
            for j in range(1, strength + 1):
                if highs[i] <= highs[i - j] or highs[i] <= highs[i + j]:
                    is_high = False
                    break
            if is_high:
                pivot_highs.append({'index': i, 'val': highs[i]})
            is_low = True
            for j in range(1, strength + 1):
                if lows[i] >= lows[i - j] or lows[i] >= lows[i + j]:
                    is_low = False
                    break
            if is_low:
                pivot_lows.append({'index': i, 'val': lows[i]})
        return pivot_highs, pivot_lows

    def find_all_patterns(self, candles: List[List]) -> List[dict]:
        if len(candles) < self.ma_period + 10:
            return []
        all_patterns = []
        closes = [float(c[4]) for c in candles]
        highs = [float(c[2]) for c in candles]
        lows = [float(c[3]) for c in candles]
        pivot_highs, pivot_lows = self.find_pivots(highs, lows)
        if len(pivot_highs) < 2 or len(pivot_lows) < 2:
            return []
        rsi = self.calculate_rsi(closes, self.rsi_period)
        for i in range(30, len(candles)):
            if i < self.ma_period: continue
            if lows[i] > min(lows[i-3:i+1]): continue
            relevant_highs = [p for p in pivot_highs if p['index'] < i - 1]
            relevant_lows = [p for p in pivot_lows if p['index'] < i - 1]
            if len(relevant_highs) < 2 or len(relevant_lows) < 1:
                continue
            found_for_i = False
            for pt_c in reversed(relevant_highs[-3:]):
                if found_for_i: break
                for pt_b in reversed(relevant_lows[-3:]):
                    if found_for_i: break
                    if pt_b['index'] >= pt_c['index']: continue
                    for pt_a in reversed(relevant_highs):
                        if pt_a['index'] >= pt_b['index']: continue
                        if pt_a['index'] < pt_c['index'] - 60: break
                        lows_segment = lows[pt_c['index']+1 : i+1]
                        if not lows_segment: continue
                        min_low_val = min(lows_segment)
                        d_idx = pt_c['index'] + 1 + lows_segment.index(min_low_val)
                        pt_d = {'index': d_idx, 'val': min_low_val}
                        if pt_d['val'] >= pt_b['val']: continue
                        if pt_c['val'] >= pt_a['val']: continue
                        ab_amp = pt_a['val'] - pt_b['val']
                        cd_amp = pt_c['val'] - pt_d['val']
                        if ab_amp <= 0: continue
                        ratio = cd_amp / ab_amp
                        if not (0.75 <= ratio <= 1.25): continue
                        if rsi[pt_d['index']] <= rsi[pt_b['index']]: continue
                        if any(p['points']['D']['index'] == pt_d['index'] for p in all_patterns):
                            found_for_i = True
                            break
                        all_patterns.append({
                            "time": int(candles[pt_d['index']][0] / 1000),
                            "side": "buy",
                            "points": {
                                "A": {"index": pt_a['index'], "val": pt_a['val'], "time": int(candles[pt_a['index']][0] / 1000)},
                                "B": {"index": pt_b['index'], "val": pt_b['val'], "time": int(candles[pt_b['index']][0] / 1000)},
                                "C": {"index": pt_c['index'], "val": pt_c['val'], "time": int(candles[pt_c['index']][0] / 1000)},
                                "D": {"index": pt_d['index'], "val": pt_d['val'], "time": int(candles[pt_d['index']][0] / 1000)}
                            },
                            "ratio": round(ratio, 2),
                            "rsi_b": round(rsi[pt_b['index']], 2),
                            "rsi_d": round(rsi[pt_d['index']], 2)
                        })
                        found_for_i = True
                        break
        return all_patterns

strategy_n = HarmonicABCDStrategy()


def test_symbol(symbol, interval="30", limit=600):
    lines = []
    lines.append(f"\n=== ANALISANDO {symbol} ({interval}) ===")
    
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT start_time, open, high, low, close, volume FROM klines WHERE symbol = ? AND interval = ? ORDER BY start_time DESC LIMIT ?",
        conn, params=(symbol, interval, limit)
    )
    conn.close()
    
    if df.empty:
        lines.append("Nenhum dado encontrado no DB!")
        return lines
        
    lines.append(f"Carregados {len(df)} candles do DB local.")
    
    df = df.iloc[::-1].reset_index(drop=True)
    df['start_time_dt'] = pd.to_datetime(df['start_time'], unit='ms')
    df.set_index('start_time_dt', inplace=True)
    
    cols = ['open', 'high', 'low', 'close', 'volume']
    for col in cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=cols, inplace=True)
    
    klines_list = []
    for ts, row in df.iterrows():
        t_ms = int(ts.timestamp() * 1000)
        klines_list.append([
            t_ms,
            float(row['open']), float(row['high']), float(row['low']), float(row['close']), float(row['volume'])
        ])
        
    lines.append(f"Formatados {len(klines_list)} candles para klines_list.")
    
    # Roda MOLA
    mola = detect_mola_events(df)
    lines.append(f"Zonas MOLA detectadas: {len(mola)}")
    if mola:
        lines.append(f"Exemplo MOLA: {mola[-1]}")
        
    # Roda ABCD
    abcd = strategy_n.find_all_patterns(klines_list)
    lines.append(f"Padrões ABCD detectados: {len(abcd)}")
    if abcd:
        lines.append(f"Exemplo ABCD: {abcd[-1]}")
        
    # Roda 1-2-3
    patterns_123 = detect_123_pattern_pure(klines_list[::-1], find_all=True)
    lines.append(f"Padrões 1-2-3 detectados: {len(patterns_123)}")
    if patterns_123:
        lines.append(f"Exemplo 1-2-3: {patterns_123[-1]}")
        
    return lines

def main():
    lines = ["--- DIAGNÓSTICO DE ESTRATÉGIAS 30M (PURO E ISOLADO) ---"]
    
    for sym in ["AVAXUSDT", "IMXUSDT", "SUIUSDT", "LINKUSDT"]:
        try:
            sym_lines = test_symbol(sym)
            lines.extend(sym_lines)
        except Exception as e:
            lines.append(f"Erro analisando {sym}: {e}")
            
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("Salvo em:", OUT_PATH)

if __name__ == "__main__":
    main()
