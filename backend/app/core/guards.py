import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

RATE_LIMITS: Dict[str, Tuple[int, int]] = {
    "/api/v1/hermes/chat": (60, 60),
    "/api/hermes/chat": (60, 60),
    "/api/v1/trading/": (240, 60),
    "/api/slots": (300, 60),
    "/api/system/state": (300, 60),
}
DEFAULT_LIMIT: Tuple[int, int] = (600, 60)

_hits: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)

LOCAL_ORIGINS = [
    "http://localhost:8085",
    "http://127.0.0.1:8085",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://1crypten.space",
    "https://1c-100-production.up.railway.app"
]

def _limit_for(path: str) -> Tuple[int, int]:
    for prefix, lim in RATE_LIMITS.items():
        if path.startswith(prefix):
            return lim
    return DEFAULT_LIMIT

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ("/health", "/api/health", "/api/v1/hermes/vitals"):
            return await call_next(request)
        max_req, window = _limit_for(request.url.path)
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        parts = [p for p in request.url.path.split("/") if p][:3]
        bucket_id = "/" + "/".join(parts)
        key = (ip, bucket_id)
        bucket = _hits[key]
        
        while bucket and bucket[0] <= now - window:
            bucket.popleft()
        if len(bucket) >= max_req:
            return JSONResponse(
                {"detail": "Taxa de requisições excedida. Aguarde alguns instantes."},
                status_code=429,
            )
        bucket.append(now)
        return await call_next(request)
