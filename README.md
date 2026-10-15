# 1Crypten 7.0 — Elite Trading System

Sistema de trading automatizado para cripto na OKX. App FastAPI unico que roda o motor real + dois laboratorios de forward-testing (Scalping Lab e Swing Lab), com gestao de risco por IA e stops progressivos (escadinha).

> Arquitetura completa e a fonte de verdade tecnica: **[MASTER_ARCHITECTURE.md](./MASTER_ARCHITECTURE.md)**.

---

## Quick Start

**Requisitos:** Python 3.12+ e credenciais OKX.

```bash
git clone https://github.com/spcompensa-glitch/1C-10.0.git
cd 1C-7.0
pip install -r requirements.txt
cp .env .env.local   # edite com suas credenciais OKX

# Inicia o app (entry point unico)
uvicorn backend.main:app --host 0.0.0.0 --port 8085
```

- **URL:** http://localhost:8085
- **Login padrao:** `admin` / `admin123`

---

## Configuracao (variaveis criticas)

```bash
OKX_EXECUTION_MODE=REAL          # REAL = live | PAPER = simulado
OKX_API_KEY_MASTER=<chave>
OKX_API_SECRET_MASTER=<secret>
OKX_PASSPHRASE_MASTER=<passphrase>
OKX_TESTNET=False
PORT=8085
JWT_SECRET_KEY=<chave-aleatoria>
FIREBASE_CREDENTIALS_PATH=serviceAccountKey.json   # opcional
```

---

## Deploy

- **Plataforma:** Railway + Docker (Python 3.12-slim, PORT 8085).
- **Entry point:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 1`.
- **Health check:** `GET /api/health`.
- Branch `main` → auto-deploy.
- **Repo:** `spcompensa-glitch/1C-10.0`

### Railway CLI

```bash
# Token de acesso (variavel de ambiente)
$env:RAILWAY_TOKEN="46dfd90f-61af-4990-992c-976cfe4984cc"

# IDs do projeto
Project ID:  34576d19-f534-443e-8813-969e758efa3a
Environment: 733c8dac-c62a-4832-ad75-1f8525f28caf
Service:     eceff4c8-6aa6-4183-acc9-cc930d8440b5 (1C-10.0)

# Comandos uteis
railway logs -p <PROJECT> -e <ENV> -s "1C-10.0"          # ver logs
railway redeploy --project <PROJECT> --environment <ENV> --service <SVC> --yes  # forcar deploy
railway service list --json                               # listar servicos
```

### Variaveis de Ambiente (Railway)

| Variavel | Valor | Observacao |
|----------|-------|------------|
| `DATABASE_URL` | `postgresql://postgres:...@mainline.proxy.rlwy.net:22832/railway` | Postgres Railway |
| `JWT_SECRET_KEY` | `1crypten-railway-secret-2026-prod` | Chave JWT |
| `OKX_EXECUTION_MODE` | `PAPER` | Modo simulado |
| `PORT` | `8085` | Porta do app |

### Dominios

| Dominio | Tipo |
|---------|------|
| `1crypten.space` | Custom domain |
| `1c-100-production.up.railway.app` | Railway default |

---

## Endpoints principais

| Rota | Metodo | Funcao |
|------|--------|--------|
| `/api/health` | GET | Health check |
| `/api/slots` | GET | Slots ativos |
| `/api/system/state` | GET | Estado do sistema |
| `/api/radar/pulse` | GET | Sinais do radar |
| `/api/sandbox/unified-state` | GET | Banca consolidada simulada |
| `/mcp` | GET/POST | Servidor Model Context Protocol (MCP 2.x) |
| `/api/v1/hermes/rag/search` | GET | Busca semântica no Segundo Cérebro (RAG) |
| `/api/v1/ml/generate-dataset` | POST | Geração de datasets para Fine-Tuning |
| `/api/v1/hermes/laya/kronos-projection` | GET | Projeção K-Line autoregressiva nos gráficos |
| `/api/hermes/chat` | POST | Chat IA (Hermes) |
| `/api/auth/login` | POST | Login (JWT) |
| `/api/admin/reset-system` | POST | Nuclear reset |

