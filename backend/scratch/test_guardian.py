# -*- coding: utf-8 -*-
import asyncio
import logging
import time
import sys
import os

# Adiciona o diretório backend ao path do Python para poder importar as dependências
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.portfolio_guardian import portfolio_guardian
from services.okx_service import okx_service
from services.anti_slippage import anti_slippage_engine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TestGuardian")

async def run_simulation():
    logger.info("🧪 [TESTE] Iniciando simulação da Máquina de Estados do Portfolio Guardian...")
    
    # Verifica parâmetros configurados
    logger.info(f"⚙️ Config: Activation Trigger = {portfolio_guardian.activation_trigger}%")
    logger.info(f"⚙️ Config: Trailing Margin = {portfolio_guardian.trailing_margin}%")
    
    # 1. Estado inicial: OBSERVANDO
    logger.info("--- Fase 1: OBSERVANDO ---")
    assert portfolio_guardian.state == "OBSERVANDO", f"Esperado OBSERVANDO, obtido {portfolio_guardian.state}"
    
    # Simula posição inicial com lucro baixo (ex: 20% de ROI)
    # Margem: 100 USD, PnL: 20 USD -> ROI = 20%
    pos_mock = [
        {"instId": "BTC-USDT-SWAP", "posSide": "long", "pos": "0.1", "upl": "20.0", "margin": "100.0", "mgnVal": "100.0"}
    ]
    await portfolio_guardian._process_evaluation(pos_mock)
    assert portfolio_guardian.state == "OBSERVANDO", f"Esperado OBSERVANDO com 20% ROI, obtido {portfolio_guardian.state}"
    
    # 2. Atingindo o Trigger de Ativação (ex: 75% ROI, que é >= 70%)
    logger.info("--- Fase 2: Ativando Trailing-Stop ---")
    pos_mock[0]["upl"] = "75.0"
    await portfolio_guardian._process_evaluation(pos_mock)
    assert portfolio_guardian.state == "RASTREAMENTO_ATIVO", f"Esperado RASTREAMENTO_ATIVO com 75% ROI, obtido {portfolio_guardian.state}"
    assert portfolio_guardian.max_roi_registered == 75.0, f"Esperado pico de 75.0, obtido {portfolio_guardian.max_roi_registered}"
    
    # 3. Lucro sobe mais (ex: 90% ROI)
    logger.info("--- Fase 3: Elevando o pico de ROI ---")
    pos_mock[0]["upl"] = "90.0"
    await portfolio_guardian._process_evaluation(pos_mock)
    assert portfolio_guardian.state == "RASTREAMENTO_ATIVO", f"Esperado RASTREAMENTO_ATIVO com 90% ROI, obtido {portfolio_guardian.state}"
    assert portfolio_guardian.max_roi_registered == 90.0, f"Esperado pico de 90.0, obtido {portfolio_guardian.max_roi_registered}"

    # 4. Pequeno recuo que NÃO dispara o corte (ex: cai para 80% ROI, que é > 90 - 15 = 75%)
    logger.info("--- Fase 4: Pequeno recuo (sem corte) ---")
    pos_mock[0]["upl"] = "80.0"
    await portfolio_guardian._process_evaluation(pos_mock)
    assert portfolio_guardian.state == "RASTREAMENTO_ATIVO", f"Esperado continuar RASTREAMENTO_ATIVO com 80% ROI, obtido {portfolio_guardian.state}"
    
    # 5. Recuo crítico que DISPARA o corte (ex: cai para 74% ROI, que é < 90 - 15 = 75%)
    logger.info("--- Fase 5: Recuo Crítico (Dispara Knife-Drop) ---")
    pos_mock[0]["upl"] = "74.0"
    await portfolio_guardian._process_evaluation(pos_mock)
    # Após a execução do Knife-Drop, o estado deve resetar para OBSERVANDO
    assert portfolio_guardian.state == "OBSERVANDO", f"Esperado retonar a OBSERVANDO pós Knife-Drop, obtido {portfolio_guardian.state}"
    assert portfolio_guardian.max_roi_registered == 0.0, f"Esperado pico resetado para 0, obtido {portfolio_guardian.max_roi_registered}"
    
    logger.info("✅ [TESTE-SUCCESS] A máquina de estados do Portfolio Guardian funcionou PERFEITAMENTE!")
    
    # 6. Testando Sharding de Cohorts do Anti-Slippage
    logger.info("--- Fase 6: Testando Sharding e Equilíbrio de Cohorts ---")
    cohorts = anti_slippage_engine.sharding_cohort_distribution(None)  # Usa mock de 100 usuários
    
    # Verifica o balanceamento
    sums = {}
    for c_name, members in cohorts.items():
        sums[c_name] = sum(m.get("equity", 0.0) for m in members)
        
    logger.info(f"Estatísticas dos saldos das turmas: {sums}")
    max_diff = max(sums.values()) - min(sums.values())
    logger.info(f"Diferença máxima de saldo consolidado entre turmas: ${max_diff:.2f}")
    assert max_diff < 5000.0, f"Diferença entre turmas muito alta! Balanceamento falhou: {max_diff}"
    
    logger.info("✅ [TESTE-SUCCESS] O Sharding Greedy Snake balanceou as turmas de forma espetacular!")

if __name__ == "__main__":
    asyncio.run(run_simulation())
