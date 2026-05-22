
import asyncio
import os
import sys
from datetime import datetime

# Adicionar o path do backend para importar o database_service
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "1CRYPTEN_SPACE_V4.0", "backend")
sys.path.append(backend_path)

from services.database_service import database_service

async def analyze():
    print("--- ANALISANDO ESTADO DO SISTEMA 10D REAL 5.0 ---")
    await database_service.initialize()
    
    # 1. Banca Status
    banca = await database_service.get_banca_status()
    print(f"\n[BANCA]")
    print(f" - Saldo Total: ${banca.get('saldo_total', 0):.2f}")
    print(f" - Risco Real: {banca.get('risco_real_percent', 0):.2f}%")
    print(f" - Slots Disponíveis: {banca.get('slots_disponiveis', 0)}")
    print(f" - Status: {banca.get('status', 'N/A')}")
    
    # 2. Slots Ativos
    slots = await database_service.get_active_slots()
    print(f"\n[SLOTS ATIVOS]")
    active_count = 0
    for s in slots:
        if s.get('symbol'):
            active_count += 1
            print(f"\nSlot {s['id']}: {s['symbol']} ({s['side']})")
            print(f" - Entry: ${s['entry_price']:.4f}")
            print(f" - Current Stop: ${s['current_stop']:.4f}")
            print(f" - PnL: {s['pnl_percent']:.2f}%")
            print(f" - Status Risco: {s['status_risco']}")
            print(f" - Pensamento: {s['pensamento']}")
    
    if active_count == 0:
        print(" - Nenhum slot ativo no momento.")
        
    # 3. Moonbags
    moons = await database_service.get_moonbags()
    print(f"\n[MOONBAGS]")
    if moons:
        for m in moons:
            print(f" - {m['symbol']}: Side={m['side']}, Qty={m['qty']}, Entry=${m['entry_price']:.4f}, PnL={m['pnl_percent']:.2f}%")
    else:
        print(" - Nenhuma Moonbag ativa.")

    # 4. Histórico Recente
    history = await database_service.get_trade_history(limit=10)
    print(f"\n[HISTÓRICO RECENTE (Últimos 10)]")
    if history:
        for h in history:
            ts = h['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(h['timestamp'], datetime) else h['timestamp']
            print(f" - {ts} | {h['symbol']} | {h['side']} | PnL: {h['pnl_percent']:.2f}% (${h['pnl']:.2f}) | Reason: {h['close_reason']}")
    else:
        print(" - Nenhum histórico encontrado.")

    # 5. Ciclo do Vault
    vault = await database_service.get_vault_cycle()
    if vault:
        print(f"\n[VAULT CYCLE]")
        print(f" - Ciclo Atual: {vault.get('cycle_number')}")
        print(f" - Sniper Wins: {vault.get('sniper_wins')}/10")
        print(f" - Lucro do Ciclo: ${vault.get('cycle_profit', 0):.2f}")
        print(f" - Total Trades: {vault.get('total_trades_cycle', 0)}")

if __name__ == "__main__":
    asyncio.run(analyze())
