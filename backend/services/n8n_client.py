import os
import httpx
import logging

logger = logging.getLogger("N8NMCPClient")

class N8NMCPClient:
    """
    Cliente MCP HTTP para conectar o backend Python ao servidor MCP do n8n.
    Permite que os Agentes em Python listem e executem fluxos do n8n dinamicamente.
    """
    def __init__(self):
        self.url = os.getenv("N8N_MCP_URL", "https://n8n-production-8e2d4.up.railway.app/mcp-server/http")
        self.token = os.getenv("N8N_MCP_TOKEN", "")

    def _get_headers(self):
        headers = {
            "Content-Type": "application/json"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def list_tools(self) -> dict:
        """Lista os fluxos (Tools) disponíveis no n8n."""
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(self.url, json=payload, headers=self._get_headers())
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.error(f"❌ Erro ao listar tools do n8n: {e}")
            raise

    async def call_tool(self, tool_name: str, arguments: dict = None) -> dict:
        """Aciona um fluxo específico no n8n."""
        if arguments is None:
            arguments = {}
            
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 2
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(self.url, json=payload, headers=self._get_headers())
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.error(f"❌ Erro ao chamar tool {tool_name} no n8n: {e}")
            raise

n8n_client = N8NMCPClient()
