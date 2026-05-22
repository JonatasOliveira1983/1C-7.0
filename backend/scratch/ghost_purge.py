# -*- coding: utf-8 -*-
import asyncio
import os
import sys
import json
import firebase_admin
from firebase_admin import credentials, db, firestore
from sqlalchemy import text

# Add backend to path
sys.path.append(os.getcwd())

from services.database_service import database_service, Slot

# Load .env
from dotenv import load_dotenv
load_dotenv()

DB_URL = os.getenv("FIREBASE_DATABASE_URL")
CRED_PATH = "serviceAccountKey.json"

async def total_purge():
    print("INICIANDO PURGA TOTAL DE FANTASMAS...")
    
    # 1. Postgres Purge
    try:
        await database_service.initialize()
        async with database_service.AsyncSessionLocal() as session:
            print("Limpando Postgres...")
            await session.execute(text("UPDATE banca_status SET saldo_total = 100.0, risco_real_percent = 0.0, slots_disponiveis = 4 WHERE id = 1"))
            await session.execute(text("TRUNCATE TABLE slots RESTART IDENTITY"))
            for i in range(1, 5):
                session.add(Slot(id=i, status_risco="LIVRE", leverage=50.0))
            await session.execute(text("TRUNCATE TABLE trade_history RESTART IDENTITY CASCADE"))
            await session.execute(text("TRUNCATE TABLE moonbags RESTART IDENTITY CASCADE"))
            await session.execute(text("TRUNCATE TABLE order_genesis RESTART IDENTITY CASCADE"))
            await session.commit()
            print("Postgres OK.")
    except Exception as e:
        print(f"Erro Postgres: {e}")

    # 2. Firebase RTDB Purge (Onde os fantasmas moram na UI)
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(CRED_PATH)
            firebase_admin.initialize_app(cred, {'databaseURL': DB_URL})
        
        print("Limpando RTDB (live_slots, banca_status)...")
        ref = db.reference("/")
        
        slots_reset = {}
        for i in range(1, 5):
            slots_reset[str(i)] = {"id": i, "symbol": None, "status_risco": "LIVRE", "pnl_percent": 0}
            
        ref.update({
            "live_slots": slots_reset,
            "banca_status": {
                "saldo_total": 100.0,
                "risco_real_percent": 0.0,
                "slots_disponiveis": 4,
                "last_update": 0
            },
            "orders_genesis": {},
            "trade_history": {}
        })
        print("RTDB OK.")
        
        # 3. Firestore Purge
        print("Limpando Firestore (slots_ativos)...")
        fs = firestore.client()
        for i in range(1, 5):
            fs.collection('slots_ativos').document(str(i)).set({
                "id": i, "symbol": None, "status_risco": "LIVRE", "pnl_percent": 0
            })
        print("Firestore OK.")

    except Exception as e:
        print(f"Erro Firebase: {e}")

    print("PURGA CONCLUIDA. Se os fantasmas voltarem, REINICIE O BOT IMEDIATAMENTE.")

if __name__ == "__main__":
    asyncio.run(total_purge())
