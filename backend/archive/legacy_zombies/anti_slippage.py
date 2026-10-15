# -*- coding: utf-8 -*-
import asyncio
import logging
import random
from typing import List, Dict, Any
from config import settings
from services.okx_service import okx_service
from services.hermes_broker import hermes_broker_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AntiSlippage")

class AntiSlippageEngine:
    def __init__(self):
        self.max_jitter_ms = settings.ANTI_SLIPPAGE_MAX_JITTER_MS
        logger.info(f"🧠 [ANTI-SLIPPAGE] Inicializado. Jitter Máximo: {self.max_jitter_ms}ms")

    async def calculate_order_size(self, user_equity: float, mark_price: float, symbol: str) -> float:
        """
        Calcula o tamanho ideal de contratos/ordem com base no capital do usuário (equity)
        e alavancagem configurada, normalizando de acordo com a precisão decimal da OKX.
        """
        try:
            # 50x alavancagem recomendada pela especificação
            leverage = settings.LEVERAGE
            # Usando 10% do capital por slot (regra sniper)
            risk_per_slot = 0.10
            
            if settings.OKX_API_KEY_MASTER:
                user_equity = 100.0
                leverage = 50.0
                risk_per_slot = 0.10
                
            margin_usd = user_equity * risk_per_slot
            buying_power = margin_usd * leverage
            
            raw_qty = buying_power / mark_price
            
            # Obtém limites decimais do instrumento do cache/API da OKX
            inst_details = await okx_service.get_instrument_details(symbol)
            lot_size = float(inst_details.get("lotSize", "1.0"))
            
            # Arredonda a quantidade rigorosamente para múltiplos de lotSize
            normalized_qty = round(raw_qty / lot_size) * lot_size
            
            # Garante que respeita a quantidade mínima
            min_sz = float(inst_details.get("minSz", "1.0"))
            if normalized_qty < min_sz:
                normalized_qty = min_sz
                
            return round(normalized_qty, 4)
        except Exception as e:
            logger.error(f"❌ [ANTI-SLIPPAGE] Erro ao calcular tamanho da ordem: {e}")
            return 0.0

    def sharding_cohort_distribution(self, users: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Distribui e equilibra o conjunto de usuários ativos em 4 cohorts uniformes (A, B, C, D)
        baseando-se no saldo (equity) total consolidado de cada turma.
        """
        # Se não receber usuários, cria uma lista fictícia de 100 usuários com saldos variados para fins de testes
        if not users:
            logger.warning("⚠️ [ANTI-SLIPPAGE] Nenhuma lista de usuários fornecida. Gerando 100 contas mockadas para distribuição.")
            users = [
                {
                    "uid": f"usr_{i:03d}",
                    "username": f"user_{i}",
                    "equity": random.uniform(100.0, 5000.0),
                    "api_key": f"mock_key_{i}"
                }
                for i in range(1, 101)
            ]

        # Ordena os usuários por saldo (equity) decrescente
        sorted_users = sorted(users, key=lambda x: x.get("equity", 0.0), reverse=True)
        
        cohorts = {
            "Cohort_A": [],
            "Cohort_B": [],
            "Cohort_C": [],
            "Cohort_D": []
        }
        
        # Algoritmo de distribuição tipo cobra (Greedy snake sharding) para garantir que
        # os saldos totais fiquem extremamente balanceados entre os cohorts.
        cohort_names = ["Cohort_A", "Cohort_B", "Cohort_C", "Cohort_D"]
        for idx, user in enumerate(sorted_users):
            # Determina qual cohort recebe o usuário para balancear
            # Inverte a ordem de distribuição a cada rodada de 4 usuários (0,1,2,3, 3,2,1,0)
            round_idx = idx // 4
            position = idx % 4
            
            if round_idx % 2 == 0:
                selected_cohort = cohort_names[position]
            else:
                selected_cohort = cohort_names[3 - position]
                
            cohorts[selected_cohort].append(user)

        # Loga as estatísticas de balanceamento de cada cohort
        for name, members in cohorts.items():
            total_equity = sum(m.get("equity", 0.0) for m in members)
            logger.info(f"📊 [SHARDING] {name}: {len(members)} usuários | Saldo Consolidado: ${total_equity:.2f}")
            
        return cohorts

    async def execute_staggered_orders(self, symbol: str, side: str, entry_price: float, cohorts_data: Dict[str, List[Dict[str, Any]]]):
        """
        Executa a pulverização temporal adicionando um Random Jitter uniforme (0 a max_jitter_ms)
        para cada turma na fila de envio MQTT do Hermes Broker.
        """
        logger.info(f"🚀 [ANTI-SLIPPAGE] Iniciando pulverização de ordem temporal para {symbol} ({side})...")
        
        async def dispatch_cohort(cohort_name: str, members: List[Dict[str, Any]]):
            # Injeta atraso aleatório uniforme (Random_Uniform(0, max_jitter_ms)) para a turma
            jitter_seconds = random.uniform(0, self.max_jitter_ms) / 1000.0
            await asyncio.sleep(jitter_seconds)
            
            # Compila apenas os ids dos membros da turma para o payload do MQTT
            member_ids = [m.get("uid") for m in members]
            
            # Publica o sinal de sniper direcionado a esta turma no MQTT
            success = await hermes_broker_service.publish_sniper_signal(
                symbol=symbol,
                side=side,
                entry_price=entry_price,
                cohorts=[cohort_name]
            )
            
            if success:
                logger.info(
                    f"⚡ [ANTI-SLIPPAGE] Despacho realizado para {cohort_name} | "
                    f"Jitter aplicado: {jitter_seconds * 1000:.1f}ms | {len(member_ids)} usuários notificados."
                )
            else:
                logger.error(f"❌ [ANTI-SLIPPAGE] Falha ao despachar ordem para {cohort_name}.")

        # Dispara todas as turmas concorrentemente. Cada uma aplicará seu próprio jitter interno!
        tasks = []
        for cohort_name, members in cohorts_data.items():
            tasks.append(asyncio.create_task(dispatch_cohort(cohort_name, members)))
            
        await asyncio.gather(*tasks)
        logger.info("✨ [ANTI-SLIPPAGE] Ciclo de pulverização temporal finalizado com sucesso.")

# Instanciação Singleton
anti_slippage_engine = AntiSlippageEngine()
