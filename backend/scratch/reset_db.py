import asyncio
import os
import sys
from dotenv import load_dotenv

# Carregar variáveis do .env do backend
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(env_path)

# Adicionar backend ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from services.database_service import database_service

async def reset_database():
    print("Iniciando limpeza do banco de dados (Hard Reset)...")
    
    # Inicializa engine
    await database_service.initialize()
    
    async with database_service.engine.begin() as conn:
        print("1. Limpando Histórico de Trades e Moonbags...")
        await conn.execute(text("DELETE FROM trade_history"))
        await conn.execute(text("DELETE FROM moonbags"))
        await conn.execute(text("DELETE FROM order_genesis"))
        await conn.execute(text("DELETE FROM vault_withdrawals"))
        
        print("2. Resetando Slots...")
        # Limpa conteúdo dos slots mas mantém as linhas (1 a 4)
        await conn.execute(text("""
            UPDATE slots SET 
                symbol = NULL, 
                side = NULL, 
                qty = 0.0, 
                entry_price = 0.0, 
                entry_margin = 0.0,
                current_stop = 0.0, 
                initial_stop = 0.0, 
                target_price = 0.0, 
                liq_price = 0.0, 
                pnl_percent = 0.0, 
                status_risco = 'LIVRE',
                order_id = NULL,
                genesis_id = NULL,
                symbol_adx = 0.0,
                market_regime = NULL,
                unified_confidence = 50,
                fleet_intel = NULL,
                pensamento = NULL,
                timestamp_last_intel = 0.0,
                sentinel_first_hit_at = 0.0,
                timestamp_last_update = 0.0,
                opened_at = 0.0
        """))
        
        print("3. Resetando Banca (BancaStatus) para $100.0...")
        await conn.execute(text("""
            UPDATE banca_status SET 
                saldo_total = 100.0, 
                risco_real_percent = 0.0, 
                slots_disponiveis = 4, 
                status = 'FACTORY_RESET'
        """))
        
        print("4. Resetando Vault Cycles...")
        await conn.execute(text("""
            UPDATE vault_cycles SET 
                sniper_wins = 0, 
                cycle_number = 1, 
                cycle_profit = 0.0, 
                cycle_losses = 0.0,
                vault_total = 0.0,
                total_trades_cycle = 0,
                cycle_gains_count = 0,
                cycle_losses_count = 0,
                accumulated_vault = 0.0,
                used_symbols_in_cycle = '[]'::jsonb,
                cycle_start_bankroll = 100.0,
                next_entry_value = 0.0,
                mega_cycle_wins = 0,
                mega_cycle_total = 0,
                mega_cycle_number = 1,
                mega_cycle_profit = 0.0,
                order_ids_processed = '[]'::jsonb
        """))
        
        print("5. Limpando System State (Paper Engine)...")
        await conn.execute(text("DELETE FROM system_state"))
        
    print("✅ RESET CONCLUÍDO COM SUCESSO! Sistema pronto para iniciar.")

if __name__ == "__main__":
    asyncio.run(reset_database())
