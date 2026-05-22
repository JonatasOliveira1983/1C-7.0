import logging
import time
from typing import Dict, Any
from services.firebase_service import firebase_service
from services.vault_service import vault_service

logger = logging.getLogger("KernelTools")

class KernelTools:
    """
    Standard tools exposed by the AIOS Kernel for agents to maintain awareness.
    """
    
    @staticmethod
    async def get_system_pulse() -> Dict[str, Any]:
        """
        Generates a 360-degree 'Pulse' report of the entire 1CRYPTEN environment.
        This is the source of truth for all AI conversations.
        """
        try:
            banca = await firebase_service.get_banca_status()
            slots = await firebase_service.get_active_slots()
            vault = await vault_service.get_cycle_status()
            signals = await firebase_service.get_recent_signals(limit=5)
            
            # Identify active mission
            active_symbols = [s["symbol"] for s in slots if s.get("symbol")]
            mission = f"ACTIVE ({', '.join(active_symbols)})" if active_symbols else "SCANNING FOR OPPORTUNITIES"
            
            pulse = {
                "equity": {
                    "balance": banca.get("saldo_total", 0),
                    "risk_pct": banca.get("risco_real_percent", 0),
                    "slots_available": 4 - len(active_symbols)
                },
                "mission_status": mission,
                "vault_progress": {
                    "wins": vault.get("sniper_wins", 0),
                    "total_goal": 10,
                    "vault_balance": vault.get("vault_total", 0)
                },
                "recent_radar": [s["symbol"] for s in signals if s.get("score", 0) > 80],
                "system_health": "OPTIMAL",
                "timestamp": time.time()
            }
            return pulse
        except Exception as e:
            logger.error(f"Error generating kernel pulse: {e}")
            return {"error": str(e)}

kernel_tools = KernelTools()
