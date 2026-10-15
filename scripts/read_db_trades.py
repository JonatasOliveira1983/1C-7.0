import sqlite3
import os
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

db_path = os.path.join('backend', 'local_sniper.db')
if not os.path.exists(db_path):
    print("Database file does not exist:", db_path)
    sys.exit(0)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("PRAGMA table_info(sandbox_trades);")
cols = [c[1] for c in cur.fetchall()]

cur.execute("SELECT * FROM sandbox_trades ORDER BY rowid ASC;")
all_rows = cur.fetchall()

def analyze_batch(rows, title):
    wins = 0
    losses = 0
    breakevens = 0
    win_pnl = 0.0
    loss_pnl = 0.0
    total_pnl = 0.0
    total_fees = 0.0
    symbols_stat = {}

    for r in rows:
        d = dict(zip(cols, r))
        cm = d.get('contract_meta')
        if isinstance(cm, str):
            try: cm = json.loads(cm)
            except: cm = {}
        elif not isinstance(cm, dict): cm = {}
        
        net_pnl = float(cm.get('net_pnl_usd') or d.get('pnl_usd') or 0.0)
        fees = float(cm.get('total_fees_usd') or 0.0)
        pnl_pct = float(d.get('pnl_pct') or cm.get('net_roi') or 0.0)
        sym = d.get('symbol') or 'UNKNOWN'
        
        total_pnl += net_pnl
        total_fees += fees
        
        if net_pnl > 0.01:
            wins += 1
            win_pnl += net_pnl
        elif net_pnl < -0.01:
            losses += 1
            loss_pnl += abs(net_pnl)
        else:
            breakevens += 1
            
        if sym not in symbols_stat:
            symbols_stat[sym] = {'count': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0}
        symbols_stat[sym]['count'] += 1
        symbols_stat[sym]['pnl'] += net_pnl
        if net_pnl > 0.01:
            symbols_stat[sym]['wins'] += 1
        elif net_pnl < -0.01:
            symbols_stat[sym]['losses'] += 1

    total_closed = wins + losses + breakevens
    wr = (wins / total_closed * 100.0) if total_closed > 0 else 0.0
    pf = (win_pnl / loss_pnl) if loss_pnl > 0 else 999.0

    print(f"\n=======================================================")
    print(f" {title} ")
    print(f"=======================================================")
    print(f"  • Total Trades: {total_closed}")
    print(f"  • Wins: {wins} | Losses: {losses} | BE: {breakevens}")
    print(f"  • Win Rate: {wr:.1f}%")
    print(f"  • PnL Líquido: ${total_pnl:.2f}")
    print(f"  • Ganhos Brutos: +${win_pnl:.2f}")
    print(f"  • Perdas Brutas: -${loss_pnl:.2f}")
    print(f"  • Taxas e Slippage: ${total_fees:.2f}")
    print(f"  • Fator de Lucro (Profit Factor): {pf:.2f}")
    print(f"  • Desempenho por Ativo:")
    for s, st in sorted(symbols_stat.items(), key=lambda x: x[1]['pnl'], reverse=True):
        print(f"    - {s}: {st['count']} trades | W:{st['wins']} L:{st['losses']} | PnL: ${st['pnl']:.2f}")

    return {
        'total': total_closed, 'wins': wins, 'losses': losses,
        'pnl': total_pnl, 'wr': wr, 'pf': pf, 'win_pnl': win_pnl, 'loss_pnl': loss_pnl
    }

# 1º Período: os primeiros 15 trades
p1_rows = all_rows[:15]
# 2º Período: os últimos 10 trades (após os ajustes do Farol Macro e filtro)
p2_rows = all_rows[15:]

analyze_batch(p1_rows, "1º PERÍODO (PRIMEIRAS 4 HORAS - ANTES DOS AJUSTES)")
analyze_batch(p2_rows, "2º PERÍODO (ÚLTIMAS 4 HORAS - APÓS AJUSTES DO FAROL MACRO)")
analyze_batch(all_rows, "CONSOLIDADO GERAL (8 HORAS TOTAIS)")

print("\n--- DETALHE DOS TRADES DO 2º PERÍODO ---")
for i, r in enumerate(p2_rows):
    d = dict(zip(cols, r))
    cm = d.get('contract_meta')
    if isinstance(cm, str):
        try: cm = json.loads(cm)
        except: cm = {}
    elif not isinstance(cm, dict): cm = {}
    net_pnl = float(cm.get('net_pnl_usd') or d.get('pnl_usd') or 0.0)
    pnl_pct = float(d.get('pnl_pct') or cm.get('net_roi') or 0.0)
    print(f"  {i+1}. {d.get('created_at')} | {d.get('symbol')} {d.get('direction')} | Status: {d.get('status')} | ROI: {pnl_pct:.2f}% | PnL: ${net_pnl:.2f} | Rationale: {cm.get('rationale','')[:65]}")

cur.execute("SELECT * FROM sandbox_trades WHERE status = 'OPEN';")
open_rows = cur.fetchall()
print(f"\n--- POSIÇÕES ABERTAS NO MOMENTO ({len(open_rows)}) ---")
for r in open_rows:
    d = dict(zip(cols, r))
    cm = d.get('contract_meta') or {}
    if isinstance(cm, str):
        try: cm = json.loads(cm)
        except: cm = {}
    print(f"  -> {d.get('symbol')} {d.get('direction')} | Entrada: ${d.get('entry_price')} | SL: ${d.get('stop_loss')} | TP: ${d.get('take_profit')} | Lev: {d.get('leverage')}x | Criado: {d.get('created_at')}")
