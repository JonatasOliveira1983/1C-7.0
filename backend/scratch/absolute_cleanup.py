# -*- coding: utf-8 -*-
import sqlite3
import os
import sys
import asyncio

# Garante que o diretório backend esteja no path para carregar o database_service
sys.path.append(os.path.join(os.getcwd(), 'backend'))

def cleanup_sqlite(db_path):
    print(f"[*] Purgando slots no SQLite: {db_path}...")
    if not os.path.exists(db_path):
        print(f"[!] Arquivo nao encontrado: {db_path}. Pulando.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Garante que a tabela slots exista antes de limpar
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='slots';")
        if not cursor.fetchone():
            print(f"[!] Tabela 'slots' nao existe no banco {db_path}. Pulando.")
            conn.close()
            return
            
        # Purgando slots de 1 a 4
        for i in range(1, 5):
            cursor.execute("""
                UPDATE slots SET 
                    symbol = NULL,
                    side = NULL,
                    qty = 0.0,
                    entry_price = 0.0,
                    entry_margin = 0.0,
                    current_stop = 0.0,
                    initial_stop = 0.0,
                    order_id = NULL,
                    target_price = 0.0,
                    status_risco = 'LIVRE',
                    pnl_percent = 0.0,
                    strategy = NULL,
                    strategy_label = NULL,
                    genesis_id = NULL,
                    opened_at = NULL,
                    pensamento = NULL,
                    score = 0.0
                WHERE id = ?;
            """, (i,))
        
        conn.commit()
        conn.close()
        print(f"[+] SQLite {db_path} higienizado com sucesso!")
    except Exception as e:
        print(f"[-] Erro ao higienizar SQLite {db_path}: {e}")

async def cleanup_postgres():
    print("[*] Purgando slots no PostgreSQL de Producao (Railway)...")
    
    # URL de produção explícita
    prod_url = "postgresql+asyncpg://postgres:JSLsEfBVPywKuYJSAypuNPVvIgYwGXzz@centerbeam.proxy.rlwy.net:54059/railway"
    
    try:
        from services.database_service import DatabaseService
        # Sobrescreve a inicialização do DatabaseService para forçar a URL de produção
        db_service = DatabaseService()
        db_service.engine = None
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.ext.asyncio import AsyncSession
        
        db_service.engine = create_async_engine(prod_url, echo=False)
        db_service.AsyncSessionLocal = sessionmaker(
            db_service.engine, class_=AsyncSession, expire_on_commit=False
        )
        
        await db_service.initialize()
        
        # Reseta os slots de 1 a 4
        for i in range(1, 5):
            empty_data = {
                "symbol": None,
                "side": None,
                "qty": 0.0,
                "entry_price": 0.0,
                "entry_margin": 0.0,
                "current_stop": 0.0,
                "initial_stop": 0.0,
                "order_id": None,
                "target_price": 0.0,
                "status_risco": "LIVRE",
                "pnl_percent": 0.0,
                "strategy": None,
                "strategy_label": None,
                "genesis_id": None,
                "opened_at": None,
                "pensamento": None,
                "score": 0.0
            }
            await db_service.update_slot(i, empty_data)
            
        print("[+] PostgreSQL de Producao (Railway) higienizado com sucesso!")
    except Exception as e:
        print(f"[-] Erro ao higienizar PostgreSQL: {e}")

async def main():
    # 1. Higienizar SQLite da raiz
    cleanup_sqlite("local_sniper.db")
    
    # 2. Higienizar SQLite do backend
    cleanup_sqlite("backend/local_sniper.db")
    
    # 3. Higienizar Postgres de produção
    await cleanup_postgres()

if __name__ == "__main__":
    asyncio.run(main())
