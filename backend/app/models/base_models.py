"""
Base Tecnológica — Modelos Relacionais Centrais (SQLAlchemy).
Entidades corporativas para operações, auditoria, conformidade e envelopes de assinatura/telemetria.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class Operation(Base):
    """Registro mestre de uma operação, caso, transação ou processo do sistema."""
    __tablename__ = "operations"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    op_type = Column(String(50), default="geral", index=True)
    status = Column(String(50), default="intake", index=True)
    
    # Contraparte / Cliente
    client_name = Column(String(200), nullable=True)
    client_document = Column(String(50), nullable=True, index=True)  # CPF / CNPJ / ID
    client_email = Column(String(150), nullable=True)
    
    # Valores & Parâmetros
    total_value = Column(Float, default=0.0)
    currency = Column(String(10), default="BRL")
    metadata_json = Column(Text, default="{}")
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    documents = relationship("OperationDocument", back_populates="operation", cascade="all, delete-orphan")
    compliance_checks = relationship("ComplianceCheck", back_populates="operation", cascade="all, delete-orphan")
    envelopes = relationship("ContractEnvelope", back_populates="operation", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="operation", cascade="all, delete-orphan")


class OperationDocument(Base):
    """Documentos anexos a uma operação (laudos, identidades, contratos, procurações)."""
    __tablename__ = "operation_documents"

    id = Column(Integer, primary_key=True, index=True)
    operation_id = Column(Integer, ForeignKey("operations.id"), nullable=True)
    
    name = Column(String(255), nullable=False)
    doc_type = Column(String(50), default="outros")  # cnh, rg, passaporte, contrato, laudo
    file_path = Column(String(500), nullable=False)
    sha256_hash = Column(String(64), nullable=True, index=True)
    
    verified = Column(Boolean, default=False)
    extracted_data = Column(Text, nullable=True)  # JSON com dados do OCR
    created_at = Column(DateTime, default=datetime.utcnow)

    operation = relationship("Operation", back_populates="documents")


class ComplianceCheck(Base):
    """Auditoria de conformidade, KYC/AML, sanções e certidões."""
    __tablename__ = "compliance_checks"

    id = Column(Integer, primary_key=True, index=True)
    operation_id = Column(Integer, ForeignKey("operations.id"), nullable=True)
    
    agent_name = Column(String(50), nullable=False)  # Ex: Dra. Kim, Sam, Charlie
    check_type = Column(String(100), nullable=False)
    risk_score = Column(Integer, default=0)  # 0 (seguro) a 100 (crítico)
    status = Column(String(50), default="REGULAR")  # REGULAR, ALERTA, REJEITADO
    protocol_code = Column(String(100), nullable=True)
    summary = Column(Text, nullable=True)
    details_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)

    operation = relationship("Operation", back_populates="compliance_checks")


class ContractEnvelope(Base):
    """Ciclo de vida de assinaturas eletrônicas e telemetria forense de e-mail."""
    __tablename__ = "contract_envelopes"

    id = Column(Integer, primary_key=True, index=True)
    operation_id = Column(Integer, ForeignKey("operations.id"), nullable=True)
    token = Column(String(64), unique=True, index=True, nullable=False)
    
    title = Column(String(200), default="Documento Oficial")
    recipient_name = Column(String(150), nullable=True)
    recipient_email = Column(String(150), nullable=True)
    
    # Estágios: CRIADO -> ENVIADO -> ABERTO -> DOWNLOAD -> ASSINADO
    status = Column(String(30), default="CRIADO", index=True)
    
    # Telemetria
    open_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    first_opened_at = Column(DateTime, nullable=True)
    last_opened_at = Column(DateTime, nullable=True)
    last_ip = Column(String(50), nullable=True)
    user_agent = Column(String(300), nullable=True)
    detected_client = Column(String(100), nullable=True)  # Outlook, Apple Mail, Chrome, etc.
    
    # Assinatura
    signed_at = Column(DateTime, nullable=True)
    signature_hash = Column(String(64), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    operation = relationship("Operation", back_populates="envelopes")


class AuditEvent(Base):
    """Trilha imutável de auditoria corporativa com selo criptográfico."""
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    operation_id = Column(Integer, ForeignKey("operations.id"), nullable=True)
    
    agent_name = Column(String(50), nullable=False)
    action_type = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    ip_address = Column(String(50), default="127.0.0.1")
    sha256_seal = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    operation = relationship("Operation", back_populates="audit_events")


def ensure_schema(engine):
    """Cria tabelas se não existirem."""
    Base.metadata.create_all(bind=engine)
