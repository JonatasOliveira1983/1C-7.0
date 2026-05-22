# check_railway_slots.py
import asyncio
import os
import sys
import logging
from sqlalchemy import text

# Adicionar o diretório backend ao sys.path para poder importar database_service
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, "..", "1CRYPTEN_SPACE_V4.0", "backend")
services_dir = os.path.join(backend_dir, "services")
sys.path.append(backend_dir)
sys.path.append(services_dir)

from database_service import DatabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CheckSlots")

async def check():
    # Carregar DATABASE_URL do .env
    env_path = os.path.join(backend_dir, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("DATABASE_URL="):
                    db_url = line.split("=", 1)[1].strip()
                    os.environ["DATABASE_URL"] = db_url
                    break

    db = DatabaseService()
    async with db.engine.connect() as conn:
        result = await conn.execute(text("SELECT id, symbol, status_risco, order_id FROM slots ORDER BY id"))
        rows = result.fetchall()
        print("\n--- STATUS DOS SLOTS NO BANCO (RAILWAY) ---")
        for row in rows:
            print(f"Slot {row[0]}: {row[1]} | Status: {row[2]} | OrderID: {row[3]}")
        print("-------------------------------------------\n")

if __name__ == "__main__":
    asyncio.run(check())
