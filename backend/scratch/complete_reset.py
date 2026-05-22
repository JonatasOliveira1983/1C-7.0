import sys
import os
import asyncio

# Setup do path para carregar módulos do backend
base_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(base_dir)
sys.path.append(backend_dir)

from services.database_service import DatabaseService
from nuclear_reset_v110 import nuclear_reset

async def run_complete_reset():
    print("--- INICIANDO RESET COMPLETO DE BANCA E HISTÓRICO ---")
    
    # 1. Reset Nuclear de Firebase + Local
    print("\nExecutando nuclear_reset() do Firebase e Paper Storage...")
    try:
        nuclear_reset()
    except Exception as e:
        print(f"Erro no nuclear_reset(): {e}")

    # 2. Reset Nuclear do Postgres
    print("\nExecutando reset_system_data() no Postgres...")
    try:
        db_service = DatabaseService()
        success = await db_service.reset_system_data()
        if success:
            print("✅ Postgres resetado com sucesso.")
        else:
            print("❌ Falha ao resetar o Postgres.")
    except Exception as e:
        print(f"Erro ao resetar o Postgres: {e}")

    print("\n--- RESET COMPLETO CONCLUÍDO COM SUCESSO ---")

if __name__ == "__main__":
    asyncio.run(run_complete_reset())
