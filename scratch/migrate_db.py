# migrate_db.py
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

import database_service
from database_service import DatabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Migration")

async def migrate():
    # Garantir que a DATABASE_URL do Railway seja usada se estiver disponível no .env
    env_path = os.path.join(backend_dir, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("DATABASE_URL="):
                    db_url = line.split("=", 1)[1].strip()
                    os.environ["DATABASE_URL"] = db_url
                    logger.info("📍 Usando DATABASE_URL do arquivo .env")
                    break

    db = DatabaseService()
    
    # Define columns to add
    # Format: (table, column, type)
    migrations = [
        ("slots", "t1", "DOUBLE PRECISION"),
        ("slots", "t2", "DOUBLE PRECISION"),
        ("slots", "t3", "DOUBLE PRECISION"),
        ("slots", "t4", "DOUBLE PRECISION"),
        ("slots", "t5", "DOUBLE PRECISION"),
        ("slots", "vision_url", "TEXT"),
        ("trade_history", "vision_url", "TEXT"),
        ("moonbags", "leverage", "DOUBLE PRECISION"),
        ("moonbags", "order_id", "TEXT"),
        ("moonbags", "opened_at", "DOUBLE PRECISION")
    ]

    async with db.engine.begin() as conn:
        for table, col, col_type in migrations:
            try:
                logger.info(f"Adding column {col} to table {table}...")
                # PostgreSQL syntax for ADD COLUMN IF NOT EXISTS
                await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_type};"))
                logger.info(f"✅ Column {col} added or already exists in {table}.")
            except Exception as e:
                logger.error(f"❌ Error adding {col} to {table}: {e}")

    logger.info("🚀 Migration completed.")

if __name__ == "__main__":
    asyncio.run(migrate())
