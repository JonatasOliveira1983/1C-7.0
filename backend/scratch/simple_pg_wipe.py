
import asyncio
import os
import sys
from datetime import datetime

# Garantir que o path inclua o backend
sys.path.append(os.getcwd())

from services.database_service import database_service
from sqlalchemy import text

async def simple_pg_wipe():
    log_file = "wipe_output.txt"
    with open(log_file, "w") as f:
        f.write(f"--- START PG WIPE {datetime.now()} ---\n")
        try:
            await database_service.initialize()
            f.write("DB Initialized\n")
            
            async with database_service.AsyncSessionLocal() as session:
                # 1. Wipe Slots
                await session.execute(text("UPDATE slots SET symbol=NULL, side=NULL, status_risco='LIVRE', qty=0, entry_price=0, pnl_percent=0"))
                f.write("Slots table wiped\n")
                
                # 2. Wipe Paper State
                await session.execute(text("DELETE FROM system_state WHERE key = 'paper_engine_state'"))
                f.write("Paper engine state deleted\n")
                
                await session.commit()
                f.write("Changes committed successfully\n")
        except Exception as e:
            f.write(f"ERROR: {e}\n")
        f.write("--- END PG WIPE ---\n")

if __name__ == "__main__":
    asyncio.run(simple_pg_wipe())
