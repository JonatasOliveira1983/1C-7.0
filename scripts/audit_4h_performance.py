import httpx
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

try:
    r = httpx.get('http://127.0.0.1:8085/api/sandbox/trades?limit=100', timeout=15)
    trades = r.json()
except Exception as e:
    print(f"Erro ao buscar trades: {e}")
    trades = []

try:
    s_resp = httpx.get('http://127.0.0.1:8085/api/slots', timeout=15)
    slots = s_resp.json()
except Exception as e:
    slots = []

try:
    b_resp = httpx.get('http://127.0.0.1:8085/api/sandbox/unified-state', timeout=15)
    banca = b_resp.json()
except Exception as e:
    banca = {}

try:
    p_resp = httpx.get('http://127.0.0.1:8085/api/v1/hermes/laya/pulse', timeout=15)
    pulse = p_resp.json()
except Exception as e:
    pulse = {}

print("=================================================================")
print("           RELATÓRIO DE AUDITORIA FORENSE - 4 HORAS             ")
print("=================================================================")
print(f"Saldo Total / Equity: ${banca.get('total_equity', 0):.2f}")
print(f"Saldo Disponível:     ${banca.get('available_balance', 0):.2f}")
print(f"PnL Realizado Total:  ${banca.get('total_pnl_usd', 0):.2f}")
print(f"Posições Ativas:      {len(slots)}")
print(f"Total Trades no Histórico: {len(trades)}")
print(f"Modo Atual da Laya:   {pulse.get('regime_mode')} (ADX: {pulse.get('master_adx')})")
print(f"Última Varredura:     {pulse.get('last_scan_ago_s')}s atrás")
print("=================================================================\n")

total_pnl = 0.0
total_fees = 0.0
wins = 0
losses = 0
breakevens = 0
win_pnl = 0.0
loss_pnl = 0.0

symbols_stat = {}
strategies_stat = {}

for t in trades:
    meta = t.get('contract_meta', {}) or {}
    net_pnl = float(meta.get('net_pnl_usd', 0.0) or t.get('pnl_usd', 0.0) or 0.0)
    pnl_pct = float(t.get('pnl_pct', 0.0) or meta.get('net_roi', 0.0) or 0.0)
    fees = float(meta.get('total_fees_usd', 0.0) or 0.0)
    sym = t.get('symbol', 'UNKNOWN')
    strat = t.get('strategy', 'UNKNOWN')
    status = t.get('status', 'UNKNOWN')
    
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

    if strat not in strategies_stat:
        strategies_stat[strat] = {'count': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0}
    strategies_stat[strat]['count'] += 1
    strategies_stat[strat]['pnl'] += net_pnl
    if net_pnl > 0.01:
        strategies_stat[strat]['wins'] += 1
    elif net_pnl < -0.01:
        strategies_stat[strat]['losses'] += 1

total_closed = wins + losses + breakevens
win_rate = (wins / total_closed * 100.0) if total_closed > 0 else 0.0
profit_factor = (win_pnl / loss_pnl) if loss_pnl > 0 else 999.0

print(f"📊 DESEMPENHO GLOBAL:")
print(f"  • Total Trades Fechados: {total_closed}")
print(f"  • Trades Vencedores (Wins): {wins}")
print(f"  • Trades Perdedores (Losses): {losses}")
print(f"  • Breakevens: {breakevens}")
print(f"  • Taxa de Acerto (Win Rate): {win_rate:.1f}%")
print(f"  • PnL Líquido Total: ${total_pnl:.2f}")
print(f"  • Total Ganho com Wins: +${win_pnl:.2f}")
print(f"  • Total Perdido com Losses: -${loss_pnl:.2f}")
print(f"  • Taxas e Slippage: ${total_fees:.2f}")
print(f"  • Fator de Lucro (Profit Factor): {profit_factor:.2f}\n")

print("🪙 PERFORMANCE POR PAR:")
for s, st in sorted(symbols_stat.items(), key=lambda x: x[1]['pnl'], reverse=True):
    wr = (st['wins'] / st['count'] * 100) if st['count'] > 0 else 0
    print(f"  [{s}] {st['count']} trades | Win: {st['wins']} | Loss: {st['losses']} | WR: {wr:.0f}% | PnL: ${st['pnl']:.2f}")

print("\n🧠 PERFORMANCE POR ESTRATÉGIA:")
for strat, st in sorted(strategies_stat.items(), key=lambda x: x[1]['pnl'], reverse=True):
    wr = (st['wins'] / st['count'] * 100) if st['count'] > 0 else 0
    print(f"  [{strat}] {st['count']} trades | Win: {st['wins']} | Loss: {st['losses']} | WR: {wr:.0f}% | PnL: ${st['pnl']:.2f}")

print("\n📜 HISTÓRICO COMPLETO DOS TRADES EXECUTADOS:")
for i, t in enumerate(trades):
    meta = t.get('contract_meta', {}) or {}
    print(f"  {i+1}. {t.get('created_at', '--')} | {t.get('symbol')} {t.get('direction')} | Status: {t.get('status')} | ROI: {t.get('pnl_pct', 0):.2f}% | PnL: ${meta.get('net_pnl_usd', 0):.2f} | Rationale: {meta.get('rationale', '')[:65]}")
