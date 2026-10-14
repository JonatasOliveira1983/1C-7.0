"""
BASE Tecnologica — Modulo de Dados: Memoria Agentica, Contexto Conversacional & Trilha de Auditoria.
Cada sistema renomeia o orquestrador (Hermes no X-Eng) e ajusta os exemplos abaixo ao seu dominio.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Text, Integer
from app.core.database import Base

class AgentConversationMemory(Base):
    """Armazena o historico e contexto persistente da conversa com o orquestrador e os agentes."""
    __tablename__ = "agent_conversation_memories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, index=True, default="default_session")
    sender = Column(String, nullable=False) # "User" ou o nome do orquestrador/agente
    message_text = Column(Text, nullable=False)
    target_agent = Column(String, default="Hermes")
    detected_intent = Column(String, nullable=True) # ex: "PEDIDO_ORCAMENTO", "AVANCAR_ETAPA"
    extracted_entities_json = Column(Text, nullable=True) # Metadados extraídos em JSON
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentActionLog(Base):
    """Trilha de auditoria das ações automáticas disparadas pelos agentes com suporte a reversão."""
    __tablename__ = "agent_action_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, index=True, default="default_session")
    agent_id = Column(String, nullable=False) # "valmir", "geraldo", "carla", "danilo"
    agent_name = Column(String, nullable=False) # "Valmir (Suprimentos)"
    action_type = Column(String, nullable=False) # "CREATE_PURCHASE_ORDER", "MOVE_STAGE", "RECORD_RDO"
    target_entity = Column(String, nullable=False) # "operational_works", "procurement_purchase_orders"
    target_id = Column(String, nullable=True)
    summary_description = Column(Text, nullable=False)
    snapshot_data_json = Column(Text, nullable=True) # Dados anteriores/criados para desfazer
    is_undone = Column(Integer, default=0) # 1 se o usuário clicou em Desfazer
    executed_at = Column(DateTime, default=datetime.utcnow)
