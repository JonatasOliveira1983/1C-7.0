import logging
import json
import asyncio
import time
from pathlib import Path
from config import settings
from typing import Optional, Any, Dict
from .aios_adapter import AIOSAdapter

# Use a standard dictionary for in-memory fallback
_LOCAL_CACHE: Dict[str, str] = {}
_LOCAL_EXPIRY: Dict[str, float] = {}

# V16.5: Initialize AIOS Adapter for cold/warm persistence
# Standard project root discovery
PROJECT_ROOT = str(Path(__file__).parents[3])
aios_adapter = AIOSAdapter(PROJECT_ROOT)

class MockRedis:
    """V16.5: Enhanced In-Memory Fallback with AIOS Persistence Bridge."""
    async def ping(self): return True
    
    async def set(self, key: str, value: str, ex: int = None, nx: bool = False):
        if nx and key in _LOCAL_CACHE:
            # Check if expired
            if time.time() < _LOCAL_EXPIRY.get(key, float('inf')):
                return False
        
        _LOCAL_CACHE[key] = value
        if ex:
            _LOCAL_EXPIRY[key] = time.time() + ex
        else:
            _LOCAL_EXPIRY[key] = float('inf')
            
        # V16.5 Persistence Sync: Save critical metrics to AIOS disk
        # V16.7 Optimization: SKIP volatile metrics (ticker, cvd) to avoid event loop blockage
        # Only persist stable system state, not high-frequency data
        if key.startswith("system:") or key.startswith("vault:"):
            aios_adapter.save_state(key, value)
            
        return True

    async def get(self, key: str):
        # 1. Try local cache
        if key in _LOCAL_CACHE:
            if time.time() < _LOCAL_EXPIRY.get(key, float('inf')):
                return _LOCAL_CACHE[key]
            else:
                del _LOCAL_CACHE[key]
                del _LOCAL_EXPIRY[key]
        
        # 2. V16.5 Bridge: Try AIOS disk cache if memory is empty
        persistent_val = aios_adapter.get_state(key)
        if persistent_val:
            # Restore to memory for speed
            _LOCAL_CACHE[key] = persistent_val
            _LOCAL_EXPIRY[key] = time.time() + 60 # Default fresh expiry
            return persistent_val
            
        return None

    async def delete(self, key: str):
        _LOCAL_CACHE.pop(key, None)
        _LOCAL_EXPIRY.pop(key, None)

    async def publish(self, channel: str, message: str):
        return 1

logger = logging.getLogger("RedisService")

class RedisService:
    def __init__(self):
        self.client: Any = None
        self.host = settings.REDIS_HOST
        self.port = settings.REDIS_PORT
        self.db = settings.REDIS_DB
        self.is_connected = False
        self.is_fallback = False

    async def connect(self):
        """Initializes the Redis async client with robust fallback."""
        if self.is_connected:
            return
        
        try:
            import redis.asyncio as redis_lib
            import os
            # [V110.175] Railway Native REDIS_URL priority
            redis_url = getattr(settings, "REDIS_URL", None) or os.getenv("REDIS_URL")
            
            if redis_url:
                self.client = redis_lib.Redis.from_url(redis_url, decode_responses=True)
            else:
                self.client = redis_lib.Redis(
                    host=self.host,
                    port=self.port,
                    password=settings.REDIS_PASSWORD,
                    db=self.db,
                    decode_responses=True
                )
            # Test connection with short timeout
            await asyncio.wait_for(self.client.ping(), timeout=2.0)
            self.is_connected = True
            self.is_fallback = False
            logger.info(f"🚀 Redis Connected: {self.host}:{self.port} (DB {self.db})")
        except Exception as e:
            logger.warning(f"⚠️ Redis Connection Failed ({e}). Entering AIOS Fallback Mode (In-Memory + Disk).")
            self.client = MockRedis()
            self.is_connected = True
            self.is_fallback = True
            logger.info("💎 AIOS Fallback Active: Memory + Disk persistence enabled.")

    async def set_ticker(self, symbol: str, price: float):
        """Caches the last price of a symbol (TTL: 60s)."""
        try:
            key = f"ticker:{symbol.upper()}"
            await self.client.set(key, str(price), ex=60)
        except Exception as e:
            logger.error(f"Redis set_ticker error: {e}")

    async def get_ticker(self, symbol: str) -> Optional[float]:
        """Retrieves cached price for a symbol."""
        try:
            val = await self.client.get(f"ticker:{symbol.upper()}")
            return float(val) if val else None
        except Exception: return None

    async def set_cvd(self, symbol: str, cvd: float):
        """Caches the cumulative delta score (TTL: 300s)."""
        try:
            key = f"cvd:{symbol.upper()}"
            await self.client.set(key, str(cvd), ex=300)
        except Exception as e:
            logger.error(f"Redis set_cvd error: {e}")

    async def get_cvd(self, symbol: str) -> float:
        """Retrieves cached CVD score."""
        try:
            val = await self.client.get(f"cvd:{symbol.upper()}")
            return float(val) if val else 0.0
        except Exception: return 0.0

    async def set_oi(self, symbol: str, oi: float):
        """Caches the Open Interest (TTL: 300s)."""
        try:
            key = f"oi:{symbol.upper()}"
            await self.client.set(key, str(oi), ex=300)
        except Exception as e:
            logger.error(f"Redis set_oi error: {e}")

    async def get_oi(self, symbol: str) -> float:
        """Retrieves cached Open Interest."""
        try:
            val = await self.client.get(f"oi:{symbol.upper()}")
            return float(val) if val else 0.0
        except Exception: return 0.0

    async def set_ls_ratio(self, symbol: str, ratio: float):
        """Caches the Long/Short Ratio (TTL: 300s)."""
        try:
            key = f"ls:{symbol.upper()}"
            await self.client.set(key, str(ratio), ex=300)
        except Exception as e:
            logger.error(f"Redis set_ls_ratio error: {e}")

    async def get_ls_ratio(self, symbol: str) -> float:
        """Retrieves cached Long/Short Ratio."""
        try:
            val = await self.client.get(f"ls:{symbol.upper()}")
            return float(val) if val else 1.0
        except Exception: return 1.0

    async def acquire_lock(self, lock_name: str, acquire_timeout: int = 5, lock_timeout: int = 10) -> bool:
        """Distributed atomic lock using SET NX or local Mock."""
        lock_key = f"lock:{lock_name}"
        end_time = time.time() + acquire_timeout
        
        while time.time() < end_time:
            # nx=True handles the atomic check
            if await self.client.set(lock_key, "locked", ex=lock_timeout, nx=True):
                return True
            await asyncio.sleep(0.05)
            
        return False

    async def release_lock(self, lock_name: str):
        """Releases a distributed lock."""
        try:
            await self.client.delete(f"lock:{lock_name}")
        except Exception: pass

    async def publish_update(self, channel: str, data: dict):
        """Publishes a message to a Redis channel for real-time UI updates."""
        try:
            await self.client.publish(channel, json.dumps(data))
        except Exception as e:
            logger.error(f"Redis publish error: {e}")

# Global Instance
redis_service = RedisService()