Lista completa de routers/prefixos em `MASTER_ARCHITECTURE.md` (secao 10).

---

## ❖ Kronos Conviction Scorer & Projeção Gráfica (V143)

O 1C-7.0 agora conta com um **scorer de convicção baseado em séries temporais** usando o Kronos-mini (4.1M params, AAAI 2026).

### Modos de Operação

| Modo | Requisito | Descrição |
|------|-----------|----------|
| **REAL** 🚀 | `pip install kronos-forecast torch` | Inferência com Kronos-mini (CPU, ~200MB RAM, ~1-2s por predição) |
| **FALLBACK** 🛡️ | Nenhum (padrão) | Regressão linear simples — leve, rápido, sempre disponível |

O Kronos adiciona uma **5ª dimensão** ao consenso de frota do CaptainAgent, com peso de 18% no unified_score.

**Configuração** (via `.env`):
```bash
KRONOS_ENABLED=true
KRONOS_SCORE_WEIGHT=0.18
KRONOS_INTERVAL=5
KRONOS_TIMEOUT=5.0
```

**Testes**: `cd backend && pytest tests/test_kronos_scorer.py -v` (24 testes)

---

## 🏛️ Universo de 50 Ativos de Elite & Funil de Alta Vazão (V158)

O 1Crypten 7.0 opera exclusivamente sobre uma cesta canônica de **50 ativos de elite institucional** da OKX, eliminando memecoins (`DOGE`, `PEPE`, `PENGU`, `TRUTH`, `WAL`, etc.), derivativos sintéticos e tokens de pó (`< $0.05`).

### As 5 Categorias Institucionais:
1. **Layer 1 Consagradas & Bluechips (15)**: `ETH`, `SOL`, `AVAX`, `SUI`, `NEAR`, `ADA`, `XRP`, `DOT`, `APT`, `SEI`, `HBAR`, `ALGO`, `TON`, `ATOM`, `LTC`
2. **Layer 2 & Escalabilidade (8)**: `ARB`, `OP`, `POL` (MATIC), `STRK`, `MNT`, `METIS`, `BLAST`, `ZK`
3. **DeFi, Oráculos & Liquidez (12)**: `LINK`, `UNI`, `AAVE`, `MKR`, `SNX`, `CRV`, `LDO`, `PYTH`, `ONDO`, `INJ`, `PENDLE`, `DYDX`
4. **Inteligência Artificial, DePIN & Big Data (10)**: `RENDER`, `FET`, `GRASS`, `FIL`, `TIA`, `ICP`, `AR`, `THETA`, `JASMY`, `AKT`
5. **Gaming, Metaverso & Web3 Institucional (5)**: `SAND`, `MANA`, `AXS`, `GALA`, `CHZ`

### Arquitetura do Funil em 3 Estágios:
- **Estágio 1 (Batch Tickers)**: 1 única requisição `GET /api/v5/market/tickers` captura preço, volume e variação de todos os 50 pares e do Bitcoin em 100ms.
- **Estágio 2 (Métricas MTF & Semáforo)**: Coleta controlada de Klines H1 e fluxo Rubik via `asyncio.Semaphore(10)`.
- **Estágio 3 (Deep Dive & Farol Macro)**: Convicção Kronos nos top 4 candidatos. Se o Bitcoin estiver em queda macro (`btc_trend_bias < -0.3%`), compras (LONG) de contra-tendência são vetadas, autorizando apenas operações vendidas (SHORT) a favor do fluxo.

---

## Testes

```bash
cd backend && pytest                           # todos os testes
cd backend && pytest tests/test_kronos_scorer.py -v  # testes do Kronos (24)
pytest -m "not slow"                            # apenas rapidos
pytest --cov=backend/                           # com cobertura
```

---

## Troubleshooting

| Problema | Causa | Solucao |
|----------|-------|---------|
| "Only sending to Sandbox" | `OKX_EXECUTION_MODE=PAPER` | Setar `REAL` no .env |
| Erro 429 OKX | Muitas chamadas rapidas | OKXCommandQueue (anti-429) ja ativo |
| Dashboard nao atualiza | WebSocket morto | Reiniciar backend |
| Slots nao abrem | Regime gate (ADX) | Verificar `/api/system/state` |

