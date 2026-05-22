import logging
import time
from collections import OrderedDict
from typing import Dict, Any, Optional, List

logger = logging.getLogger("AIOS_Memory")

class KLRUCache:
    """
    K-Least Recently Used cache implementation.
    Evicts items not used recently, keeping high-relevance info in 'RAM'.
    """
    def __init__(self, capacity: int = 100):
        self.capacity = capacity
        self.cache = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: str, value: Any):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

class AIOSMemoryManager:
    """
    Unified memory layer for the AIOS Fleet.
    Manages shared intelligence and strategic insights.
    """
    
    def __init__(self):
        # Tactical RAM for recent insights
        self.strategic_mem = KLRUCache(capacity=50) 
        # Ticker/Data cache
        self.data_cache = KLRUCache(capacity=200)

    def set_insight(self, key: str, value: Any):
        """Stores a strategic insight (e.g., 'BTC high volatility detected')."""
        logger.info(f"🧠 [MEMORY] Storing insight: {key}")
        self.strategic_mem.put(key, {
            "value": value,
            "timestamp": time.time()
        })

    def get_insight(self, key: str) -> Optional[Any]:
        """Retrieves a strategic insight."""
        insight = self.strategic_mem.get(key)
        return insight["value"] if insight else None

    def cache_ticker_data(self, symbol: str, data: Dict[str, Any]):
        self.data_cache.put(symbol, data)

    def get_ticker_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        return self.data_cache.get(symbol)

# Singleton instance
memory_manager = AIOSMemoryManager()
