# 1CRYPTEN 7.0 — DOCUMENTAÇÃO TÉCNICA: MCP 2.x, RAG SEMÂNTICO & FINE-TUNING PIPELINE

> **Status**: Em Produção & Operacional  
> **Versão**: 7.0.0 (V148+)  
> **Data de Atualização**: 12/10/2026  
> **Fontes Canônicas**: `MASTER_ARCHITECTURE.md`, `backend/services/mcp_bridge.py`, `backend/services/rag_service.py`, `backend/app/ml/fine_tuning/`

---

## 📑 Sumário Executivo

O ecossistema de inteligência artificial do **1Crypten** combina três pilares tecnológicos de ponta para tomada de decisão institucional, auditoria autônoma e aprendizado contínuo:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           1CRYPTEN AI CORE ECOSYSTEM                            │
├─────────────────────┬───────────────────────────┬───────────────────────────────┤
│    MCP 2.x Bridge   │       RAG Semântico       │     Fine-Tuning & Datasets    │
│  (Model Context)    │      (Second Brain)       │    (Calibração Empírica)      │
├─────────────────────┼───────────────────────────┼───────────────────────────────┤
│ • Protocolo Aberto  │ • BM25 / TF-IDF Vector    │ • Dataset JSONL Supervisionado│
│ • Starlette SSE     │ • MASTER_ARCHITECTURE.md  │ • Bayesian Temperature Scale  │
│ • Standalone Stdio  │ • Obsidian Vault Galaxy   │ • Kronos Adapter (Incerteza)  │
│ • Claude/Cursor/n8n │ • Injeção Prompt Hermes   │ • Laya Smart Money H1 Feed    │
└─────────────────────┴───────────────────────────┴───────────────────────────────┘
```

---

## 1. 🔌 Model Context Protocol (MCP 2.x) Bridge

O **Model Context Protocol (MCP)** é o padrão aberto da Anthropic para interoperabilidade segura entre modelos de linguagem e ferramentas de sistemas em produção. No 1Crypten, o MCP é implementado em duas camadas complementares:

### 1.1. Arquitetura de Montagem

1. **Mount Nativo FastAPI ASGI** (`backend/services/mcp_bridge.py`):
   - Montado diretamente na raiz `/mcp` do backend (`backend/main.py`).
   - Servidor SSE (Server-Sent Events) compatível com MCP 2.x (`mcp.server.mcpserver.MCPServer`) e fallback automático para FastMCP 1.x (`mcp.server.fastmcp.FastMCP`).
   - Endpoints expostos:
     - `GET /mcp/sse`: Canal de streaming de eventos para clientes conectados.
     - `POST /mcp/messages`: Receptor de comandos JSON-RPC 2.0.
     - `GET /mcp/tools`: Endpoint REST de auditoria rápida da lista de ferramentas.

2. **Servidor Standalone Stdio** (`backend/mcp_server.py`):
   - Permite conexão direta por pipes stdio para IDEs e agentes locais:
     - **Claude Desktop App** (`claude_desktop_config.json`).
     - **Cursor IDE** (`Settings > Features > MCP Servers`).
     - **Hermes / n8n / Agentes Autônomos**.

### 1.2. Catálogo Oficial de Ferramentas Expostas (5 Tools)

| Ferramenta | Descrição | Parâmetros | Retorno Principal |
| :--- | :--- | :--- | :--- |
| `get_balance` | Consulta banca consolidada, equity unificado e modo de execução. | Nenhum | `unified_balance_usd`, `execution_mode`, `simulated_base_usd` |
| `get_positions` | Lista todas as posições ativas em tempo real (Scalp e Swing). | Nenhum | Lista de posições com `entry_price`, `current_stop`, `target`, `pnl_percent` |
| `get_radar_signals` | Captura pulso de fluxo institucional (Whale vs Retail) da Laya. | Nenhum | Top tickers com LSR, Open Interest, Bias direcional e convicção |
| `evaluate_asset` | Avalia confluência de entrada combinando Laya Flow e Kronos AI. | `symbol` (str), `side` (str, default "BUY") | Status de confluência, score Kronos, regime de fluxo e validação institucional |
| `get_system_snapshot` | Retorna telemetria macro do sistema e governança de risco. | Nenhum | `regime_mode`, `master_adx`, `unified_balance_usd`, `doctrine` |

### 1.3. Como Conectar o MCP aos Clientes

#### Configuração para Claude Desktop (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "1crypten": {
      "command": "python",
      "args": [
        "c:\\Users\\jonat\\Desktop\\Sistemas 2026\\2 - 1C-SET26\\backend\\mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "c:\\Users\\jonat\\Desktop\\Sistemas 2026\\2 - 1C-SET26\\backend"
      }
    }
  }
}
```

