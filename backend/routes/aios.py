from fastapi import APIRouter, Depends, Header, HTTPException, Request
import logging
import os
from config import settings

router = APIRouter(prefix="/api/aios", tags=["AIOS"])
logger = logging.getLogger("1CRYPTEN-AIOS")

def get_adapter():
    from main import BASE_DIR
    from services.aios_adapter import AIOSAdapter
    return AIOSAdapter(os.path.abspath(os.path.join(BASE_DIR, "..", "..")))

@router.get("/memory")
async def get_aios_memory(category: str = None):
    try:
        adapter = get_adapter()
        if category:
            data = adapter.load_memory(category)
            return {"category": category, "data": data, "status": "ok"}
        all_memories = {}
        for cat in ["whale", "sentiment", "macro", "tickers"]:
            mem = adapter.load_memory(cat)
            if mem: all_memories[cat] = mem
        return {"memories": all_memories, "status": "ok"}
    except Exception as e:
        logger.error(f"AIOS Memory Bridge Error: {e}")
        return {"status": "error", "message": str(e), "memories": {}}

@router.get("/state")
async def get_aios_state():
    try:
        adapter = get_adapter()
        state_keys = ["last_macro_risk", "last_whale_alert", "fleet_status", "last_sentiment_score", "active_agents"]
        state = {key: adapter.get_state(key) for key in state_keys if adapter.get_state(key) is not None}
        return {"state": state, "status": "ok"}
    except Exception as e:
        logger.error(f"AIOS State Bridge Error: {e}")
        return {"status": "error", "message": str(e), "state": {}}

@router.get("/debug/kernel")
async def debug_kernel():
    from services.kernel.dispatcher import kernel
    from main import BASE_DIR
    return {
        "agents": list(kernel.agents.keys()),
        "roles": kernel.roles,
        "is_ready": len(kernel.roles) >= 3,
        "base_dir": BASE_DIR
    }
