import asyncio
import os
import sys
import logging
import firebase_admin
from firebase_admin import credentials, db
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Adicionar o diretório backend ao path para importar config
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AuditSync")

async def audit_sync():
    logger.info("🔍 Iniciando Auditoria de Sincronia: PostgreSQL vs Firebase RTDB")
    
    # 1. Configurar Postgres
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("❌ DATABASE_URL não encontrada no ambiente!")
        return
        
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(db_url)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # 2. Configurar Firebase
    cred_path = os.path.join(os.path.dirname(__file__), "..", "serviceAccountKey.json")
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {'databaseURL': settings.FIREBASE_DATABASE_URL})
    
    ref = db.reference("/")
    
    try:
        # --- AUDITORIA DE SLOTS ---
        async with AsyncSessionLocal() as session:
            # Pegar slots do Postgres
            res = await session.execute(text("SELECT id, symbol, status_risco, order_id FROM slots ORDER BY id"))
            pg_slots = res.fetchall()
            
            # Pegar slots do Firebase
            fb_slots = ref.child("live_slots").get()
            if not fb_slots:
                # Tentar buscar como dicionário se a estrutura for diferente
                fb_slots = {}
            
            logger.info("\n--- [SLOTS COMPARISON] ---")
            discrepancies = 0
            for pg_s in pg_slots:
                s_id = pg_s[0]
                pg_symbol = pg_s[1]
                pg_status = pg_s[2]
                
                # Firebase pode ser uma lista ou dict
                fb_s = None
                if isinstance(fb_slots, list):
                    if s_id < len(fb_slots):
                        fb_s = fb_slots[s_id]
                elif isinstance(fb_slots, dict):
                    fb_s = fb_slots.get(str(s_id))
                
                fb_symbol = fb_s.get("symbol") if fb_s else "N/A"
                fb_status = fb_s.get("status_risco") if fb_s else "N/A"
                
                match = (pg_symbol == fb_symbol)
                status_icon = "✅" if match else "❌"
                if not match: discrepancies += 1
                
                logger.info(f"Slot {s_id}: PG({pg_symbol or 'LIVRE'}) vs FB({fb_symbol or 'LIVRE'}) {status_icon}")

        # --- AUDITORIA DE BANCA ---
        async with AsyncSessionLocal() as session:
            res = await session.execute(text("SELECT saldo_total FROM banca_status WHERE id = 1"))
            pg_banca = res.scalar()
            
            fb_banca_data = ref.child("banca_status").get()
            fb_banca = fb_banca_data.get("saldo_total") if fb_banca_data else "N/A"
            
            match = (str(pg_banca) == str(fb_banca))
            status_icon = "✅" if match else "❌"
            if not match: discrepancies += 1
            logger.info(f"\nBanca: PG(${pg_banca}) vs FB(${fb_banca}) {status_icon}")

        if discrepancies == 0:
            logger.info("\n💎 RESULTADO: Sincronia perfeita detectada!")
        else:
            logger.warning(f"\n⚠️ RESULTADO: {discrepancies} discrepâncias encontradas.")
            logger.info("Sugestão: Execute um script de reparo para forçar a soberania do Postgres.")

    except Exception as e:
        logger.error(f"Erro durante auditoria: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(audit_sync())