#### Conexão via SSE para n8n ou Agentes Remotos:
```http
GET http://localhost:8085/mcp/sse HTTP/1.1
Accept: text/event-stream
```

---

## 2. 🧠 RAG Semântico Unificado (Second Brain & Architecture)

O **RAG Semântico** (`backend/services/rag_service.py` e rota `backend/routes/rag_routes.py`) funciona como a memória viva e a fonte de verdade operacional do sistema, garantindo recuperação sub-milissegundo de diretrizes e regras sem latência de bancos vetoriais pesados.

### 2.1. Fontes de Conhecimento Indexadas

O motor realiza varredura recursiva e particionamento inteligente em seções canônicas de:
1. **`MASTER_ARCHITECTURE.md`**: Diretrizes inegociáveis, contratos, portas, limites de risco e histórico de versões.
2. **`vault_galaxy/`**: Cofre Obsidian institucional contendo diários de trades (`journal/`), estratégias operacionais (`strategies/`) e notas de auditoria (`trades/`).
3. **`AGENTS.md` & `.agents/rules/`**: Metodologia Superpowers, invariantes de stop, anti-hedge e protocolos operacionais.
4. **`docs/`**: Blueprints, auditorias de rentabilidade e especificações de turnaround.

### 2.2. Algoritmo & Métricas de Desempenho

- **Mecanismo**: Algoritmo BM25 / TF-IDF vetorial em memória com normalização de termos e pesos por categoria (`ARCHITECTURE`, `GALAXY_STRATEGIES`, `RULES`, `DOCS`).
- **Tempo de Indexação Completa**: ~60 milissegundos para mais de 120 chunks estruturados.
- **Latência de Recuperação**: < 1.5 ms por consulta.
- **Injeção em Tempo Real**: Conectado diretamente ao prompt do operador no `HermesAgent` (`backend/services/hermes_agent.py`) e na rota de chat `/chat`, enriquecendo as respostas com as invariantes exatas do sistema.

### 2.3. Endpoints REST da API do RAG

- **`GET /api/v1/hermes/rag/search?q={query}&limit=5`**:  
  Executa busca semântica e retorna os chunks mais relevantes com score de similaridade, título e fonte.
- **`POST /api/v1/hermes/rag/reindex`**:  
  Força a reindexação a quente de todos os arquivos de documentação sem reiniciar o servidor FastAPI.
- **`GET /api/v1/hermes/rag/status`**:  
  Retorna telemetria da base de conhecimento (total de documentos, data da última indexação e status de prontidão).

---

## 3. 🎯 Pipeline de Datasets & Fine-Tuning de IA

O pipeline de Machine Learning supervisionado (`backend/app/ml/fine_tuning/`) foi projetado para calibrar a sensibilidade dos modelos decisórios de acordo com os resultados empíricos das operações reais e simuladas.

### 3.1. Componentes do Pipeline

#### A. DatasetGenerator (`dataset_generator.py`)
- Extrai o histórico auditado de trades do Sandbox/OKX e logs de fluxo Rubik.
- Gera datasets supervisionados em formato JSONL padronizado:
  - **`laya_decision_dataset.jsonl`**: Tuplas contendo variáveis de entrada (LSR, Open Interest, ADX, regime de volatilidade, bias) e a decisão ótima com o resultado em PnL (`target_decision`: `BUY`, `SELL`, `HOLD`).
  - **`kronos_series_dataset.jsonl`**: Sequências temporais de K-lines (janela de 24 velas de entrada para predição das 12 velas subsequentes) para calibração de projeção de preço.

#### B. LayaFineTuneTrainer (`laya_finetune_trainer.py`)
- **Calibração Empírica Bayesiana & Temperature Scaling**:
  - Ajusta a distribuição de probabilidades de entrada com base nas taxas de acerto históricas por regime de mercado.
  - Se GPU com PyTorch/PEFT estiver disponível, executa adaptação via LoRA sobre embeddings; caso contrário, executa calibração Bayesiana determinística ultra-rápida.
  - Produz o artefato **`laya_calibrated_weights.json`**:
    - Fatores de escala por regime (`confidence_multiplier`).
    - Temperatura de decisão ($T = 0.85$ para decisões mais incisivas e menor entropia).
    - Thresholds mínimos de convicção ajustados dinamicamente.

#### C. KronosAdapterTrainer (`kronos_adapter_trainer.py`)
- Calibra a dispersão e incerteza das trajetórias geradas pelo transformer Kronos.
- Alinha as projeções estatísticas às K-lines da OKX SWAP gerando o artefato `kronos_adapter.json`.

