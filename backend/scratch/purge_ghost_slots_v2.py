"""
purge_ghost_slots_v2.py — Operação Ghost Buster
Limpa slots fantasmas no Postgres que não possuem posição real em paper_positions.
"""
import asyncio
import os
import sys
import json
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

async def purge_ghost_slots():
    from services.sovereign_service import sovereign_service
    from services.database_service import database_service

    print("\n" + "="*60)
    print("  [GHOST BUSTER V2] - Operacao de Purga de Slots Fantasmas")
    print("="*60)

    # 1. Inicializar serviços
    await database_service.initialize()
    await sovereign_service.initialize()

    # 2. Ler paper_positions do arquivo em disco (fonte de verdade de posições reais em PAPER)
    paper_file = os.path.join(os.path.dirname(__file__), "..", "services", "paper_positions.v110.json")
    real_positions = set()
    try:
        with open(paper_file, "r", encoding="utf-8") as f:
            paper_data = json.load(f)
        for pos in paper_data.get("positions", []):
            sym = (pos.get("symbol") or "").replace(".P", "").upper()
            if sym:
                real_positions.add(sym)
        print(f"\n[INFO] Posicoes reais em paper_positions: {real_positions or '{vazio}'}")
    except Exception as e:
        print(f"[WARN] Nao foi possivel ler paper_positions: {e}")
        print("   Tratando como VAZIO (todas as posicoes em RAM foram perdidas).")

    # 3. Ler slots do Postgres
    db_slots = await database_service.get_active_slots()
    print(f"\n[INFO] ESTADO ATUAL DOS SLOTS NO POSTGRES ({len(db_slots)} slots):")
    print("-"*60)

    ghost_slots = []
    for slot in db_slots:
        slot_id = slot.get("id")
        symbol  = slot.get("symbol")
        opened_at = slot.get("opened_at", 0)
        status  = slot.get("status_risco", "?")

        if symbol:
            norm_sym = symbol.replace(".P", "").upper()
            age_h = (time.time() - float(opened_at or 0)) / 3600
            has_real = norm_sym in real_positions
            tag = "[REAL]" if has_real else f"[GHOST] (aberto ha {age_h:.1f}h)"
            print(f"  Slot {slot_id}: {symbol:<15} | {status:<15} | {tag}")
            if not has_real:
                ghost_slots.append(slot_id)
        else:
            print(f"  Slot {slot_id}: {'LIVRE':<15} | {status:<15} | [OK]")

    print("-"*60)
    print(f"\n[INFO] Ghost slots detectados: {ghost_slots}")

    if not ghost_slots:
        print("\n[OK] Nenhum ghost slot encontrado! Sistema saudavel.")
        return

    # 4. Confirmar e limpar
    print(f"\n[INFO] Limpando {len(ghost_slots)} ghost slot(s)...")
    for slot_id in ghost_slots:
        try:
            await sovereign_service.free_slot(slot_id, reason="[GHOST-BUSTER-V2] Slot fantasma sem posicao real detectado e purgado.")
            print(f"  [OK] Slot {slot_id} PURGADO com sucesso.")
        except Exception as e:
            print(f"  [ERRO] Erro ao purgar Slot {slot_id}: {e}")

    # 5. Verificação pós-purga
    print("\n[INFO] ESTADO POS-PURGA:")
    print("-"*60)
    db_slots_after = await database_service.get_active_slots()
    for slot in db_slots_after:
        symbol = slot.get("symbol")
        status = slot.get("status_risco", "?")
        print(f"  Slot {slot.get('id')}: {(symbol or 'LIVRE'):<15} | {status}")
    print("-"*60)
    print("\n[OK] Purga concluida! O Capitao pode retomar as operacoes.")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(purge_ghost_slots())
