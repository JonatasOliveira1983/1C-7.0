import json
import os
import sys

# Força UTF-8 no output do terminal
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

backup_path = r'c:\Users\spcom\Desktop\10D REAL 4.0\1CRYPTEN_SPACE_V4.0\backend\trade_history_backup.json'

def parse_multi_json(path):
    results = []
    if not os.path.exists(path):
        return results
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
        return [data]
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        pos = 0
        while pos < len(content):
            try:
                obj, next_pos = decoder.raw_decode(content, pos)
                results.append(obj)
                pos = next_pos
                while pos < len(content) and content[pos].isspace():
                    pos += 1
            except Exception:
                break
    return results

data = parse_multi_json(backup_path)
print(f"Total de registros: {len(data)}")

print("\n--- ANALISE DE HISTORICO ---")
for r in data[-20:]:
    symbol = r.get('symbol', 'N/A')
    side = r.get('side', 'N/A')
    pnl = r.get('pnl_percent', 0.0)
    if pnl is None: pnl = 0.0
    reason = r.get('close_reason', 'N/A')
    date = r.get('closed_at', r.get('timestamp', 'N/A'))
    
    win_loss = "WIN" if pnl > 0 else "LOSS"
    print(f"[{date}] {symbol} | {side} | {win_loss} | PNL: {pnl:.2f}% | Motivo: {reason}")
    
    # Detecção de armadilha
    is_trap = any(kw in str(reason).lower() for kw in ['trap', 'armadilha', 'fakeout', 'manipulation'])
    if is_trap or pnl < -4:
        print(f"  !!! POSSIVEL ARMADILHA INSTITUCIONAL !!!")

print("\n--- RESUMO ESTATISTICO ---")
losses = [r for r in data if (r.get('pnl_percent') or 0) < 0]
traps = [r for r in data if any(kw in str(r.get('close_reason', '')).lower() for kw in ['trap', 'armadilha', 'fakeout'])]

print(f"Total Trades: {len(data)}")
print(f"Total Losses: {len(losses)}")
print(f"Possiveis Armadilhas: {len(traps)}")
