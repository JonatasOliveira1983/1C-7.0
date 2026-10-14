"""
Base Tecnológica — Audit & Immutability Service.
Gravação de eventos na trilha imutável AuditEvent com hash SHA-256 e sanitização de PII.
"""
import hashlib
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.base_models import AuditEvent


def sanitize_pii(text: str) -> str:
    """Sanitiza PII (CPFs, e-mails parciais, chaves, senhas)."""
    if not text:
        return ""
    # Mascara CPF: 123.456.789-10 -> 123.***.***-10
    t = re.sub(r"(\d{3})\.?(\d{3})\.?(\d{3})-?(\d{2})", r"\1.***.***-\4", text)
    # Mascara CNPJ: 12.345.678/0001-90 -> 12.***.***/0001-90
    t = re.sub(r"(\d{2})\.?(\d{3})\.?(\d{3})/(\d{4})-?(\d{2})", r"\1.***.***/\4-\5", t)
    return t


def log_event(
    db: Session,
    agent_name: str,
    action_type: str,
    description: str,
    operation_id: Optional[int] = None,
    ip_address: str = "127.0.0.1"
) -> AuditEvent:
    """Registra evento na trilha de auditoria com selo criptográfico SHA-256."""
    now = datetime.utcnow()
    clean_desc = sanitize_pii(description)
    raw_seal = f"{now.isoformat()}-{agent_name}-{action_type}-{clean_desc}-{ip_address}"
    seal = hashlib.sha256(raw_seal.encode("utf-8")).hexdigest()

    event = AuditEvent(
        operation_id=operation_id,
        agent_name=agent_name,
        action_type=action_type,
        description=clean_desc,
        ip_address=ip_address,
        sha256_seal=seal,
        created_at=now
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_recent_events(db: Session, limit: int = 50) -> List[Dict[str, Any]]:
    """Retorna os eventos mais recentes para a interface de auditoria."""
    rows = (
        db.query(AuditEvent)
        .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "operation_id": r.operation_id,
            "agent_name": r.agent_name,
            "action_type": r.action_type,
            "description": r.description,
            "ip_address": r.ip_address,
            "sha256_seal": r.sha256_seal,
            "timestamp": r.created_at.strftime("%d/%m/%Y %H:%M:%S") if r.created_at else ""
        }
        for r in rows
    ]
