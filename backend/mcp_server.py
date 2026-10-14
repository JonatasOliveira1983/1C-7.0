# -*- coding: utf-8 -*-
"""
Crypten 1C-7.0 MCP Server Runner
Runs the MCP server standalone (via SSE / Streamable HTTP) for external agent connections (n8n, Cursor, Claude Desktop).
"""
import os
import uvicorn
from services.mcp_bridge import get_asgi_app

app = get_asgi_app()

if __name__ == "__main__":
    port = int(os.environ.get("MCP_PORT", 8086))
    print(f"❖ [1CRYPTEN] Iniciando Servidor MCP Oficial na porta {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
