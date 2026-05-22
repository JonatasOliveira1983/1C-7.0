import json
import os

backup_path = r'c:\Users\spcom\Desktop\10D REAL 4.0\1CRYPTEN_SPACE_V4.0\backend\trade_history_backup.json'

def parse_multi_json(path):
    results = []
    if not os.path.exists(path):
        return results
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        
    # Tenta carregar como lista normal primeiro
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
        return [data]
    except json.JSONDecodeError:
        # Se falhar, tenta ler como objetos sequenciais
        # Procura por }{ ou \n
        import re
        # Uma abordagem simples: separa por '}{' e tenta reconstruir
        # Mas o erro "Extra data" costuma ser objetos um depois do outro
        decoder = json.JSONDecoder()
        pos = 0
        while pos < len(content):
            try:
                obj, next_pos = decoder.raw_decode(content, pos)
                results.append(obj)
                pos = next_pos
                # Pula espaços em branco/newlines entre objetos
                while pos < len(content) and content[pos].isspace():
                    pos += 1
            except Exception as e:
                print(f"Erro ao decodificar na posição {pos}: {e}")
                break
    return results

data = parse_multi_json(backup_path)
print(f"\nTotal de registros encontrados: {len(data)}")

print(f"\nÚltimos 15 trades do histórico:")
for r in data[-15:]:
    symbol = r.get('symbol', 'N/A')
    side = r.get('side', 'N/A')
    pnl = r.get('pnl_percent', 0)
    reason = r.get('close_reason', 'N/A')
    date = r.get('closed_at', r.get('timestamp', 'N/A'))
    
    status = "✅ WIN" if pnl > 0 else "❌ LOSS"
    print(f"[{date}] {symbol} | {side} | {status} | PNL: {pnl:.2f}% | Motivo: {reason}")
    
    # Busca por padrões de armadilha no log/razão
    if 'trap' in str(reason).lower() or 'armadilha' in str(reason).lower() or pnl < -5:
        print(f"  ⚠️ ALERTA: Possível armadilha institucional detectada ou loss alto.")
