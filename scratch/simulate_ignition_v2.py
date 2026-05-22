import asyncio
import time
import json
import logging
from services.signal_generator import signal_generator
from services.sovereign_service import sovereign_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SimulateIgnition")

async def simulate():
    symbol = "AVAXUSDT"
    logger.info(f"⚡ Simulando IGNITION_STRIKE para {symbol}...")
    
    ign_signal = {
        "symbol": symbol,
        "side": "Buy",
        "score": 98.5,
        "trigger_type": "IGNITION_STRIKE",
        "is_ignition": True,
        "reason": "Mola Crítica (0.15) | Flow Violento (2.1) | Trend Alinhada",
        "timestamp": time.time()
    }
    
    # Injeta na fila do Radar
    await signal_generator.signal_queue.put((-110, time.time(), ign_signal))
    logger.info("🚀 Sinal de Ignição injetado na fila com prioridade -110.")
    logger.info("Aguarde o Capitão processar (observe os logs do backend).")

if __name__ == "__main__":
    asyncio.run(simulate())
