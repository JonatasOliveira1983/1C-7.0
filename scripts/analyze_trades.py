import sqlite3
import json

conn = sqlite3.connect("file:local_sniper.db?mode=ro", uri=True)
c = conn.cursor()

for tbl in ['sandbox_trades', 'sandbox_swing_trades']:
    print(f"\n=======================================================")
    print(f"       ANALISE FORENSE ESTRITA: {tbl}")
    print(f"=======================================================\n")
    
    rows = c.execute(f"SELECT id, symbol, strategy, direction, entry_price, current_price, stop_loss, target, max_roi, current_roi, pnl_pct, status, opened_at, closed_at, contract_meta FROM {tbl}").fetchall()
    
    closed_rows = [r for r in rows if r[11] != 'ACTIVE']
    active_rows = [r for r in rows if r[11] == 'ACTIVE']
    
    print(f"Total Registros: {len(rows)} | Ativos: {len(active_rows)} | Fechados: {len(closed_rows)}")
    
    if not closed_rows:
        print("Nenhum trade fechado.")
        continue
    
    trades_data = []
    for r in closed_rows:
        tid, sym, strat, direct, ep, cp, sl, tgt, max_r, cur_r, pnl_pct, status, op_at, cl_at, meta = r
        pnl = pnl_pct or 0.0
        meta_dict = {}
        if meta:
            try:
                meta_dict = json.loads(meta)
            except:
                pass
        
        margin = meta_dict.get('margin', 200.0)
        pnl_usd = meta_dict.get('realized_pnl_usd', (pnl / 100.0) * margin if margin else 0.0)
        
        trades_data.append({
            'id': tid,
            'symbol': sym,
            'strategy': strat,
            'direction': direct,
            'entry_price': ep,
            'exit_price': cp,
            'stop_loss': sl,
            'target': tgt,
            'max_roi': max_r,
            'pnl_pct': pnl,
            'pnl_usd': pnl_usd,
            'status': status,
            'opened_at': op_at,
            'closed_at': cl_at,
            'margin': margin,
            'meta': meta_dict
        })
        
    wins = [t for t in trades_data if t['pnl_pct'] > 0]
    losses = [t for t in trades_data if t['pnl_pct'] <= 0]
    
    total_trades = len(trades_data)
    win_rate = (len(wins) / total_trades) * 100 if total_trades else 0
    
    avg_win_pct = sum(t['pnl_pct'] for t in wins) / len(wins) if wins else 0
    avg_loss_pct = sum(t['pnl_pct'] for t in losses) / len(losses) if losses else 0
    
    avg_win_usd = sum(t['pnl_usd'] for t in wins) / len(wins) if wins else 0
    avg_loss_usd = sum(t['pnl_usd'] for t in losses) / len(losses) if losses else 0
    
    total_pnl_usd = sum(t['pnl_usd'] for t in trades_data)
    
    payoff_pct = abs(avg_win_pct / avg_loss_pct) if avg_loss_pct != 0 else 0
    payoff_usd = abs(avg_win_usd / avg_loss_usd) if avg_loss_usd != 0 else 0
    be_wr = (1 / (1 + payoff_pct)) * 100 if (1 + payoff_pct) != 0 else 0
    
    print(f"DESEMPENHO GLOBAL:")
    print(f"  * Total Trades: {total_trades}")
    print(f"  * Vitorias (Wins): {len(wins)} ({win_rate:.1f}%)")
    print(f"  * Derrotas (Losses): {len(losses)} ({100 - win_rate:.1f}%)")
    print(f"  * PnL Total Realizado Estimado: ${total_pnl_usd:.2f}")
    print(f"  * Ganho Medio por Vitoria: +{avg_win_pct:.2f}% (${avg_win_usd:.2f})")
    print(f"  * Perda Media por Derrota: {avg_loss_pct:.2f}% (${avg_loss_usd:.2f})")
    print(f"  * Assimetria R:R (Payoff Ratio): 1 : {1/payoff_pct:.2f} INVERSA! (Perda media e {1/payoff_pct:.2f}x MAIOR que o ganho medio)")
    print(f"  * Win Rate MINIMO Matematico para Breakeven: {be_wr:.1f}%\n")
    
    # Status de fechamento
    status_counts = {}
    for t in trades_data:
        st = t['status']
        status_counts[st] = status_counts.get(st, 0) + 1
    print("STATUS DE SAIDA:")
    for st, cnt in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        trades_st = [t for t in trades_data if t['status'] == st]
        st_pnl = sum(t['pnl_usd'] for t in trades_st)
        st_avg = sum(t['pnl_pct'] for t in trades_st) / cnt
        print(f"  * {st}: {cnt} trades ({cnt/total_trades*100:.1f}%) | PnL Acumulado: ${st_pnl:.2f} | Media ROI: {st_avg:.2f}%")
        
    # Estrategias
    strat_counts = {}
    for t in trades_data:
        st = t['strategy']
        strat_counts[st] = strat_counts.get(st, 0) + 1
    print("\nESTRATEGIAS EXECUTADAS:")
    for st, cnt in sorted(strat_counts.items(), key=lambda x: x[1], reverse=True):
        trades_st = [t for t in trades_data if t['strategy'] == st]
        st_wins = len([t for t in trades_st if t['pnl_pct'] > 0])
        st_pnl = sum(t['pnl_usd'] for t in trades_st)
        print(f"  * {st}: {cnt} trades | WR: {st_wins/cnt*100:.1f}% | PnL: ${st_pnl:.2f}")
        
    # Direcao (Bias)
    shorts = [t for t in trades_data if (t['direction'] or '').upper() in ['SELL', 'SHORT']]
    longs = [t for t in trades_data if (t['direction'] or '').upper() in ['BUY', 'LONG']]
    print(f"\nBIAS DIRECIONAL:")
    print(f"  * SHORT: {len(shorts)} ({len(shorts)/total_trades*100:.1f}%) | WR: {len([t for t in shorts if t['pnl_pct']>0])/len(shorts)*100 if shorts else 0:.1f}% | PnL: ${sum(t['pnl_usd'] for t in shorts):.2f}")
    print(f"  * LONG:  {len(longs)} ({len(longs)/total_trades*100:.1f}%) | WR: {len([t for t in longs if t['pnl_pct']>0])/len(longs)*100 if longs else 0:.1f}% | PnL: ${sum(t['pnl_usd'] for t in longs):.2f}")
    
    # Max ROI que o trade chegou a atingir vs o que realizou
    print("\nANALISE DE SAIDA PREMATURA / DESPERDICIO DE LUCRO:")
    left_on_table = []
    for t in trades_data:
        m_roi = t['max_roi'] or 0.0
        final_roi = t['pnl_pct']
        diff = m_roi - final_roi
        left_on_table.append(diff)
    avg_left = sum(left_on_table) / len(left_on_table) if left_on_table else 0
    print(f"  * Em media, o trade devolveu {avg_left:.2f}% de ROI a partir da maxima antes de fechar.")
    
    # Top 5 Maiores Ganhos e Perdas
    sorted_by_pct = sorted(trades_data, key=lambda x: x['pnl_pct'])
    print("\nTOP 5 MAIORES PERDAS:")
    for t in sorted_by_pct[:5]:
        print(f"  {t['symbol']} ({t['direction']}) | {t['strategy']} | ROI: {t['pnl_pct']:.2f}% (${t['pnl_usd']:.2f}) | Status: {t['status']} | MaxROI Atingido: {t['max_roi']}%")
        
    print("\nTOP 5 MAIORES GANHOS:")
    for t in sorted_by_pct[-5:][::-1]:
        print(f"  {t['symbol']} ({t['direction']}) | {t['strategy']} | ROI: {t['pnl_pct']:.2f}% (${t['pnl_usd']:.2f}) | Status: {t['status']} | MaxROI Atingido: {t['max_roi']}%")
