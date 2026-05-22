import asyncio
import json
import logging
import time
import math
from collections import deque
from pybit.unified_trading import WebSocket
from config import settings
from services.redis_service import redis_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BybitWS")

class BybitWS:
    def __init__(self):
        self.endpoint = "wss://stream-testnet.bybit.com/v5/public/linear" if settings.BYBIT_TESTNET else "wss://stream.bybit.com/v5/public/linear"
        self.ws = None
        # CVD storage: {symbol: {timestamp: delta}}
        self.cvd_data = {} 
        self.prices = {} # {symbol: last_price}
        self.max_cvd_history = 5000 # V44.1: Increased to 5000 for 1h temporal windows
        self.active_symbols = []
        
        # V5.1.0: Protocol Drag
        self.btc_price = 0.0
        self.btc_variation_1h = 0.0
        self.btc_variation_24h = 0.0
        self.btc_variation_15m = 0.0 # [V42.0] Short-term crash detection
        self.btc_adx = 20.0          # [V110.30.2] Market Intelligence ADX
        self.decorrelation_avg = 0.0 # [V110.30.2] Correlation Telemetry

        self.atr_cache = {} # {symbol: atr_value}
        self.rsi_cache = {} # {symbol: rsi_value}
        self.ls_ratio_cache = {} # {symbol: ratio}
        self.oi_cache = {} # {symbol: oi}
        self.turnover_24h_cache = {} # {symbol: turnover_24h_usd}
        self.last_atr_update = 0
        self.pulse_task = None # [V110.30.2] Heartbeat Task
        self.loop = None 
        
        # [V55.0] Microstructure: Orderbook Data
        self.vamp_cache = {}  # {symbol: vamp_value}
        self.obi_cache = {}   # {symbol: imbalance_score}
        self.orderbook_data = {} # {symbol: {bids: [], asks: []}}
        
        # [V44.1] Temporal CVD Cache (Avoid re-calculating whole deque)
        self.temporal_cvd_cache = {} # {symbol: {window: {score, ts}}}

        # 🆕 V6.0: Command Tower Metrics
        self.latency_ms = 0
        self.last_message_time = time.time() * 1000 # [V110.50] Init with current time
        self.buffer_health = 100
        # V15.7.3: Rate Limiter for 89-pair expansion
        self._api_semaphore = asyncio.Semaphore(10)
        
        # 🆕 [V110.50] Decoupled Processing Fila
        self.msg_queue = asyncio.Queue()
        self.worker_task = None
        self.is_reconnecting = False
        
        # [V110.62] CORRELATION SHIELD STORAGE
        # {symbol: deque([price1, price2, ...], maxlen=60)} - 1 point per minute
        self.price_history = {}
        self.last_history_update = {} # {symbol: timestamp}

    def handle_trade_message(self, message):
        """[V110.50] Decoupled: Only injects into queue to keep WS thread fast."""
        try:
            if self.loop and self.loop.is_running():
                message["_type"] = "trade"
                self.loop.call_soon_threadsafe(self.msg_queue.put_nowait, message)
        except Exception as e:
            logger.error(f"Error queuing trade message: {e}")

    async def _process_trade(self, message):
        """Processes trade messages to calculate CVD."""
        try:
            # 🆕 V6.0: Latency Tracking
            receive_ts = time.time() * 1000
            msg_ts = message.get("ts", receive_ts)
            self.latency_ms = max(0, receive_ts - msg_ts)
            self.last_message_time = receive_ts

            data = message.get("data", [])
            topic = message.get("topic", "")
            # V5.2.2: Keep symbol consistent with topic (No .P suffix for Mainnet/Testnet public topics)
            symbol = topic.replace("publicTrade.", "")

            if symbol not in self.cvd_data:
                self.cvd_data[symbol] = deque(maxlen=self.max_cvd_history)

            for trade in data:
                side = trade.get("S") # 'Buy' or 'Sell'
                size = float(trade.get("v", 0))
                price = float(trade.get("p", 0))
                trade_ts = float(trade.get("T", time.time() * 1000))
                
                # UPDATE: Normalize CVD to USD Value for fair comparison
                norm_sym = symbol.replace(".P", "").upper()
                if price == 0: price = self.prices.get(norm_sym, 0)
                else: self.prices[norm_sym] = price # Update last known price from trade event

                delta = (size * price) if side == "Buy" else -(size * price)
                self.cvd_data[symbol].append({
                    "timestamp": trade_ts,
                    "delta": delta
                })
                
                # V5.4.0: Persist to Redis Cache for low-latency ROIs
                # [V44.1] Score current (Full Deque)
                score = sum(item["delta"] for item in self.cvd_data[symbol])
                await redis_service.set_cvd(symbol, score)
                    
            # 🆕 V6.0: Push health metrics to Redis
            if getattr(redis_service, 'client', None):
                health_data = {"latency": self.latency_ms, "status": "ONLINE", "ts": self.last_message_time}
                await redis_service.client.set("ws_health", json.dumps(health_data))
        except Exception as e:
            logger.error(f"Error processing trade message: {e}")

    def handle_orderbook_message(self, message):
        """[V110.50] Decoupled into queue."""
        try:
            if self.loop and self.loop.is_running():
                message["_type"] = "orderbook"
                self.loop.call_soon_threadsafe(self.msg_queue.put_nowait, message)
        except Exception as e:
            logger.error(f"Error queuing orderbook message: {e}")

    async def _process_orderbook(self, message):
        """[V55.0] Processes orderbook updates to calculate VAMP and OBI."""
        try:
            data = message.get("data", {})
            topic = message.get("topic", "")
            symbol = topic.replace("orderbook.50.", "")
            norm_sym = symbol.replace(".P", "").upper()
            
            bids = data.get("b", [])  # [[price, size], ...]
            asks = data.get("a", [])  # [[price, size], ...]
            
            if not bids or not asks:
                return

            # Update latency & health metrics on ANY message
            self.last_message_time = time.time() * 1000

            # OBI (Order Book Imbalance) - Net pressure in top 10 levels
            bid_vol_top = sum(float(b[1]) for b in bids[:10])
            ask_vol_top = sum(float(a[1]) for a in asks[:10])
            
            obi = (bid_vol_top - ask_vol_top) / (bid_vol_top + ask_vol_top) if (bid_vol_top + ask_vol_top) > 0 else 0
            self.obi_cache[norm_sym] = round(obi, 4)

            # VAMP (Volume Adjusted Mid Price) - Weighted price logic
            p_bid, q_bid = float(bids[0][0]), float(bids[0][1])
            p_ask, q_ask = float(asks[0][0]), float(asks[0][1])
            
            vamp = ((p_bid * q_ask) + (p_ask * q_bid)) / (q_bid + q_ask) if (q_bid + q_ask) > 0 else (p_bid + p_ask) / 2
            self.vamp_cache[norm_sym] = round(vamp, 8)
            
            # Store raw snapshot
            self.orderbook_data[norm_sym] = {"bids": bids[:20], "asks": asks[:20]}

            # Sync to Redis
            await redis_service.client.set(f"obi:{norm_sym}", self.obi_cache[norm_sym])
            await redis_service.client.set(f"vamp:{norm_sym}", self.vamp_cache[norm_sym])

        except Exception as e:
            logger.error(f"Error processing orderbook message: {e}")

    def handle_ticker_message(self, message):
        """[V110.50] Decoupled into queue."""
        try:
            if self.loop and self.loop.is_running():
                message["_type"] = "ticker"
                self.loop.call_soon_threadsafe(self.msg_queue.put_nowait, message)
        except Exception as e:
            logger.error(f"Error queuing ticker message: {e}")

    async def _process_ticker(self, message):
        """Processes ticker updates to maintain current price references."""
        try:
            data = message.get("data", {})
            topic = message.get("topic", "")
            symbol = topic.replace("tickers.", "")
            
            # Update health
            self.last_message_time = time.time() * 1000

            if "lastPrice" in data:
                norm_sym = symbol.replace(".P", "").upper()
                price = float(data["lastPrice"])
                self.prices[norm_sym] = price
                if "turnover24h" in data:
                    self.turnover_24h_cache[norm_sym] = float(data["turnover24h"])
                
                # Sync to Redis
                await redis_service.set_ticker(norm_sym, price)
                
                # [V110.62] Update Temporal Price History (1-minute resolution)
                now = time.time()
                last_update = self.last_history_update.get(norm_sym, 0)
                if now - last_update >= 60: # 1 minute
                    if norm_sym not in self.price_history:
                        self.price_history[norm_sym] = deque(maxlen=60)
                    self.price_history[norm_sym].append(price)
                    self.last_history_update[norm_sym] = now
        except Exception as e:
            logger.error(f"Error processing ticker message: {e}")

    def get_current_price(self, symbol: str) -> float:
        """[V5.2.5] Returns the last known price for a symbol."""
        norm_sym = symbol.replace(".P", "").upper()
        return self.prices.get(norm_sym, 0.0)

    def get_cvd_score(self, symbol: str) -> float:
        """Returns the current cumulative delta for the stored history."""
        # V5.2.4: Normalize symbol to match internal keys (remove .P)
        norm_symbol = symbol.replace(".P", "").upper()
        if norm_symbol not in self.cvd_data:
            return 0.0
        # V15.1: Thread-safe snapshot to avoid 'deque mutated during iteration'
        data_snapshot = list(self.cvd_data[norm_symbol])
        return sum(item["delta"] for item in data_snapshot)

    def get_cvd_score_time(self, symbol: str, window_seconds: int = 300) -> float:
        """[V44.1] Returns CVD score for a specific time window (default 5m)."""
        norm_symbol = symbol.replace(".P", "").upper()
        if norm_symbol not in self.cvd_data:
            return 0.0
        
        now_ms = time.time() * 1000
        threshold_ms = now_ms - (window_seconds * 1000)
        
        # V15.1: Thread-safe snapshot to avoid 'deque mutated during iteration'
        data_snapshot = list(self.cvd_data[norm_symbol])
        
        # Filter by timestamp
        window_delta = sum(item["delta"] for item in data_snapshot if item["timestamp"] >= threshold_ms)
        return window_delta

    def get_correlation(self, symbol_a: str, symbol_b: str) -> float:
        """
        [V110.62] Calcula a correlação de Pearson entre dois ativos.
        Usa o price_history (60 pontos). Retorna valor entre -1.0 e 1.0.
        """
        sym_a = symbol_a.replace(".P", "").upper()
        sym_b = symbol_b.replace(".P", "").upper()
        
        if sym_a not in self.price_history or sym_b not in self.price_history:
            return 0.0
            
        hist_a = list(self.price_history[sym_a])
        hist_b = list(self.price_history[sym_b])
        
        # Necesário ter pontos suficientes para correlação significativa (min 10)
        n = min(len(hist_a), len(hist_b))
        if n < 10:
            return 0.0
            
        # Alinha os tamanhos
        x = hist_a[-n:]
        y = hist_b[-n:]
        
        try:
            mean_x = sum(x) / n
            mean_y = sum(y) / n
            
            num = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
            den_x = sum((x[i] - mean_x)**2 for i in range(n))
            den_y = sum((y[i] - mean_y)**2 for i in range(n))
            
            den = math.sqrt(den_x * den_y)
            if den == 0:
                return 0.0
                
            return round(num / den, 4)
        except Exception as e:
            logger.error(f"Error calculating correlation between {sym_a} and {sym_b}: {e}")
            return 0.0

    def _calculate_adx(self, klines) -> float:
        """Helper to calculate ADX using Wilder's Smoothing."""
        if not klines or len(klines) < 28:
            return 0.0
            
        try:
            candles = klines[::-1] # Chronological
            highs = [float(c[2]) for c in candles]
            lows = [float(c[3]) for c in candles]
            closes = [float(c[4]) for c in candles]
            
            period = 14
            tr_list, plus_dm_list, minus_dm_list = [], [], []
            for i in range(1, len(candles)):
                tr = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
                tr_list.append(tr)
                h_diff = highs[i] - highs[i-1]
                l_diff = lows[i-1] - lows[i]
                plus_dm_list.append(h_diff if (h_diff > l_diff and h_diff > 0) else 0)
                minus_dm_list.append(l_diff if (l_diff > h_diff and l_diff > 0) else 0)
            
            atr = sum(tr_list[:period]) / period
            plus_di_smooth = sum(plus_dm_list[:period]) / period
            minus_di_smooth = sum(minus_dm_list[:period]) / period
            dx_list = []
            for i in range(period, len(tr_list)):
                atr = (atr * (period - 1) + tr_list[i]) / period
                plus_di_smooth = (plus_di_smooth * (period - 1) + plus_dm_list[i]) / period
                minus_di_smooth = (minus_di_smooth * (period - 1) + minus_dm_list[i]) / period
                pdi = (plus_di_smooth / atr * 100) if atr > 0 else 0
                mdi = (minus_di_smooth / atr * 100) if atr > 0 else 0
                dx_list.append(abs(pdi - mdi) / (pdi + mdi) * 100 if (pdi + mdi) > 0 else 0)
            
            if dx_list:
                adx = sum(dx_list[:period]) / period
                for i in range(period, len(dx_list)):
                    adx = (adx * (period - 1) + dx_list[i]) / period
                return round(adx, 2)
        except Exception as adx_err:
            logger.error(f"Error calculating ADX: {adx_err}")
        return 0.0

    async def update_market_context(self):
        """
        V110.36.0: Updates BTC variation and calculates Master ADX (M-ADX).
        M-ADX Weights: 4H (40%), 1H (40%), 15m (20%).
        """
        from services.bybit_rest import bybit_rest_service
        now = time.time()
        
        try:
            # 1. Update BTC Variation (1h)
            btc_klines_1h = await bybit_rest_service.get_klines(symbol="BTCUSDT", interval="60", limit=30)
            if len(btc_klines_1h) >= 2:
                # Bybit returns newest first: [current, previous]
                close_latest = float(btc_klines_1h[0][4])
                close_prev = float(btc_klines_1h[1][4])
                self.btc_variation_1h = ((close_latest - close_prev) / close_prev) * 100
                self.btc_price = close_latest

            # 2. [V110.36.0] Master ADX (M-ADX) Calculation
            # Fetch 4H and 15m klines concurrently alongside the already fetched 1H
            btc_klines_4h = await bybit_rest_service.get_klines(symbol="BTCUSDT", interval="240", limit=30)
            btc_klines_15m = await bybit_rest_service.get_klines(symbol="BTCUSDT", interval="15", limit=30)
            
            adx_4h = self._calculate_adx(btc_klines_4h)
            adx_1h = self._calculate_adx(btc_klines_1h)
            adx_15m = self._calculate_adx(btc_klines_15m)
            
            if adx_4h > 0 and adx_1h > 0 and adx_15m > 0:
                self.btc_adx = round((adx_4h * 0.40) + (adx_1h * 0.40) + (adx_15m * 0.20), 2)
                logger.info(f"🔮 [M-ADX] 4H:{adx_4h} | 1H:{adx_1h} | 15m:{adx_15m} -> Master: {self.btc_adx}")
            elif adx_1h > 0:
                # Fallback if 4H fails
                self.btc_adx = adx_1h
                logger.info(f"🔮 [M-ADX Fallback] Using 1H ADX: {adx_1h}")

            # [V42.0] Short-term variation (15m) for crash detection
            btc_15m = await bybit_rest_service.get_klines(symbol="BTCUSDT", interval="15", limit=2)
            if len(btc_15m) >= 2:
                c15_latest = float(btc_15m[0][4])
                c15_prev = float(btc_15m[1][4])
                self.btc_variation_15m = ((c15_latest - c15_prev) / c15_prev) * 100

            # [V110.30.2] BTC Variation (24h)
            btc_24h = await bybit_rest_service.get_klines(symbol="BTCUSDT", interval="D", limit=2)
            if len(btc_24h) >= 2:
                c24_latest = float(btc_24h[0][4])
                c24_prev = float(btc_24h[1][4])
                self.btc_variation_24h = ((c24_latest - c24_prev) / c24_prev) * 100

            # 🆕 [V110.32.1] Sync with Oracle Agent
            try:
                from services.agents.oracle_agent import oracle_agent
                await oracle_agent.update_market_data("bybit_ws", {
                    "btc_price": self.btc_price,
                    "btc_variation_1h": self.btc_variation_1h,
                    "btc_variation_24h": self.btc_variation_24h,
                    "btc_adx": self.btc_adx
                })
            except Exception as oracle_err:
                logger.error(f"Error syncing with Oracle from WS: {oracle_err}")

            # V15.7.4: Sync with Sniper Pulse (Every 60s)
            if now - self.last_atr_update > 60: 
                
                async def process_symbol_metrics(symbol):
                    async with self._api_semaphore:
                        try:
                            # [V110.20.1] Blocklist Guard
                            norm_sym = symbol.replace(".P", "").upper()
                            if norm_sym in settings.ASSET_BLOCKLIST:
                                return
                            # ATR & RSI fetch
                            klines = await bybit_rest_service.get_klines(symbol=symbol, interval="60", limit=16)
                            if len(klines) >= 15:
                                # --- ATR Calculation ---
                                tr_list = []
                                for i in range(1, len(klines)):
                                    high, low, prev_close = float(klines[i][2]), float(klines[i][3]), float(klines[i-1][4])
                                    tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
                                    tr_list.append(tr)
                                self.atr_cache[symbol] = sum(tr_list[-14:]) / 14

                                # --- RSI Calculation ---
                                # Use float conversion to avoid type errors
                                try:
                                    closes = [float(k[4]) for k in klines]
                                    changes = [closes[i] - closes[i-1] for i in range(1, len(closes))]
                                    gains = [c if c > 0 else 0 for c in changes[-14:]]
                                    losses = [abs(c) if c < 0 else 0 for c in changes[-14:]]
                                    avg_gain, avg_loss = sum(gains) / 14, sum(losses) / 14
                                    self.rsi_cache[symbol] = 100 if avg_loss == 0 else 100 - (100 / (1 + (avg_gain / avg_loss)))
                                except Exception as rsi_err:
                                    logger.error(f"RSI Calc error for {symbol}: {rsi_err}")

                            # --- LS Ratio & OI ---
                            ls_ratio = await bybit_rest_service.get_account_ratio(symbol)
                            oi = await bybit_rest_service.get_open_interest(symbol)

                            self.ls_ratio_cache[symbol] = ls_ratio
                            self.oi_cache[symbol] = oi
                            
                            await redis_service.set_ls_ratio(symbol, ls_ratio)
                            await redis_service.set_oi(symbol, oi)
                            
                        except Exception as sym_err:
                            logger.error(f"Error processing metrics for {symbol}: {sym_err}")

                # [V110.117] Otimização de Thread Pool: Processar em chunks de 10 ativos
                # Isso evita disparar centenas de requisições REST/Threads simultâneas que bloqueiam a API.
                if self.active_symbols:
                    chunks = [self.active_symbols[i:i + 10] for i in range(0, len(self.active_symbols), 10)]
                    processed_total = 0
                    for chunk in chunks:
                        await asyncio.gather(*(process_symbol_metrics(s) for s in chunk))
                        processed_total += len(chunk)
                        
                    self.last_atr_update = now
                    logger.info(f"V15.7: Sniper Pulse (ATR/RSI/LS/OI) updated for {processed_total} symbols (Chunked Processing).")

        except Exception as e:
            logger.error(f"Error updating market context in BybitWS: {e}")

    async def start(self, symbols: list):
        """Starts the WebSocket connection for a list of symbols (V4.3 Expansion)."""
        logger.info(f"🔄 [BYBIT-WS] Starting WebSocket for {len(symbols)} symbols...")
        # V12.1: Always include BTCUSDT for CVD/Drag tracking
        has_btc = any(s.replace(".P", "").upper() == "BTCUSDT" for s in symbols)
        if not has_btc:
            symbols.insert(0, "BTCUSDT")
            logger.info("V12.1: BTCUSDT added to WebSocket monitoring for BTC Command Center")
        
        self.active_symbols = symbols
        self.loop = asyncio.get_running_loop() # V5.4.5: Capture main loop
        
        # [V110.30.2] Start Heartbeat Loop
        if not self.pulse_task:
            self.pulse_task = asyncio.create_task(self.run_loop())
            logger.info("💓 [BYBIT-WS] Heartbeat Loop Started.")
        
        # [V110.50] Start Decoupled Worker
        if not self.worker_task:
            self.worker_task = asyncio.create_task(self.process_message_queue())
            logger.info("👷 [BYBIT-WS] Async Queue Worker Started.")
        
        self.ws = WebSocket(
            testnet=settings.BYBIT_TESTNET,
            channel_type="linear",
        )
        
        # V14.1 Shield: Cap symbols at 95 to stay under 200 topics (2 per symbol + BTC)
        monitored_symbols = symbols[:95]
        for symbol in monitored_symbols:
            api_symbol = symbol.replace(".P", "")
            # Subscribe to trades for CVD calculation (V5 Public Linear)
            self.ws.trade_stream(symbol=api_symbol, callback=self.handle_trade_message)
            # Ticker stream for real-time price & normalization
            self.ws.ticker_stream(symbol=api_symbol, callback=self.handle_ticker_message)
            # [V55.0] Orderbook stream for Microstructure (Depth 50)
            self.ws.orderbook_stream(symbol=api_symbol, depth=50, callback=self.handle_orderbook_message)

    async def sync_topics(self, new_symbols: list):
        """
        [V6.0] Rebalances WebSocket subscriptions to match a new list of active symbols.
        Ensures we stay within the 200 topic limit while rotating candidates.
        """
        if not self.ws: return
        
        # Ensure BTC is always monitored
        if "BTCUSDT" not in [s.replace(".P", "").upper() for s in new_symbols]:
            new_symbols.insert(0, "BTCUSDT.P")
        
        new_monitored = new_symbols[:95]
        new_set = {s.replace(".P", "").upper() for s in new_monitored}
        old_set = {s.replace(".P", "").upper() for s in self.active_symbols[:95]}
        
        to_add = [s for s in new_monitored if s.replace(".P", "").upper() not in old_set]
        to_remove = [s for s in self.active_symbols[:95] if s.replace(".P", "").upper() not in new_set]
        
        if not to_add and not to_remove:
            return

        logger.info(f"🔄 [BYBIT-WS] Rebalancing: +{len(to_add)} | -{len(to_remove)} symbols.")
        
        # 1. Unsubscribe from old (Best effort - some pybit versions might not have unsubscribe)
        for s in to_remove:
            try:
                api_symbol = s.replace(".P", "")
                if hasattr(self.ws, "unsubscribe"):
                    self.ws.unsubscribe(f"publicTrade.{api_symbol}")
                    self.ws.unsubscribe(f"tickers.{api_symbol}")
            except Exception as e:
                logger.debug(f"Unsubscribe from {s} failed (expected if not supported): {e}")
        
        # 2. Subscribe to new
        for s in to_add:
            try:
                api_symbol = s.replace(".P", "")
                self.ws.trade_stream(symbol=api_symbol, callback=self.handle_trade_message)
                self.ws.ticker_stream(symbol=api_symbol, callback=self.handle_ticker_message)
                # [V55.0] Subscribe to orderbook
                self.ws.orderbook_stream(symbol=api_symbol, depth=50, callback=self.handle_orderbook_message)
            except Exception as e:
                logger.error(f"Subscription to {s} failed: {e}")
        
        self.active_symbols = new_symbols
        logger.info(f"✅ [BYBIT-WS] Sync complete. Total active: {len(self.active_symbols)}")

        logger.info(f"BybitWS: Subscribed to {len(new_monitored)} symbols for CVD & Price monitoring.")

    async def process_message_queue(self):
        """[V110.50] Worker that processes klines/trades outside the WS thread."""
        logger.info("🚀 [BYBIT-WS] Worker active. Subscribing to internal queue...")
        while True:
            try:
                message = await self.msg_queue.get()
                m_type = message.get("_type")
                
                if m_type == "trade":
                    await self._process_trade(message)
                elif m_type == "orderbook":
                    await self._process_orderbook(message)
                elif m_type == "ticker":
                    await self._process_ticker(message)
                
                self.msg_queue.task_done()
            except Exception as e:
                logger.error(f"Error in process_message_queue: {e}")
                await asyncio.sleep(0.1)

    async def run_loop(self):
        """[V110.50] Watchdog Heartbeat. Detects silences and restarts WS."""
        logger.info("🚀 Starting BybitWS Watchdog Loop...")
        while True:
            try:
                now_ms = time.time() * 1000
                
                # [WATCHDOG] Check if last message was too long ago (> 45s)
                # Only if we are not already reconnecting
                if not self.is_reconnecting and (now_ms - self.last_message_time > 45000):
                    logger.warning(f"⚠️ [WATCHDOG] WebSocket Silence Detected ({(now_ms - self.last_message_time)/1000:.1f}s). Restarting...")
                    self.is_reconnecting = True
                    try:
                        if self.ws: self.ws.exit()
                    except: pass
                    
                    await asyncio.sleep(2)
                    await self.start(self.active_symbols)
                    self.is_reconnecting = False
                    self.last_message_time = time.time() * 1000
                    logger.info("♻️ [WATCHDOG] WebSocket Restarted successfully.")

                await self.update_market_context()
                await asyncio.sleep(60) # Sync context every 1 min
            except Exception as e:
                logger.error(f"Error in BybitWS run_loop: {e}")
                self.is_reconnecting = False
                await asyncio.sleep(10)

    def stop(self):
        if self.ws:
            logger.info("🛑 [BYBIT-WS] Stopping WebSocket connection...")
            if self.pulse_task:
                self.pulse_task.cancel()
            self.ws.exit()
            logger.info("✅ [BYBIT-WS] WebSocket stopped successfully.")

bybit_ws_service = BybitWS()
