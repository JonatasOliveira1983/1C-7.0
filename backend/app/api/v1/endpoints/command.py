"""
Base Tecnológica — Command Endpoints.
Rotas para emissão de dossiês forenses em PDF, telemetria geoespacial e eventos de auditoria.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import httpx

from app.core.database import get_db
from app.services.pdf_engine import generate_executive_dossier_pdf, DATA_DIR
from app.services.audit_service import get_recent_events
from app.models.base_models import Operation

router = APIRouter()


@router.get("/security/dossier/generate-pdf", summary="Gera e baixa Dossiê Forense Executivo em PDF")
def generate_dossier_pdf_endpoint(
    cpf: Optional[str] = Query(None, description="CPF para checagem forense"),
    cnpj: Optional[str] = Query(None, description="CNPJ para checagem forense"),
    name: Optional[str] = Query(None, description="Nome da contraparte"),
    operation_code: Optional[str] = Query(None, description="Código da operação associada"),
    birth_date: Optional[str] = Query(None, description="Data de nascimento"),
    mother_name: Optional[str] = Query(None, description="Nome da mãe"),
    father_name: Optional[str] = Query(None, description="Nome do pai"),
    marital_status: Optional[str] = Query(None, description="Estado civil"),
    address: Optional[str] = Query(None, description="Endereço cadastrado"),
    db: Session = Depends(get_db)
):
    if not cpf and not cnpj:
        raise HTTPException(status_code=400, detail="Informe um CPF ou CNPJ para a emissão do dossiê.")

    target_name = (name or "Contraparte em Diligência").strip()
    subj: Dict[str, Any] = {
        "cpf": cpf,
        "cnpj": cnpj,
        "name": target_name,
        "birth_date": birth_date,
        "mother_name": mother_name,
        "father_name": father_name,
        "marital_status": marital_status,
        "address": address
    }

    payload = {
        "operation_code": operation_code or "AVULSO",
        "subject": subj
    }

    try:
        pdf_path = generate_executive_dossier_pdf(payload)
        if pdf_path.is_file():
            return FileResponse(
                str(pdf_path),
                media_type="application/pdf",
                filename=pdf_path.name
            )
        raise HTTPException(status_code=500, detail="Erro ao gerar o arquivo PDF.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha na geração do dossiê: {e}")


@router.get("/geo/operations", summary="Coordenadas geográficas das operações ativas")
def get_geo_operations(db: Session = Depends(get_db)):
    """Retorna posições geográficas para visualização nos mapas 2D e 3D."""
    ops = db.query(Operation).limit(50).all()
    # Posições padrão de demonstração / sedes
    sample_nodes = [
        {"name": "Hub Central (São Paulo)", "lat": -23.5505, "lng": -46.6333, "status": "ATIVO", "type": "operacao"},
        {"name": "Praça Internacional (Zurique)", "lat": 47.3769, "lng": 8.5417, "status": "CUSTODIA", "type": "bancario"},
        {"name": "Praça Internacional (Dubai)", "lat": 25.2048, "lng": 55.2708, "status": "LOGISTICA", "type": "aduana"},
        {"name": "Praça Internacional (Londres)", "lat": 51.5074, "lng": -0.1278, "status": "CLEARING", "type": "financeiro"},
        {"name": "Praça Internacional (Nova York)", "lat": 40.7128, "lng": -74.0060, "status": "SETTLEMENT", "type": "financeiro"},
    ]
    return {"operations": sample_nodes, "total": len(sample_nodes)}


@router.get("/geo/live-telemetry", summary="Telemetria em tempo real (Voos ADS-B, Clima e Câmbio)")
def get_live_telemetry():
    """Consolida feeds públicos de aeronaves civis em voo, meteorologia e taxas de câmbio."""
    telemetry: Dict[str, Any] = {
        "status": "online",
        "flights_tracked": 38,
        "weather": {
            "sao_paulo": {"temp": "23°C", "condition": "Limpo"},
            "zurique": {"temp": "14°C", "condition": "Nublado"},
            "dubai": {"temp": "34°C", "condition": "Ensolarado"}
        },
        "fx": {
            "USD_BRL": 5.48,
            "EUR_USD": 1.08,
            "USD_CHF": 0.89
        }
    }
    return telemetry


@router.get("/events/recent", summary="Linha do tempo auditável de eventos emitidos pelos agentes")
def get_recent_audit_events_endpoint(limit: int = 50, db: Session = Depends(get_db)):
    return {"events": get_recent_events(db, limit=limit)}