### 3.2. Integração com o Motor Smart Money H1 (Novo Paradigma)

Com a migração do sistema para o padrão **1H (LAYA_SMART_MONEY_H1)**:
- Os datasets de fine-tuning agora incorporam:
  1. **Amplitude do Range de Acumulação em 1H** (`range_high`, `range_low`, `range_pct`).
  2. **Divergência LSR x Open Interest no rompimento** (confirmação institucional).
  3. **Stop Loss Técnico Blindado** (alocado no limite oposto de saída da consolidação).
- O `LayaRouterService` lê `laya_calibrated_weights.json` na inicialização e modula a nota final de entrada da Laya para só autorizar disparos de alta convicção institucional.

### 3.3. Endpoints REST da API de Machine Learning

- **`POST /api/v1/ml/generate-dataset`**: Dispara a geração dos datasets JSONL a partir do banco de dados SQLite.
- **`GET /api/v1/ml/dataset-stats`**: Retorna contagem de amostras, distribuição de classes e tamanho em disco.
- **`POST /api/v1/ml/train-laya`**: Inicia o treinamento/calibração da Laya e atualiza `laya_calibrated_weights.json`.
- **`POST /api/v1/ml/train-kronos`**: Inicia o treinamento/calibração do adaptador Kronos.
- **`GET /api/v1/ml/status`**: Relatório de status dos modelos calibrados e histórico do último treinamento.

### 3.4. Catálogo Universal de Mercado OKX & Geometria Inviolável (V155)

A partir da versão **V155**, o ecossistema RAG e os modelos preditivos da Laya contam com o **`OKXUniverseService`** (`backend/app/services/okx_universe_service.py`):
1. **Mapeamento de 489 Instrumentos Perpétuos USDT-SWAP**:
   - Resolução assíncrona dos contratos diretamente da OKX pública (`/api/v5/public/instruments?instType=SWAP`).
   - Carregamento de especificações canônicas: `ctVal` (valor do contrato), `tickSize` (precisão de preço), `lotSize` e `minSz` (lotes mínimos).
2. **Telemetria e Ranking de Liquidez em Tempo Real**:
   - Sincronização contínua com `/api/v5/market/tickers?instType=SWAP`, permitindo ordenar o mercado por volume financeiro real em USDT nas 24h.
   - A Laya não depende de listas estáticas de moedas; ela seleciona os ativos mais líquidos e operáveis organicamente.
3. **Geometria Inviolável de Stop e Alvo**:
   - Eliminação de qualquer código legado que gere alvos estáticos cegos (`* 1.5`).
   - `LONG`: Alvo sempre acima do preço de entrada ($> P_{\text{entry}}$) e Stop Loss abaixo ($< P_{\text{entry}}$).
   - `SHORT`: Alvo sempre abaixo do preço de entrada ($< P_{\text{entry}}$) e Stop Loss acima ($> P_{\text{entry}}$).
   - Sanitização no backend e trava geométrica no frontend (`cockpit.html`).

---

## 4. 🛠️ Guia de Manutenção e Operação

### Como Reindexar a Base do RAG após Novas Mudanças Arquiteturais:
```bash
curl -X POST http://localhost:8085/api/v1/hermes/rag/reindex
```

### Como Gerar Novos Datasets e Recalibrar a Laya:
```bash
# 1. Gerar dataset a partir dos trades recentes
curl -X POST http://localhost:8085/api/v1/ml/generate-dataset

# 2. Executar calibração fina dos pesos
curl -X POST http://localhost:8085/api/v1/ml/train-laya
```

### Como Testar o MCP via Linha de Comando:
```bash
python backend/mcp_server.py
```
*(O servidor iniciará em modo stdio aguardando frames JSON-RPC 2.0 padrão MCP)*

---

## 5. ✅ Checklist de Governança e Invariantes

- [x] **Zero Emojis na UI e Dados**: Ícones vetoriais SVG de precisão.
- [x] **Invariante Never Give Back**: Stops progressivos só avançam, nunca regridem.
- [x] **Sub-Milissegundo no RAG**: Algoritmo BM25 em memória sem gargalos de rede ou chamadas de API externas pagas.
- [x] **Segurança no MCP**: Ferramentas expostas operam estritamente sob os limites de governança do Sandbox/OKX.
- [x] **Conexão Direta H1**: O pipeline de treino e o RAG refletem fielmente a saída de acumulação em 1H com confirmação de fluxo.
- [x] **OKX Market Universe Integrado (V155)**: 489 contratos USDT-SWAP mapeados com `ctVal` e `tickSize` canônicos.
- [x] **Geometria de Alvo e Stop Blindada (V155)**: Short com alvo para baixo e Long com alvo para cima, com código legado expurgado.
