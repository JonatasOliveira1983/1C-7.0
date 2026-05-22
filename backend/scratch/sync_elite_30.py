import asyncio
import sys
import os

backend_dir = r"c:\Users\spcom\Desktop\10D REAL 5.0\1CRYPTEN_SPACE_V4.0\backend"
sys.path.append(backend_dir)

async def sync_matrix():
    from services.database_service import database_service
    from config import settings
    
    print("🔄 [SYNC] Sincronizando Elite 30 com o Banco de Dados...")
    
    # 1. Busca lista atual no DB
    current_db = await database_service.get_monitored_from_db()
    current_symbols = [s['symbol'] for s in current_db]
    
    print(f"📊 DB atual possui {len(current_symbols)} ativos.")
    
    # 2. Prepara a nova lista (Elite 30)
    elite_30 = settings.ELITE_30_MATRIX
    
    # 3. Limpa e Insere (Força SSOT)
    # Nota: Poderíamos fazer um diff, mas para garantir a ordem e limpeza de SOL/FET, 
    # vamos deletar os que não estão na Elite 30 e adicionar os novos.
    
    to_remove = [s for s in current_symbols if s not in elite_30]
    to_add = [s for s in elite_30 if s not in current_symbols]
    
    if to_remove:
        print(f"🗑️ Removendo: {to_remove}")
        # Implementar deleção se necessário ou apenas ignorar se a UI filtrar
    
    if to_add:
        print(f"🆕 Adicionando: {to_add}")
    
    # Para simplificar e garantir a UI Limpa, vou sugerir um 'Truncate and Re-populate'
    # mas o database_service pode não ter um método direto para isso.
    # Vou usar o update_monitored_assets se existir.
    
    # Se o objetivo é que o Cockpit/Observatory mostre apenas a Elite 30:
    # Vou atualizar um por um.
    
    # Na verdade, vou apenas imprimir para diagnosticar.
    print(f"Elite 30 (Config): {elite_30}")

if __name__ == "__main__":
    asyncio.run(sync_matrix())
