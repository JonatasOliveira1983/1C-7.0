import logging
import asyncio
import time
from typing import Dict, Any, List
from services.agents.aios_adapter import AIOSAgent
from services.firebase_service import firebase_service

logger = logging.getLogger("LibrarianAuditor")

class LibrarianAuditor(AIOSAgent):
    def __init__(self):
        super().__init__(
            agent_id="agent-librarian-auditor-v1",
            role="auditor",
            capabilities=["performance_analysis", "bias_adjustment", "winrate_tracking"]
        )
        self.biases = {
            "macro_weight": 1.0,
            "whale_weight": 1.0,
            "smc_weight": 1.0,
            "last_audit": 0
        }
        self._is_initialized = False

    async def initialize(self):
        if self._is_initialized: return
        
        # Tenta carregar os vieses atuais do RTDB
        try:
            current_biases = await firebase_service.get_system_bias()
            if current_biases:
                self.biases.update(current_biases)
                logger.info(f"📚 [LIBRARIAN-AUDITOR] Biases carregados: {self.biases}")
        except Exception as e:
            logger.error(f"Erro ao carregar biases: {e}")
            
        self._is_initialized = True
        logger.info("📚 Librarian Auditor Initialized & Monitoring History.")
        asyncio.create_task(self.run_loop())

    async def run_loop(self):
        """Loop de auditoria periódica (a cada 4 horas)."""
        while True:
            try:
                await self.perform_audit()
            except Exception as e:
                logger.error(f"Erro no loop de auditoria: {e}")
            await asyncio.sleep(14400) # 4 horas

    async def perform_audit(self):
        """Analisa o histórico e ajusta os pesos de confiança."""
        logger.info("🔍 [LIBRARIAN-AUDITOR] Iniciando auditoria de performance...")
        
        trades = await firebase_service.get_trade_history(limit=50)
        if not trades:
            logger.warning("📚 [LIBRARIAN-AUDITOR] Histórico vazio. Mantendo pesos padrão.")
            return

        # Métricas de acerto por sensor
        sensors = {
            "macro": {"win": 0, "total": 0},
            "micro": {"win": 0, "total": 0}, # Whale/Micro
            "smc": {"win": 0, "total": 0}
        }

        for trade in trades:
            pnl = trade.get("pnl", 0)
            intel = trade.get("fleet_intel", {})
            if not intel: continue
            
            is_win = pnl > 0
            
            # Se o sensor deu score > 70, ele 'apostou' nesse trade
            if intel.get("macro", 50) > 70:
                sensors["macro"]["total"] += 1
                if is_win: sensors["macro"]["win"] += 1
                
            if intel.get("micro", 50) > 70:
                sensors["micro"]["total"] += 1
                if is_win: sensors["micro"]["win"] += 1
                
            if intel.get("smc", 50) > 70:
                sensors["smc"]["total"] += 1
                if is_win: sensors["smc"]["win"] += 1

        # Calcula novos pesos (Mín 0.5, Máx 1.2)
        new_biases = {}
        for key, data in sensors.items():
            if data["total"] >= 5: # Mínimo de amostras para mudar o peso
                win_rate = data["win"] / data["total"]
                # Se win_rate < 40%, reduzimos o peso progressivamente
                # Se win_rate > 60%, aumentamos o peso levemente
                weight = 1.0
                if win_rate < 0.40: weight = 0.5
                elif win_rate < 0.50: weight = 0.8
                elif win_rate > 0.65: weight = 1.2
                
                new_biases[f"{key}_weight"] = weight
            else:
                new_biases[f"{key}_weight"] = 1.0

        new_biases["last_audit"] = time.time()
        self.biases.update(new_biases)
        
        # Salva no RTDB para o Capitão consumir
        await firebase_service.save_system_bias(self.biases)
        logger.info(f"✅ [LIBRARIAN-AUDITOR] Auditoria concluída. Novos pesos: {new_biases}")

    async def on_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        msg_type = message.get("type")
        if msg_type == "FORCE_AUDIT":
            await self.perform_audit()
            return {"status": "SUCCESS", "biases": self.biases}
        return {"status": "ERROR", "message": "Unknown type"}

librarian_auditor = LibrarianAuditor()
