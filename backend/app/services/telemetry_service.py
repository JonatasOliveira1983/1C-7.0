"""
Base Tecnológica — Telemetria Forense de E-mails & Ciclo de Assinaturas Digitais.
- Pixel Transparente 1x1 anti-cache
- Detecção de Ambiente & E-mail Client (Outlook, Apple Mail, Chrome Webmail, Thunderbird)
- Download monitorado e rastreamento de aberturas
- Chancela Digital Criptográfica SHA-256 em 5 estágios
"""
import hashlib
import secrets
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.models.base_models import ContractEnvelope, AuditEvent

# Bytes oficiais de uma imagem PNG 1x1 transparente (43 bytes)
PIXEL_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06"
    b"\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r"
    b"\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def detect_email_client(user_agent: str) -> str:
    """Classifica o cliente de e-mail ou navegador a partir do User-Agent."""
    ua = (user_agent or "").lower()
    if not ua:
        return "Desconhecido / Proxy"
    if "thunderbird" in ua:
        return "Mozilla Thunderbird"
    if "microsoft outlook" in ua or "outlook" in ua or "office" in ua:
        return "Microsoft Outlook"
    if "applewebkit" in ua and ("iphone" in ua or "ipad" in ua or "cfnetwork" in ua):
        return "Apple Mail (iOS)"
    if "macintosh" in ua and "safari" in ua and "chrome" not in ua:
        return "Apple Mail (macOS)"
    if "googleimageproxy" in ua:
        return "Google Gmail (Image Proxy)"
    if "chrome" in ua:
        return "Google Chrome / Webmail"
    if "firefox" in ua:
        return "Mozilla Firefox"
    if "safari" in ua:
        return "Apple Safari"
    return "Navegador Web / Outro"


def create_envelope(
    db: Session,
    title: str,
    recipient_name: Optional[str] = None,
    recipient_email: Optional[str] = None,
    operation_id: Optional[int] = None
) -> ContractEnvelope:
    """Gera um novo envelope com token seguro criptográfico."""
    token = secrets.token_hex(20)
    env = ContractEnvelope(
        token=token,
        title=title,
        recipient_name=recipient_name,
        recipient_email=recipient_email,
        operation_id=operation_id,
        status="CRIADO"
    )
    db.add(env)
    
    # Registra evento na trilha de auditoria
    audit = AuditEvent(
        operation_id=operation_id,
        agent_name="Grace",
        action_type="ENVELOPE_CREATED",
        description=f"Envelope '{title}' criado para {recipient_name or 'Contraparte'} ({token[:8]}...)",
        sha256_seal=hashlib.sha256(f"{token}-created".encode()).hexdigest()
    )
    db.add(audit)
    db.commit()
    db.refresh(env)
    return env


def track_pixel_open(db: Session, token: str, ip: str, user_agent: str) -> Optional[ContractEnvelope]:
    """Registra evento de leitura do e-mail via pixel 1x1."""
    env = db.query(ContractEnvelope).filter(ContractEnvelope.token == token).first()
    if not env:
        return None
    
    now = datetime.utcnow()
    env.open_count += 1
    if not env.first_opened_at:
        env.first_opened_at = now
    env.last_opened_at = now
    env.last_ip = ip
    env.user_agent = user_agent
    env.detected_client = detect_email_client(user_agent)
    
    if env.status in ("CRIADO", "ENVIADO"):
        env.status = "ABERTO"
        
    audit = AuditEvent(
        operation_id=env.operation_id,
        agent_name="Sam",
        action_type="EMAIL_OPENED",
        description=f"E-mail aberto por {env.recipient_name or 'Destinatário'} via {env.detected_client} (IP {ip})",
        ip_address=ip,
        sha256_seal=hashlib.sha256(f"{token}-{now.isoformat()}-open".encode()).hexdigest()
    )
    db.add(audit)
    db.commit()
    db.refresh(env)
    return env


def track_document_download(db: Session, token: str, ip: str) -> Optional[ContractEnvelope]:
    """Registra evento de download da minuta/documento."""
    env = db.query(ContractEnvelope).filter(ContractEnvelope.token == token).first()
    if not env:
        return None
    
    now = datetime.utcnow()
    env.download_count += 1
    if env.status != "ASSINADO":
        env.status = "DOWNLOAD"
        
    audit = AuditEvent(
        operation_id=env.operation_id,
        agent_name="Charlie",
        action_type="DOCUMENT_DOWNLOADED",
        description=f"Documento baixado para análise (IP {ip}, contagem {env.download_count})",
        ip_address=ip,
        sha256_seal=hashlib.sha256(f"{token}-{now.isoformat()}-download".encode()).hexdigest()
    )
    db.add(audit)
    db.commit()
    db.refresh(env)
    return env


def sign_envelope(db: Session, token: str, ip: str) -> Optional[ContractEnvelope]:
    """Aplica a chancela de assinatura digital definitiva ao envelope."""
    env = db.query(ContractEnvelope).filter(ContractEnvelope.token == token).first()
    if not env:
        return None
    
    now = datetime.utcnow()
    seal = hashlib.sha256(f"{token}-{now.isoformat()}-{env.recipient_email}-SIGN".encode()).hexdigest()
    env.signed_at = now
    env.signature_hash = seal
    env.status = "ASSINADO"
    
    audit = AuditEvent(
        operation_id=env.operation_id,
        agent_name="Grace",
        action_type="CONTRACT_SIGNED",
        description=f"Envelope '{env.title}' assinado com sucesso. Hash: {seal[:16]}...",
        ip_address=ip,
        sha256_seal=seal
    )
    db.add(audit)
    db.commit()
    db.refresh(env)
    return env
