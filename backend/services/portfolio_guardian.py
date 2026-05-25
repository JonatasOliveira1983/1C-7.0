# -*- coding: utf-8 -*-
import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from config import settings
from services.okx_service import okx_service
from services.okx_ws import okx_ws_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PortfolioGuardian")

class PortfolioGuardian:
    def __init__(self):
        # Configurações carregadas do settings (.env)
        self.activation_trigger = settings.GUARDIAN_ACTIVATION_TRIGGER
        self.trailing_margin = settings.GUARDIAN_TRAILING_MARGIN
        
        # Estados da Máquina de Estados:
        # "OBSERVANDO": Monitorando PnL e margem aguardando o trigger de ativação.
        # "RASTREAMENTO_ATIVO": Trailing Stop ativado, rastreando pico máximo de ROI.
        # "EXECUTAR_CORTE": Disparado Knife-Drop emergencial.
        self.state = "OBSERVANDO"
        
        self.max_roi_registered = 0.0
        self.current_roi = 0.0
        self.last_pnl_sum = 0.0
        self.last_margin_sum = 0.0
        self.last_update_time = time.time()
        
        # Lock de concorrência para evitar chamadas duplas ao Knife-Drop
        self._lock = asyncio.Lock()
        
        logger.info(f"🛡️ [GUARDIAN] Inicializado. Gatilho de Ativação: {self.activation_trigger}% | Margem de Recuo: {self.trailing_margin}%")

    def start(self):
        """Registra o callback no WebSocket da OKX para receber atualizações automáticas."""
        okx_ws_service.register_callback(self.evaluate_master_state)
        logger.info("🛡️ [GUARDIAN] Escuta ativada no WebSocket privado da OKX Master.")

    def get_status(self) -> Dict[str, Any]:
        """Retorna o status atual do Guardian para diagnóstico ou APIs externas."""
        return {
            "estado": self.state,
            "roi_atual": round(self.current_roi, 2),
            "pico_roi_registrado": round(self.max_roi_registered, 2),
            "ultimo_pnl": round(self.last_pnl_sum, 2),
            "ultima_margem": round(self.last_margin_sum, 2),
            "gatilho_ativacao": self.activation_trigger,
            "margem_recuo": self.trailing_margin,
            "timestamp": self.last_update_time
        }

    def evaluate_master_state(self, positions: List[Dict[str, Any]]):
        """
        Callback que recebe as posições ativas do WebSocket privado da OKX e
        executa a avaliação atômica da máquina de estados do Trailing-Stop.
        """
        # Como o callback é síncrono no loop do WS, criamos uma tarefa assíncrona para rodar a avaliação.
        asyncio.create_task(self._process_evaluation(positions))

    async def _process_evaluation(self, positions: List[Dict[str, Any]]):
        async with self._lock:
            # [ANTI-FACÃO] Consulta Moonbags/Emancipados para blinda-los do corte
            from services.firebase_service import firebase_service
            try:
                moonbags = await firebase_service.get_moonbags(limit=200)
                emancipated_symbols = set()
                if moonbags:
                    for m in moonbags:
                        sym = m.get("symbol")
                        if sym:
                            emancipated_symbols.add(sym.upper().replace(".P", ""))
            except Exception as e:
                logger.error(f"🛡️ [GUARDIAN] Erro ao buscar Moonbags: {e}")
                emancipated_symbols = set()

            # Filtra posições, removendo as protegidas
            tactical_positions = []
            for pos in positions:
                inst_id = pos.get("instId", "").upper().replace(".P", "")
                # Se for Bybit, usa symbol
                if not inst_id:
                    inst_id = pos.get("symbol", "").upper().replace(".P", "")
                    
                if inst_id in emancipated_symbols:
                    # Não logar warning para não floodar o terminal, apenas ignorar
                    continue
                tactical_positions.append(pos)
                
            positions = tactical_positions

            if not positions:
                # Sem posições abertas, resetamos o estado para OBSERVANDO se necessário
                if self.state != "OBSERVANDO":
                    logger.info("🛡️ [GUARDIAN] Nenhuma posição aberta detectada na Conta Master. Retornando ao estado OBSERVANDO.")
                    self.state = "OBSERVANDO"
                    self.max_roi_registered = 0.0
                self.current_roi = 0.0
                self.last_pnl_sum = 0.0
                self.last_margin_sum = 0.0
                self.last_update_time = time.time()
                return

            pnl_sum = 0.0
            margin_sum = 0.0
            
            for pos in positions:
                try:
                    # upl = unrealized profit and loss
                    upl = float(pos.get("upl", 0.0))
                    # margin ou mgnVal = margem alocada
                    margin = float(pos.get("margin", pos.get("mgnVal", 0.0)))
                    
                    pnl_sum += upl
                    margin_sum += margin
                except Exception as e:
                    logger.error(f"🛡️ [GUARDIAN] Erro ao parsear valores da posição: {pos}. Erro: {e}")

            self.last_pnl_sum = pnl_sum
            self.last_margin_sum = margin_sum
            self.last_update_time = time.time()

            # Calcula o ROI unificado (%)
            if margin_sum > 0:
                self.current_roi = (pnl_sum / margin_sum) * 100.0
            else:
                self.current_roi = 0.0

            logger.info(f"📊 [GUARDIAN] ROI Master: {self.current_roi:.2f}% | PnL Total: ${pnl_sum:.2f} | Margem Total: ${margin_sum:.2f} | Estado: {self.state}")

            # MÁQUINA DE ESTADOS DO GUARDIAN
            if self.state == "OBSERVANDO":
                if self.current_roi >= self.activation_trigger:
                    self.state = "RASTREAMENTO_ATIVO"
                    self.max_roi_registered = self.current_roi
                    logger.warning(
                        f"🚀🚀🚀 [GUARDIAN] Trailing-Stop ATIVADO! ROI Master ({self.current_roi:.2f}%) "
                        f"atingiu o limite mínimo de ativação de {self.activation_trigger}%."
                    )
            
            elif self.state == "RASTREAMENTO_ATIVO":
                # Atualiza a máxima histórica registrada
                if self.current_roi > self.max_roi_registered:
                    self.max_roi_registered = self.current_roi
                    logger.info(f"📈 [GUARDIAN] Novo pico de ROI registrado: {self.max_roi_registered:.2f}%")

                # Verifica se houve recuo abaixo da margem tolerada
                threshold_corte = self.max_roi_registered - self.trailing_margin
                logger.info(f"🔍 [GUARDIAN] Análise: ROI Atual {self.current_roi:.2f}% | Gatilho de Corte {threshold_corte:.2f}% (Pico: {self.max_roi_registered:.2f}%)")
                
                if self.current_roi < threshold_corte:
                    self.state = "EXECUTAR_CORTE"
                    logger.critical(
                        f"💥💥💥 [GUARDIAN - KNIFE-DROP] GATILHO DISPARADO! "
                        f"ROI Master ({self.current_roi:.2f}%) recuou abaixo do limite tolerado ({threshold_corte:.2f}%)."
                    )
                    await self._execute_knife_drop(positions)

            elif self.state == "EXECUTAR_CORTE":
                # Proteção contra repetição se posições ainda existirem
                logger.warning("🛡️ [GUARDIAN] Já em estado de EXECUTAR_CORTE. Aguardando finalização das ordens.")

    async def _execute_knife_drop(self, positions: List[Dict[str, Any]]):
        """Executa o fechamento emergencial em lote da OKX e emite alerta de pânico."""
        try:
            # 1. Dispara fechamento em lote na corretora
            logger.critical("🔪 [GUARDIAN] Enviando ordem de fechamento imediato em Lote na OKX (Knife-Drop)...")
            res = await okx_service.batch_close_positions(positions)
            logger.info(f"🛡️ [GUARDIAN] Resposta do Knife-Drop: {res}")
            
            # 2. Publica o sinal de pânico no broker MQTT do Hermes
            try:
                from services.hermes_broker import hermes_broker_service
                # Publica sinal de PANIC para fechar posições de todos os cohorts/usuários instantaneamente
                await hermes_broker_service.publish_panic_signal(positions)
            except Exception as mqtt_err:
                logger.error(f"❌ [GUARDIAN] Falha ao publicar sinal de pânico no Hermes MQTT: {mqtt_err}")

            # Transiciona de volta para OBSERVANDO após limpar o portfólio
            self.state = "OBSERVANDO"
            self.max_roi_registered = 0.0
            logger.info("🛡️ [GUARDIAN] Execução de corte encerrada. Retornando ao estado de OBSERVANDO.")

        except Exception as e:
            logger.error(f"❌ [GUARDIAN] Erro crítico na execução do Knife-Drop: {e}", exc_info=True)
            self.state = "RASTREAMENTO_ATIVO"  # Tenta novamente na próxima atualização

# Instanciação Singleton
portfolio_guardian = PortfolioGuardian()
