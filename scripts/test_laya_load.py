import os
import sys
import time

sys.path.insert(0, os.path.abspath("backend/app"))
from services.laya_router_service import laya_router_service

print("Testing LayaRouterService status:", laya_router_service.get_status())
t0 = time.time()
res = laya_router_service.classify("Hermes, qual o status do mercado de BTC?")
elapsed = time.time() - t0
print(f"Classification result in {elapsed:.3f}s:", res)
