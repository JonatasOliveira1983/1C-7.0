import asyncio
import asyncpg

async def check():
    db_url = "postgresql://postgres:JSLsEfBVPywKuYJSAypuNPVvIgYwGXzz@centerbeam.proxy.rlwy.net:54059/railway"
    conn = await asyncpg.connect(db_url)
    slots = await conn.fetch("SELECT id, symbol, status_risco, genesis_id, entry_price FROM slots ORDER BY id")
    print("ID | SYMBOL | STATUS | GENESIS | ENTRY")
    for s in slots:
        print(f"{s['id']} | {s['symbol']} | {s['status_risco']} | {s['genesis_id']} | {s['entry_price']}")
    
    banca = await conn.fetchrow("SELECT saldo_total, status FROM banca_status WHERE id = 1")
    print(f"\nBANCA: ${banca['saldo_total']} ({banca['status']})")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check())
