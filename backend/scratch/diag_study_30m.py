import asyncio
import os
import sys

# Adiciona o diretório do backend ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.agents.librarian import librarian_agent

async def test():
    # Inicializa o banco do extractor
    from services.backtest.data_extractor import init_db
    init_db()
    
    print("--- DIAGNÓSTICO ESTUDO 30M ---")
    
    # Testa AVAXUSDT.P
    print("\n[AVAXUSDT.P]")
    res_avax = await librarian_agent.get_visual_data("AVAXUSDT.P", interval="30", limit=600)
    if res_avax:
        print(f"Klines encontradas: {len(res_avax.get('klines', []))}")
        print(f"patterns_123: {len(res_avax.get('patterns_123', []))}")
        print(f"patterns_abcd: {len(res_avax.get('patterns_abcd', []))}")
        print(f"patterns_mola: {len(res_avax.get('patterns_mola', []))}")
    else:
        print("Retornou vazio!")
        
    # Testa IMXUSDT.P
    print("\n[IMXUSDT.P]")
    res_imx = await librarian_agent.get_visual_data("IMXUSDT.P", interval="30", limit=600)
    if res_imx:
        print(f"Klines encontradas: {len(res_imx.get('klines', []))}")
        print(f"patterns_123: {len(res_imx.get('patterns_123', []))}")
        print(f"patterns_abcd: {len(res_imx.get('patterns_abcd', []))}")
        print(f"patterns_mola: {len(res_imx.get('patterns_mola', []))}")
    else:
        print("Retornou vazio!")

if __name__ == "__main__":
    asyncio.run(test())
