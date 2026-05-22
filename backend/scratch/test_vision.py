import asyncio
import logging
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "1CRYPTEN_SPACE_V4.0", "backend"))

from services.agents.vision_agent import vision_agent

async def test_vision():
    logging.basicConfig(level=logging.INFO)
    symbol = "AVAXUSDT"
    print(f"--- Iniciando teste de visao para {symbol} ---")
    
    # Simula um estudo de contexto
    result = await vision_agent.analyze_market_context(symbol)
    
    print("\n--- RESULTADO DA ANÁLISE DO VISÃO ---")
    if "visual_context" in result:
        print(f"Pensamentos do Visão:\n{result['visual_context']}")
    else:
        print("Falha na análise visual.")
    print("------------------------------------\n")

if __name__ == "__main__":
    asyncio.run(test_vision())
