import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv(os.path.join("..", ".env"))
TOKEN = os.getenv("N8N_MCP_TOKEN")
API_URL = "https://n8n-production-8e2d4.up.railway.app/api/v1/workflows/PI0VK4G2xXADAX0I"
PYTHON_APP = "https://10d50-production.up.railway.app"

with open("workflow.json", "r") as f:
    wf = json.load(f)

# Update nodes
for node in wf["nodes"]:
    if node["name"] == "Oracle & Macro Analyst (Python)":
        node["type"] = "n8n-nodes-base.httpRequest"
        node["typeVersion"] = 4.1
        node["parameters"] = {
            "url": f"{PYTHON_APP}/api/system/state",
            "method": "GET"
        }
    elif node["name"] == "Fleet Audit (Python)":
        node["type"] = "n8n-nodes-base.httpRequest"
        node["typeVersion"] = 4.1
        node["parameters"] = {
            "url": f"{PYTHON_APP}/api/slots",
            "method": "GET"
        }
    elif node["name"] == "Sieve Agent (Python)":
        node["type"] = "n8n-nodes-base.httpRequest"
        node["typeVersion"] = 4.1
        node["parameters"] = {
            "url": f"{PYTHON_APP}/api/radar/pulse",
            "method": "GET"
        }
    elif node["name"] == "Captain Agent (Python Executa)":
        node["type"] = "n8n-nodes-base.httpRequest"
        node["typeVersion"] = 4.1
        node["parameters"] = {
            "url": f"{PYTHON_APP}/api/captain/tocaias",
            "method": "GET"
        }
    elif node["name"] == "Agente Visão (n8n Nativo)":
        # Transformando o Agente em um Switch temporário ou NoOp para evitar erro de credencial no teste
        node["type"] = "n8n-nodes-base.noOp"
        node["typeVersion"] = 1
        node["parameters"] = {}
        node["notes"] = "Agente LangChain desativado no script para teste (Requer OpenAI Key na nuvem)"
    elif node["name"] == "Avalia Slots Livres":
        node["parameters"] = {
            "conditions": {
                "boolean": [
                    {
                        "value1": "={{ Object.keys($json).length < 4 }}",
                        "value2": True
                    }
                ]
            }
        }

payload = {
    "nodes": wf.get("nodes", []),
    "connections": wf.get("connections", {}),
    "name": wf.get("name", "Macro-Orquestrador Híbrido 10D5.0"),
    "settings": {}
}

req = urllib.request.Request(API_URL, method="PUT", headers={
    "X-N8N-API-KEY": TOKEN,
    "Content-Type": "application/json"
}, data=json.dumps(payload).encode("utf-8"))

try:
    resp = urllib.request.urlopen(req)
    print("Update Response:", resp.status)
    
    # Executar o fluxo
    run_url = "https://n8n-production-8e2d4.up.railway.app/api/v1/workflows/PI0VK4G2xXADAX0I/run"
    run_req = urllib.request.Request(run_url, method="POST", headers={
        "X-N8N-API-KEY": TOKEN,
        "Content-Type": "application/json"
    }, data=b'{}')
    run_resp = urllib.request.urlopen(run_req)
    result = json.loads(run_resp.read().decode("utf-8"))
    print("Run result:", json.dumps(result, indent=2))
except Exception as e:
    print("Error:", e)
    if hasattr(e, 'read'):
        print(e.read().decode())
