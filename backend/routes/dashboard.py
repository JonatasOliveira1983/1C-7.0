from fastapi import APIRouter
from fastapi.responses import FileResponse, RedirectResponse
import os
import logging

router = APIRouter(prefix="", tags=["Dashboard"])
logger = logging.getLogger("1CRYPTEN-DASHBOARD")

def get_dirs():
    from main import FRONTEND_DIR
    return FRONTEND_DIR

async def _serve_spa():
    FRONTEND_DIR = get_dirs()
    path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(path):
        return FileResponse(path, media_type="text/html")
    return RedirectResponse(url="/")

@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    FRONTEND_DIR = get_dirs()
    fav_path = os.path.join(FRONTEND_DIR, "favicon.ico")
    if os.path.exists(fav_path):
        return FileResponse(fav_path)
    return {"error": "favicon not found"}

@router.get("/api/dashboard")
async def get_dashboard():
    FRONTEND_DIR = get_dirs()
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return {"error": "Dashboard file not found"}

# Legacy SPA Route Handlers
@router.get("/10d")
async def serve_10d(): return await _serve_spa()

@router.get("/chat")
async def serve_chat(): return await _serve_spa()

@router.get("/config")
async def serve_config(): return await _serve_spa()

# Legacy Redirects
@router.get("/banca/ui")
async def get_banca_ui(): return RedirectResponse(url="/banca")

@router.get("/vault/ui")
async def get_vault_ui(): return RedirectResponse(url="/vault")

@router.get("/armament/ui")
@router.get("/armament")
async def get_armament_ui(): return RedirectResponse(url="/config")

@router.get("/tower")
@router.get("/command-tower")
async def get_tower_ui(): return RedirectResponse(url="/config")

@router.get("/banca")
async def serve_banca(): return RedirectResponse(url="/10d")

@router.get("/radar")
async def serve_radar(): return RedirectResponse(url="/10d")

@router.get("/vault")
async def serve_vault(): return RedirectResponse(url="/10d")

@router.get("/logs")
async def redirect_logs(): return RedirectResponse(url="/chat")

@router.get("/settings")
async def redirect_settings(): return RedirectResponse(url="/config")
