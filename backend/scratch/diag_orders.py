import asyncio
import sys
import os

# Adiciona o diretório do backend ao sys.path
backend_dir = r"c:\Users\spcom\Desktop\10D REAL 5.0\1CRYPTEN_SPACE_V4.0\backend"
sys.path.append(backend_dir)

async def main():
    try:
        from services.database_service import database_service
        from services.sovereign_service import sovereign_service
        
        print("--- Verificando Slots Ativos no Postgres ---")
        slots = await database_service.get_active_slots()
        active_slots = [s for s in slots if s.symbol]
        for s in active_slots:
            print(f"Slot {s.id}: {s.symbol} ({s.side}) - Status: {s.status_risco}")
            
        print("\n--- Verificando Moonbags no Postgres ---")
        moons = await database_service.get_moonbags()
        for m in moons:
            print(f"Moonbag: {m.symbol} ({m.side})")
            
        print("\n--- Verificando Estado Paper (Sovereign) ---")
        paper_state = await sovereign_service.get_paper_state()
        if paper_state:
            positions = paper_state.get("positions", [])
            for p in positions:
                print(f"Paper Position: {p.get('symbol')} ({p.get('side')})")
            
            moonbags = paper_state.get("moonbags", [])
            for m in moonbags:
                print(f"Paper Moonbag: {m.get('symbol')} ({m.get('side')})")
        else:
            print("Estado Paper não encontrado.")

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    asyncio.run(main())
