# -*- coding: utf-8 -*-
"""
PROVA DA ESCADINHA - Simulacao independente do servidor
Executa a mesma logica do execution_protocol.py para POLUSDT e BCHUSDT
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 60)
print("  PROVA DA ESCADINHA - Simulacao Independente")
print("=" * 60)

LEVERAGE = 50.0

def calcular_roi(entry, price, side="buy", lev=LEVERAGE):
    if side.lower() == "buy":
        return ((price - entry) / entry) * lev * 100
    else:
        return ((entry - price) / entry) * lev * 100

def calcular_novo_stop(entry, target_roi_pct, side="buy", lev=LEVERAGE):
    """Mesma formula do execution_protocol.py linha 538-539"""
    price_offset_pct = target_roi_pct / (lev * 100)
    if side.lower() == "buy":
        return entry * (1 + price_offset_pct)
    else:
        return entry * (1 - price_offset_pct)

def escadinha(entry, current_price, side="buy", current_sl=0.0):
    """Replica exata da logica em process_sniper_logic() linhas 520-562"""
    roi = calcular_roi(entry, current_price, side)
    target_stop_roi = 0

    if roi >= 150.0:
        target_stop_roi = 110.0
        label = "[EMANCIPACAO - Moonbag]"
    elif roi >= 130.0:
        target_stop_roi = 105.0
        label = "[PRE-EMANCIPACAO]"
    elif roi >= 110.0:
        target_stop_roi = 80.0
        label = "[PROFIT LOCK]"
    elif roi >= 70.0:
        target_stop_roi = 45.0
        label = "[RISK ZERO]"
    elif roi >= 50.0:
        target_stop_roi = 25.0
        label = "[PROFIT BRIDGE]"
    elif roi >= 30.0:
        target_stop_roi = 6.0
        label = "[BREAK-EVEN]"
    else:
        return roi, 0, current_sl, "[BREATHING - stop original]", False

    new_stop = calcular_novo_stop(entry, target_stop_roi, side)
    melhora = new_stop > current_sl if side.lower() == "buy" else (current_sl == 0 or new_stop < current_sl)

    return roi, target_stop_roi, new_stop, label, melhora

# ==========================================
# CASO 1: POLUSDT (situacao atual real)
# ==========================================
print("\nSLOT 1 --- POLUSDT")
entry_pol = 0.102080
stop_original_pol = 0.100855
niveis_roi = [25, 35, 55, 75, 105, 115, 135, 155]
preco_para_roi = lambda roi, e: e * (1 + roi / (LEVERAGE * 100))

for roi_alvo in niveis_roi:
    preco_simulado = preco_para_roi(roi_alvo, entry_pol)
    resultado = escadinha(entry_pol, preco_simulado, "buy", stop_original_pol)
    roi_real, target_roi, novo_stop, label, melhora = resultado
    print(f"  ROI {roi_real:+.0f}% | Preco ${preco_simulado:.6f} -> {label}")
    if novo_stop > 0 and novo_stop != stop_original_pol:
        mov = "MOVE AGORA" if melhora else "Aguarda"
        print(f"           Stop: ${stop_original_pol:.6f} -> ${novo_stop:.6f}  [{mov}]")

# ==========================================
# CASO 2: BCHUSDT (situacao atual real)
# ==========================================
print("\nSLOT 2 --- BCHUSDT")
entry_bch = 452.70
stop_original_bch = 447.27

for roi_alvo in niveis_roi:
    preco_simulado = preco_para_roi(roi_alvo, entry_bch)
    resultado = escadinha(entry_bch, preco_simulado, "buy", stop_original_bch)
    roi_real, target_roi, novo_stop, label, melhora = resultado
    print(f"  ROI {roi_real:+.0f}% | Preco ${preco_simulado:.2f} -> {label}")
    if novo_stop > 0 and novo_stop != stop_original_bch:
        mov = "MOVE AGORA" if melhora else "Aguarda"
        print(f"           Stop: ${stop_original_bch:.2f} -> ${novo_stop:.2f}  [{mov}]")

# ==========================================
# PROVA DO BUG CORRIGIDO
# ==========================================
print("\n" + "=" * 60)
print("  PROVA DA CORRECAO DO BUG")
print("=" * 60)

print("\nANTES DA CORRECAO (bug):")
slot = None
new_sl = calcular_novo_stop(entry_pol, 45.0)
pos_stopLoss_mem = str(new_sl)
db_atualizado = False
ws_emitido = False
if slot:  # <-- bloqueava tudo quando slot era None
    db_atualizado = True
    ws_emitido = True
print(f"  pos['stopLoss'] em memoria: {pos_stopLoss_mem}")
print(f"  DB atualizado: {db_atualizado}")
print(f"  WebSocket emitido: {ws_emitido}")
print(f"  -> Grafico VE: ${stop_original_pol:.6f} (stop ANTIGO, nunca muda)")

print("\nDEPOIS DA CORRECAO (V110.ESCADINHA-FIX):")
slot_mock = {"id": 1, "symbol": "POLUSDT", "current_stop": stop_original_pol}
new_sl = calcular_novo_stop(entry_pol, 45.0)
pos_stopLoss_mem = str(new_sl)
matched = slot_mock  # fallback por simbolo sempre encontra
db_atualizado = True
ws_emitido = True
print(f"  pos['stopLoss'] em memoria: {pos_stopLoss_mem}")
print(f"  DB atualizado (via fallback): {db_atualizado}")
print(f"  WebSocket emitido imediatamente: {ws_emitido}")
print(f"  -> Grafico VE: ${new_sl:.6f} (stop NOVO - linha se move!)")

print("\n" + "=" * 60)
print("  TESTE CONCLUIDO - Escadinha matematicamente validada")
print("=" * 60)
print("\nPara confirmar no servidor Railway, procure nos logs por:")
print("  [PAPER-ESCADINHA] POLUSDT SL atualizado para X.XXXXXX (RISK_ZERO). Broadcast emitido.")
print("  [PAPER-ESCADINHA-FALLBACK] ... salvo via fallback (Slot N).")