---

## Changelog (V136-SWING)

### Swing Lab — Trades de 1-7 dias com stops progressivos e TP baseado em S/R

- **[SWING-TRAILING]** Trailing suave 50% (era 75%) + Breakeven +12% (era +4%) — trades duram mais sem dar lucro embora
- **[SWING-LEVERAGE]** Fix leverage: `SWING_LEVERAGE=50` (era 10, conflito com código que usava 50)
- **[SWING-PRICE-WINDOW]** Janela de preço 30min (1800s) para Swing — evita fechar em wicks de 2min
- **[SWING-GARANTIA]** GARANTIA_TRAIL split: 50% Swing / 75% Scalping (antes统一 75%)
- **[SWING-TP]** Take Profit baseado em S/R — detecta resistências acima e cria stop ratchet progressivo
- **[SWING-PATTERNS]** Detecção de padrões gráficos: Triângulos, Topo/Fundo Duplo, Head & Shoulders
- **[SWING-PATTERN-BOOST]** Padrões gráficos boostam score do sinal (+10 a +25 pontos)

### Arquivos modificados
| Arquivo | Mudança |
|---------|---------|
| `backend/services/sandbox_service.py` | GARANTIA_TRAIL split 50%/75%, Breakeven +12% Swing |
| `backend/services/sandbox_swing_service.py` | TP S/R integration, pattern detection boost |
| `backend/services/okx_ws_public.py` | `get_conservative_price_swing()` 30min window |
| `backend/services/agents/flash_agent.py` | TP hit check, swing price window |
| `backend/config.py` | `SWING_LEVERAGE=50`, `SWING_TP_*` configs |

### Arquivos criados
| Arquivo | Função |
|---------|--------|
| `backend/services/patterns/__init__.py` | Package init |
| `backend/services/patterns/triangle_detector.py` | Triângulos (simétrico/ascendente/descendente) |
| `backend/services/patterns/double_detector.py` | Topo/Fundo Duplo |
| `backend/services/patterns/hs_detector.py` | Head & Shoulders / Inverse H&S |
| `backend/services/pattern_detector.py` | PatternDetector unificado |

---

## Changelog (V142 — Matriz Bidimensional Laya + Kronos)

- **[LAYA + KRONOS]** Criação do `LayaKronosConfluenceService` integrando a psicologia do fluxo de baleias vs sardinhas da Laya com a previsão geométrica do Kronos (AAAI 2026).
- **[RETAIL TRAP VETO]** Veto automático de compras em euforia de varejo (LSR >= 1.35), protegendo contra falsos rompimentos.
- **[SNIPER GATILHOS]** Bônus de +15 pts para `LONG_LIQUIDATION_BOTTOM` + Kronos UP e `SHORT_SQUEEZE_EXHAUSTION` + Kronos DOWN.
- **[DYNAMIC LEVERAGE CAP]** Calibração de teto de alavancagem em 20x quando a dispersão entre caminhos do Kronos for elevada (mercado caótico).
- **[API TELEMETRIA]** Endpoint `GET /api/v1/laya/kronos-confluence` integrado ao Hermes e ao Cockpit.
- **[TESTES TDD]** 6 novos testes em `tests/test_laya_kronos_confluence.py` (6/6 passando).

---

## Changelog (V141 — Framework de Engenharia Agêntica Superpowers)

- **[SUPERPOWERS]** Adoção da metodologia de engenharia agêntica formal (`obra/superpowers`) para governança autônoma da IA.
- **[REGRAS CANÔNICAS]** `.agents/rules/superpowers_methodology.md` enforçando TDD obrigatório, Never Give Back em stops, anti-hedge e evidência obrigatória antes da entrega.
- **[7 SKILLS DE ENGENHARIA]** `.agents/skills/`:
  - `brainstorming_blueprint`: Especificação socrática conectada aos blueprints.
  - `writing_plans`: Decomposição atômica de tarefas de 2 a 5 minutos com comandos de validação.
  - `subagent_driven_development`: Despacho de subagentes com revisão em dois estágios.
  - `test_driven_development`: Ciclo Red ➔ Green ➔ Refactor para motores de trading e rotas.
  - `systematic_debugging`: Protocolo forense em 4 fases para depuração de WebSocket, PnL e locks.
  - `verification_before_completion`: Portão de saída com checklist empírico obrigatório.
  - `session_forensics`: Diagnóstico forense pós-sessão de transcrições de agentes.
