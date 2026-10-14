# DOCUMENTO DE REQUISITOS TECNICOS (TRD) - 1CRYPTEN MOBILE

> **Objetivo**: Fixar as escolhas de arquitetura, linguagens, comunicacao em tempo real, integracao de IA (Hermes, Laya, RAG, MCP) e persistencia para a aplicacao mobile de bolso sem ambiguidades.

---

## 1. Plataformas e Ambientes de Execucao
- **Plataformas-Alvo**: Mobile Web Browser (Safari iOS, Chrome Android) e PWA instalavel na tela inicial do celular com `display: standalone`.
- **Ambiente de Desenvolvimento**: Windows 11, Python 3.12, Uvicorn ASGI Server na porta 8085.
- **Ambiente de Producao**: Servidor local / VPS dedicado com acesso direto a API da OKX v5.

---

## 2. Frontend e Tecnologias Visuais
- **Stack de Interface**: HTML5 semântico, Tailwind CSS (utilitários de layout e cores Binance Dark), JavaScript Vanilla moderno (ES6+, zero dependencias pesadas de runtime para garantir inicializacao sub-segundo).
- **Biblioteca de Graficos**: TradingView Lightweight Charts (v4.1+) otimizada para mobile, renderizando **exatamente 1 canvas ativo por vez** (com destruicao e reconstrucao rapida ao trocar de slot para preservar memoria do celular).
- **Iconografia**: SVG inline vetorial nativo (proibicao estrita de caracteres emojis).
- **Touch & Haptic**: Areas de toque (*touch targets*) minimas de 44x44 pixels, suporte a gestos de deslizamento (*swipe*) entre abas e rolagem suave com amortecimento (*momentum scrolling*).
- **Rota Dedicada**: Servida pelo FastAPI em `/mobile` e estatico em `backend/app/static/mobile_app.html`.

---

## 3. Backend, Linguagem e Banco de Dados
- **Framework de Backend**: FastAPI (Python 3.12).
- **Servidor ASGI**: Uvicorn em processo unico assincrono na porta 8085.
- **Banco de Dados**: SQLite local em modo WAL (`backend/local_sniper.db` e `app_database.db`), com indices otimizados em `sandbox_trades`, `agent_conversation_memories` e `audit_events`.
- **Comunicacao em Tempo Real**: 
  - Canal WebSocket (`/ws/mobile` ou streaming de eventos SSE) para transmissao de ticks de precos da OKX e PnL dos slots a cada 1000ms.
  - Sincronizacao de historico de chat com Hermes via REST assincrono (`/api/v1/hermes/chat`, `/api/v1/hermes/history`).

---

## 4. Nucleo de Inteligencia Artificial (Hermes, Laya, RAG e MCP)
- **Orquestrador Central (Hermes 2.0)**:
  - Responde na rota `/api/v1/hermes/chat`.
  - Mantem memoria conversacional persistente no SQLite (`agent_conversation_memories`).
  - Aciona o motor hibrido de inferencia (DeepSeek Cloud via API de alta velocidade ou Qwen local em CPU/GGUF).
- **Roteador Tatico Laya (System 1)**:
  - `laya_router_service.py` executando localmente na CPU em sub-segundo para classificar perguntas taticas e telemetria de slots.
- **RAG Semântico Local (Nivel 1)**:
  - `rag_service.py` utilizando BM25 Okapi sobre documentos em `backend/data/knowledge/` (playbook de trading, politica de risco 15X, manual de operacao da OKX).
  - Injeta contexto relevante no prompt do Hermes sem custo de APIs externas de embeddings.
- **Protocolo de Ferramentas MCP (FastMCP)**:
  - Servidor MCP integrado em `backend/services/mcp_bridge.py` e endpoints `/api/v1/mcp`.
  - Ferramentas expostas ao Hermes:
    - `get_balance`: Saldo em USDT e margem disponivel.
    - `get_open_positions`: Dados dos 4 slots operacionais.
    - `close_position`: Execucao controlada de encerramento de trade.
    - `get_audit_log`: Registros forenses com hash SHA-256.

---

## 5. Integracoes Externas
| Provedor / API | Finalidade Tecnica | Protocolo | Tolerancia de Falha |
|---|---|---|---|
| **OKX API v5** | Cotações em tempo real de SWAP perpétuo, candles 15m/1h e execução de ordens | REST v5 + WebSocket | Cache em memória local caso ocorra timeout |
| **DeepSeek Cloud API** | Raciocínio conversacional de alta inteligência para o Hermes | REST (HTTPS) | Fallback gracioso para respostas operacionais locais estruturadas |

---

## 6. Seguranca, Integridade e Auditoria
- **Zero Alucinacao em Transacoes**: Hermes e a interface mobile nunca enviam ordens sem a validacao dos parametros de preco e alavancagem 15X.
- **Auditoria Forense SHA-256**: Cada acao executada via mobile ou comando conversacional gera um evento de auditoria assinado (`AuditEvent`).
- **Bloqueio de Emojis**: Todo payload de entrada e saida de texto passa pelo filtro `_strip_emojis` implementado no `hermes_service.py`.

---

## 7. Metas de Desempenho e SLA Mobile
- **Tempo de Primeiro Carregamento (FCP)**: < 1.200 ms em conexao movel 4G.
- **Tempo de Resposta do Hermes (Chat)**: < 1.000 ms para respostas taticas e saudacoes; < 2.500 ms com sintese LLM.
- **Alternancia entre Abas**: < 80 ms (troca instantanea no DOM sem recarregamento de pagina).
- **Troca de Slot no Grafico Solo**: < 300 ms para carregar candles e tracos de entrada/stop/alvo.
