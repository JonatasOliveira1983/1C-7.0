from fastapi import APIRouter
from app.api.v1.endpoints import hermes, command, ml, memory
from routes.trading import router as trading_router
from routes.sandbox import router as sandbox_router
from routes.market import router as market_router
from routes.system import router as system_router
from routes.auth import router as auth_router
from routes.admin import router as admin_router

api_router = APIRouter()

# Rotas Corporativas da Base Tecnológica & Memória Agêntica
api_router.include_router(hermes.router, prefix="/hermes", tags=["Hermes Orchestrator"])
api_router.include_router(command.router, prefix="/command", tags=["Command & Telemetry"])
api_router.include_router(ml.router, prefix="/ml", tags=["Machine Learning & Fine-Tuning"])
api_router.include_router(memory.router, prefix="/memory", tags=["Agent Memory & Episodic Store"])

# Rotas do Motor de Trading OKX
api_router.include_router(trading_router, tags=["Trading Engine"])
api_router.include_router(sandbox_router, prefix="/sandbox", tags=["Sandbox Labs"])
api_router.include_router(market_router, tags=["Market & Oracle"])
api_router.include_router(system_router, prefix="/system", tags=["System & Health"])
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(admin_router, prefix="/admin", tags=["Administration"])
