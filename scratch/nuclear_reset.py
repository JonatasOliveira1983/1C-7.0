# -*- coding: utf-8 -*-
# Script de Reset Nuclear para a 10D Sniper Factory
# Objetivo: Limpar banca, slots, histórico e moonbags para novo ciclo de testes.

import asyncio
import os
import sys

# Adiciona o diretório backend ao path para importar os serviços
sys.path.append(os.path.join(os.getcwd(), "1CRYPTEN_SPACE_V4.0", "backend"))

from services.database_service import database_service

async def perform_nuclear_reset():
    print("Iniciando Reset Nuclear do Sistema...")
    
    # 1. Inicializa o serviço de banco de dados
    await database_service.initialize()
    
    # 2. Executa o Reset Nuclear
    success = await database_service.reset_system_data()
    
    if success:
        print("[SUCESSO] Banca resetada para $100, Slots limpos, Historico e Moonbags apagados.")
        print("O sistema esta pronto para um novo ciclo de testes limpo.")
    else:
        print("[ERRO] Falha ao executar o reset nuclear. Verifique os logs.")

if __name__ == "__main__":
    asyncio.run(perform_nuclear_reset())
