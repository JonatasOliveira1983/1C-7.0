import os
import sqlite3
import time
import urllib.request
import json
import logging
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DataExtractor")

# Ensure DB is created in backend folder
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backtest_data.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # Create klines table
    c.execute('''
        CREATE TABLE IF NOT EXISTS klines (
            symbol TEXT,
            interval TEXT,
            start_time INTEGER,
            open REAL, high REAL, low REAL, close REAL,
            volume REAL, turnover REAL,
            PRIMARY KEY (symbol, interval, start_time)
        )
    ''')
    # Create eligible pairs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS eligible_pairs (
            symbol TEXT PRIMARY KEY,
            max_leverage INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def get_last_timestamp(symbol: str, interval: str) -> int:
    """Retorna o timestamp da última vela salva para um par/intervalo."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT MAX(start_time) FROM klines WHERE symbol = ? AND interval = ?", (symbol, interval))
        res = c.fetchone()
        conn.close()
        return res[0] if res and res[0] else 0
    except:
        return 0

def get_monitored_from_db():
    """Retorna todos os símbolos que já possuem algum dado no banco local."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT DISTINCT symbol FROM klines")
        symbols = [row[0] for row in c.fetchall()]
        conn.close()
        return symbols
    except:
        return []

def get_eligible_pairs():
    """Fetches eligible pairs from Bybit that match max leverage >= 50 and are not in blocklist."""
    try:
        url = "https://api.bybit.com/v5/market/instruments-info?category=linear"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        if data.get("retCode") != 0:
            logger.error(f"Error fetching instruments: {data}")
            return []

        blocklist = settings.ASSET_BLOCKLIST
        eligible = []

        for item in data["result"]["list"]:
            symbol = item["symbol"]
            status = item["status"]
            if status != "Trading":
                continue
            
            # Check blocklist
            if symbol in blocklist:
                continue

            leverage_filter = item.get("leverageFilter", {})
            max_leverage = float(leverage_filter.get("maxLeverage", 0))

            if max_leverage >= 50:
                eligible.append((symbol, int(max_leverage)))

        logger.info(f"Retrieved {len(eligible)} eligible pairs.")
        
        # Save to DB
        conn = get_db_connection()
        c = conn.cursor()
        c.executemany("REPLACE INTO eligible_pairs (symbol, max_leverage) VALUES (?, ?)", eligible)
        conn.commit()
        conn.close()
        
        return eligible
    except Exception as e:
        logger.error(f"Failed to get eligible pairs: {e}")
        return []

def download_klines(symbol: str, interval: str, limit: int = 1000, start_time: int = None):
    """
    Downloads klines from Bybit API. Support incremental download via start_time.
    Intervals: 5, 15, 60 (1h), 120 (2h), 240 (4h).
    """
    try:
        # Rate limit safety (0.1s sleep)
        time.sleep(0.1)
        
        bybit_interval = interval
        if interval == "1h": bybit_interval = "60"
        elif interval == "2h": bybit_interval = "120"
        elif interval == "4h": bybit_interval = "240"
        elif interval == "15m": bybit_interval = "15"
        elif interval == "5m": bybit_interval = "5"
        elif interval == "D": bybit_interval = "D"
        elif interval == "W": bybit_interval = "W"

        url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval={bybit_interval}&limit={limit}"
        if start_time:
            # We want data AFTER our last timestamp
            url += f"&start={start_time + 1000}" 

        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        if data.get("retCode") != 0:
            logger.error(f"Error fetching klines for {symbol} {interval}: {data}")
            return 0

        kline_list = data["result"]["list"]
        if not kline_list:
            return 0

        records = []
        for k in kline_list:
            records.append((
                symbol, interval, int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5]), float(k[6])
            ))
            
        conn = get_db_connection()
        c = conn.cursor()
        c.executemany('''
            INSERT OR IGNORE INTO klines 
            (symbol, interval, start_time, open, high, low, close, volume, turnover) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', records)
        conn.commit()
        conn.close()
        
        logger.info(f"Saved {len(records)} klines for {symbol} ({interval})")
        return len(records)

    except Exception as e:
        logger.error(f"Failed to download klines: {e}")
        return 0

if __name__ == "__main__":
    init_db()
    # Test execution
    pairs = get_eligible_pairs()
    if pairs:
        # Just a quick test fetching 1 pair
        test_symbol = pairs[0][0]
        download_klines(test_symbol, "4h", limit=50)
