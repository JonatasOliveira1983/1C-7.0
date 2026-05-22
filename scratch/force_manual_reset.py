
import asyncio
import asyncpg
import time

async def force_clean():
    db_url = "postgresql://postgres:JSLsEfBVPywKuYJSAypuNPVvIgYwGXzz@centerbeam.proxy.rlwy.net:54059/railway"
    
    print("[NUCLEAR-WIPE] Iniciando Purga Total no Postgres...")
    try:
        conn = await asyncpg.connect(db_url)
        
        # 1. Reset Banca para $100.00
        print("Banca: Resetando para $100.00...")
        await conn.execute("UPDATE banca_status SET saldo_total = 100.0, status = 'ESTADO_ZERO', risco_real_percent = 0.0 WHERE id = 1")
        
        # 2. Limpar Histórico de Trades e Gênese
        print("Historico: Limpando TradeHistory, Moonbags e Gênese...")
        await conn.execute("DELETE FROM trade_history")
        await conn.execute("DELETE FROM moonbags")
        await conn.execute("DELETE FROM order_genesis")
        
        # 3. Limpar Slots (LIVRE)
        print("Slots: Limpando posicoes ativas...")
        await conn.execute("""
            UPDATE slots 
            SET symbol = NULL, 
                side = NULL, 
                qty = 0.0, 
                entry_price = 0.0, 
                entry_margin = 0.0,
                status_risco = 'LIVRE',
                pnl_percent = 0.0,
                current_stop = 0.0,
                initial_stop = 0.0,
                target_price = 0.0,
                order_id = NULL,
                genesis_id = NULL,
                vision_url = NULL,
                pensamento = 'PURGA NUCLEAR REALIZADA',
                score = 0,
                timestamp_last_update = $1
        """, time.time())

        # 4. Limpar Ciclos do Vault
        print("Vault: Resetando Ciclos...")
        await conn.execute("UPDATE vault_cycles SET sniper_wins = 0, cycle_profit = 0, cycle_losses = 0, total_trades_cycle = 0, accumulated_vault = 0 WHERE id = 1")

        # 5. Verify
        banca = await conn.fetchrow("SELECT saldo_total, status FROM banca_status WHERE id = 1")
        slots = await conn.fetch("SELECT id, symbol, status_risco FROM slots ORDER BY id")
        
        print("\nFinal State Audit:")
        print(f"Banca: ${banca['saldo_total']} ({banca['status']})")
        for s in slots:
            print(f"Slot {s['id']}: {s['symbol']} ({s['status_risco']})")
            
        await conn.close()
        print("\n[NUCLEAR-WIPE] Sucesso! Sistema resetado para o Estado Zero.")
        
    except Exception as e:
        print(f"[NUCLEAR-WIPE] ERRO: {e}")

if __name__ == "__main__":
    asyncio.run(force_clean())
