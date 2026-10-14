import pytest
import sys
import os

sys.path.insert(0, os.path.abspath("backend"))

from fastapi.testclient import TestClient

def get_test_client():
    from main import app
    return TestClient(app)

def test_rag_status_and_search_endpoints():
    """Valida que endpoints /api/v1/hermes/rag/status e /search respondem com sucesso."""
    client = get_test_client()
    
    # 1. Status
    res = client.get("/api/v1/hermes/rag/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert "indexed_sources" in data
    assert data["total_chunks"] >= 0

    # 2. Search
    res_search = client.get("/api/v1/hermes/rag/search?q=arquitetura&top_k=2")
    assert res_search.status_code == 200
    sdata = res_search.json()
    assert "results" in sdata
    assert len(sdata["results"]) > 0

def test_ml_status_and_dataset_stats_endpoints():
    """Valida que endpoints /api/v1/ml/status e /dataset-stats respondem com sucesso."""
    client = get_test_client()
    
    # 1. Status (registrado via app.api.v1.endpoints.ml)
    res = client.get("/api/v1/ml/status")
    assert res.status_code == 200
    data = res.json()
    assert "conductor" in data
    assert "laya" in data
    assert "kronos" in data
    assert data["laya"]["is_calibrated"] is True
    assert data["kronos"]["is_calibrated"] is True

    # 2. Stats
    res_stats = client.get("/api/v1/ml/dataset-stats")
    assert res_stats.status_code == 200
    sdata = res_stats.json()
    assert "laya_decision_dataset.jsonl" in sdata

def test_mcp_endpoints_respond():
    """Valida que o mount nativo do MCP em /mcp/tools responde em JSON."""
    client = get_test_client()
    res = client.get("/mcp/tools")
    assert res.status_code == 200
    data = res.json()
    assert "tools" in data
    tool_names = [t["name"] for t in data["tools"]]
    assert "get_balance" in tool_names
    assert "get_positions" in tool_names
