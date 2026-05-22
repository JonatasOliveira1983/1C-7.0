import asyncio
import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestVision")

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "1CRYPTEN_SPACE_V4.0", "backend"))

async def test_vision_flow():
    from services.agents.vision_agent import vision_agent
    from services.screenshot_service import screenshot_service
    from services.sovereign_service import sovereign_service
    
    print("[TEST] Iniciando Teste do Agente Visao...")
    
    # Test 1: Capture Screenshot
    symbol = "SUIUSDT"
    print(f"Capturando grafico para {symbol}...")
    path = await screenshot_service.capture_chart(symbol, interval="30")
    
    if path and os.path.exists(path):
        print(f"OK: Screenshot salvo em: {path}")
    else:
        print("ERR: Falha na captura do screenshot.")
        return

    # Test 2: Vision Analysis
    print(f"Solicitando analise do Agente Visao para {symbol} LONG...")
    result = await vision_agent.confirm_entry(symbol, "Buy", 85)
    
    print("\n--- RESULTADO DA VISAO ---")
    print(f"Decisao: {result.get('approved')}")
    print(f"Confianca: {result.get('confidence')}%")
    print(f"Analise: {result.get('reason')}")
    print(f"Pensamentos: {result.get('thoughts')}")
    print("--------------------------\n")
    
    if result.get('approved') is not None:
        print("OK: Teste de Fluxo de Visao COMPLETO.")
    else:
        print("ERR: Falha na analise de visao.")

if __name__ == "__main__":
    asyncio.run(test_vision_flow())