- **[AGENTS.md]** Entrada canônica na raiz para todos os agentes de IA.

---

## Changelog (V136.1 — Fixes Criticos)

### Bugs corrigidos nesta sessao

#### 1. ROI Inflado (IMX +4066%, XRP +316%)
- **Causa:** `_get_peak_price()` usava preços WS de 120s que tinham spikes/stale data, inflando `max_roi` permanentemente
- **Fix:** Removido `_get_peak_price()` do calculo de ROI em `flash_agent.py`. Agora usa apenas `current_price`
- **Fix:** Sanity cap `min(roi, 300.0)` em 3 pontos — 300% = 6% variacao com 50x leverage
- **Arquivos:** `flash_agent.py:148-156`, `flash_agent.py:362-366`, `sandbox_service.py:1507-1514`

#### 2. Banca Nao Atualiza ($10,000.00 com 0% retorno)
- **Causa 1:** Hardcoded `$200.00` em 4 lugares no `sandbox_service.py` em vez de ler `contract_meta.margin`
- **Causa 2:** `update_banca_status()` falhava com `BancaStatus() got multiple values for keyword argument 'id'`
- **Fix:** Substituido `* 200.00` por `(t.contract_meta or {}).get("margin", 200.0)` em todas as contas de PnL
- **Fix:** `data.pop("id", None)` antes de criar `BancaStatus(id=1, **data)` em `database_service.py:527`
- **Arquivos:** `sandbox_service.py:1359-1383`, `database_service.py:524-530`

#### 3. Captain Silenciosamente Crashando
- **Causa:** `asyncio.create_task(_process_single_signal)` — erros eram engolidos silenciosamente
- **Fix:** Wrapper `_safe_process_single_signal()` com try/except + finally que sempre limpa `active_tocaias`
- **Arquivo:** `captain.py:1175-1186`

#### 4. DECOR-HUNTER Bloqueado em LATERAL
- **Causa:** Sinais DECOR-HUNTER nao tinham `strategy_class`, caiam no default `"VELOCITY FLOW"`, eram bloqueados pelo filtro de regime
- **Fix:** Check `is_decor_hunter` por `radar_mode/strategy/slot_type` contendo "DECOR" — imune ao filtro LATERAL
- **Arquivo:** `captain.py:1219-1228`

### Comandos de manutencao

```bash
# Limpar trades sandbox (reseta banca para $10,000)
POST /api/sandbox/clear       # Scalping Lab
POST /api/sandbox/swing/clear # Swing Lab

# Reset nuclear do sistema
POST /api/admin/reset-system  # Limpa tudo: positions, slots, locks, Firebase

# Verificar estado
GET /api/sandbox/unified-state  # Banca consolidada
GET /api/sandbox/trades?active_only=true  # Trades ativos
GET /api/system/state           # Estado geral do sistema
```

---

## Changelog (V134)

- **[KRONOS]** Novo serviço de scoring de convicção via séries temporais (`backend/services/kronos_scorer.py`)
- **[CAPTAIN]** Kronos integrado como 5ª dimensão no consenso de frota (peso 18% no unified_score)
- **[CONFIG]** 7 novas configurações: `KRONOS_ENABLED`, `KRONOS_MODEL_NAME`, `KRONOS_SCORE_WEIGHT`, etc.
- **[CLEANUP]** Remoção completa do legado Bybit (26 arquivos, `pybit` removido do requirements)
- **[TESTS]** 24 novos testes para o KronosScorer (24/24 passando)

**Mantenedor:** Pedro Kalelivia
**Repositorio:** https://github.com/spcompensa-glitch/1C-10.0
