# MASTER_ARCHITECTURE.md — 1Crypten 8.4.4 (V226 - 50X SNIPER RISK CAP & PURGA DO HIGH_2H_WINDOW)

Fonte unica de verdade arquitetural. Extraido diretamente do codigo-fonte (nao de historico de versoes).
Este e o unico documento de arquitetura do projeto — o Hermes le os primeiros ~8000 caracteres deste arquivo em cada resposta (`hermes_agent.py:_load_architecture_context`), portanto os fatos mais criticos ficam no topo.

*Verificado contra o codigo em 2026-11-19. VERSION no codigo: `backend/main.py` VERSION="V226-50X-SNIPER-RISK-CAP-SOVEREIGN". DEPLOYMENT_ID="V226_TITAN_SOVEREIGN_SYSTEM". Invariantes V226 Escritas em Pedra: 1) Teto Rígido Institucional de Stop Loss em 50X (`max_stop_dist = 0.0070`): Em 50X Margem Cruzada, a distância do Stop Loss é limitada a no máximo 0.70% de preço (max -35.0% de ROI / -$3.500 no lote de $10.000), extirpando a anomalia de stops a 2.61% (-135% ROI / -$13.5k). 2) Purga Canônica de high_2h_window do Stop Loss: O cálculo de stop de entradas sniper nunca mais referencia o topo de 24 horas; ancoragem estrita na microestrutura do repique de 30M / SMA 21 com folga de apenas +0.25%, respeitando o teto de 0.70%. 3) Desasfixia de Breakeven para LAYA_PULLBACK_HUNTER_2H_30M: Isenção permanente de SCRATCH_GUARD_REJECTION (+30% ROI), restaurando a relação Risco:Retorno de 1:1.5 até 1:10. 4) Manômetro de Amplitude Titan (-60° a +60°): Monitoramento em tempo real do percentual de contratos acima da SMA 21 no 2H sobre o universo OKX (534 tickers e 31 Titãs) governando regimes macro e vetos de compra contra a maré. 5) Painel Soberano de Governança (Opção B): Escudos de Proteção na Banca Soberana com Piso de $140k (80% do lucro máximo protegido), Circuit Breaker anti-tilt (congelamento após 2 stops consecutivos), Consolidation Ceiling Sniper (>= 62% da caixa 2H) e Risco Ativo 2+2+2+2 no Risco Zero. 6) Calibração de Gatilhos Titan V225: Limiares de pavio e absorção calibrados em 30M e suporte a Breakdown 2H com autorização de altcoins Titãs no Slot 1 sob Farol BTC BEAR. 7) Telemetria Unificada V224: Micro-caching inteligente (1.2s TTL) em `/api/cockpit/telemetry` e redirect 301 de `/laya` para `/telemetry`. 8) Titan Macro Trend Lock V222: Proibição de LONGs em regime macro de baixa (SMA 8 < SMA 21 de 2H); purga da Águia Fusion com exclusividade da Pullback Hunter 2H/30M. 9) Navio Almirante V221: Slot 1 privativo do BTC com mesa zerada; simbiose direcional 100% da frota; expansão autofinanciada 2+2+2+2 no Risco Zero (+45%/+60% ROI).*
---

## 1. Visao Geral

1Crypten e um sistema de trading quantitativo e institucional automatizado para contratos perpétuos na OKX. Roda sob um app FastAPI unico (`backend.main:app`, porta 8085) que orquestra a frota soberana do Titan Engine com supervisão cognitiva da Laya Neural System 1 e auditoria forense do Hermes.

- **Entry point (unico)**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` (Procfile / railway.json / Dockerfile). **Nao existe `main.py` na raiz.**
- **Backend**: FastAPI (Python 3.12-slim)
- **Frontend & Design System**: HTML/JS standalone no padrão **Binance Design System** (`#0B0E11` Deep Canvas, `#1E2329` Cards, `#2B3139` Borders, `#FCD535` Iconic Yellow, `#0ECB81` Green, `#F6465D` Red) integrado com o motor matemático de **Thinking Orbs** em 15 pontos estratégicos da UI (`backend/app/static/cockpit.html`, `frontend/cockpit.html`, `hermes.html`, `market.html`, `mobile_app.html`).
- **Exchange**: OKX (SWAP / Portfolio Margin). Modo `PAPER` (simulado) ou `REAL`, via `OKX_EXECUTION_MODE`.
- **Semantica PAPER vs REAL (espelho do Cockpit)**: Em **PAPER**, o Cockpit (`cockpit.html`) representa o **Sandbox** — tanto o *Net Worth* (Banca Simulada Consolidada via `get_sandbox_unified_balance`) quanto o *Painel de Custodia* (ordens ativas da frota de 8 slots). Em **REAL**, a OKX recebe as ordens e o Cockpit representa a banca real da OKX.
- **Plataforma**: Railway + Docker
- **Persistencia & Memória Unificada**: PostgreSQL (SSOT) + Firebase (Firestore/RTDB) + SQLite WAL (`local_sniper.db`) + Obsidian Vault (`vault_galaxy/` para voz, chat e diários).
- **Banco de Dados de Contexto OpenViking (`viking://`)**: Sistema de arquivos virtual cognitivo com Progressive Disclosure em 3 camadas: L0 (Abstract executivo ~100 tokens), L1 (Overview operacional ~1.5k tokens) e L2 (Detail completo). O Hermes e os agentes navegam pelas raízes `viking://resources/`, `viking://user/memories/` e `viking://agent/skills/`.
- **Memória Auto-Evolutiva de Trading**: Ao fechar qualquer trade (Stop, TP, Trailing Stop ou Emergência), o sistema sintetiza automaticamente o caso em `viking://user/memories/cases/` e persiste no Obsidian Vault (`vault_galaxy/journal/`), eliminando a necessidade de o operador humano lembrar o sistema de regras ou erros passados.
- **Protocolos de IA & RAG**: OpenViking Context Engine + RAG Semântico (`RAGService`), Model Context Protocol (`mcp_bridge.py` MCP 2.x - 16 Ferramentas), Laya Neural System 1 (v0.4.31) e Hermes Intelligence Orchestrator.
- **Pipeline de Fine-Tuning & Datasets ML**: Geração contínua de datasets JSONL para calibração RLCD da Laya e adaptação temporal do Kronos via rotas `/api/v1/ml/*`.
- **Precisão & Quantização Inviolável**: Motor `OKXUniverseService` com suporte a 507 pares perpétuos da OKX, garantindo tick size exato (`format_price_by_tick`), lot size e quantização correta de contratos (`quantize_order_contracts`).

### 1.1 Diagrama de Arquitetura do Sistema

```mermaid
flowchart TD
    subgraph Frontend["Frontend Client (Binance Design & Thinking Orbs)"]
        UI_Cockpit["cockpit.html (Cockpit Soberano: Titan Engine + Radar 507 + 8 Slots Swing 2H)"]
        UI_BreadthGauge["Painel de Bordo (Manômetro de Amplitude Titan -60° a +60°)"]
        UI_ProtectionHUD["Governança & Escudos de Proteção (Piso $140k + Circuit Breaker + Ceiling Sniper)"]
        UI_Telemetry["telemetry.html (Telemetria Unificada: uPlot 60 FPS + Muralhas Liquidação + Microestrutura Sniper)"]
        UI_Plutus["plutus.html (Método ARCA Renda Perpétua + Universal Shell)"]
        UI_Hermes["hermes.html (Hermes Orchestrator & Forensic Audit)"]
        UI_Redirect["/laya -> 301 HTTP Redirect permanente para /telemetry (Titan 360 Unificado)"]
        UI_Charts["4 Quadrant Grid Charts (LightweightCharts + Weaving Orbs)"]
        UI_TitanHUD["Titan Radar HUD & Laya Neural Supervision"]
        UI_Screener["Screener Modal (Universal 507 Pares / 30 Titãs)"]
    end

    subgraph API_Routers["FastAPI Routers (backend.main:app:8085)"]
        R_Slots["/api/slots (Active Trades Mirror - 8 Slots Cap)"]
        R_State["/api/sandbox/unified-state (Equity & Net Worth)"]
        R_Pulse["/api/radar/pulse & /api/v1/hermes/laya/pulse"]
        R_Breadth["/api/market/breadth & /api/cockpit/telemetry (Regime Macro & Amplitude)"]
        R_Kronos["/api/v1/hermes/laya/kronos-projection"]
        R_Viking["/api/v1/hermes/viking/tree, /read, /search, /sync & /commit-lesson"]
        R_RAG["/api/v1/hermes/rag/search & /status & /reindex"]
        R_ML["/api/v1/ml/status & /dataset-stats & /generate-dataset & /train-laya"]
        R_MCP["/api/v1/mcp/tools (Catálogo 16 Ferramentas)"]
        R_Intel["/api/v1/market/screener-matrix & /ai-context (1C-EXP & 1C-RANGE)"]
        R_Precision["/api/v1/market/contract-specs (TickSz & LotSz Audit)"]
        R_Heatmap["/api/v1/hermes/laya/liquidation-heatmap (Coinglass Matrix & Whale Magnet)"]
        R_Telemetry["/api/telemetry/stats & /timeseries (Ring Buffer 3600s + Circuit Breaker)"]
    end

    subgraph Protocol_Bridges["Protocol & AI Bridges"]
        MCP_Bridge["MCP 2.x Starlette Mount (/mcp/sse, /mcp/tools - 16 Ferramentas)"]
        OpenViking_Engine["OpenViking Context Engine (viking:// Virtual FS - L0/L1/L2 Progressive Disclosure)"]
        RAG_Engine["RAGService (BM25 / TF-IDF Second Brain: Blueprints + Vault)"]
        LayaNeural["Laya Neural v0.4.31 (Rede Neural System 1, Cognição Reflexa & Calibração RLCD)"]
        ML_Trainer["ML Fine-Tuning Pipeline (Dataset Generator JSONL + LoRA / Adapter)"]
    end

    subgraph Decision_Engines["Tactical & Decision Engines"]
        TitanEngine["Titan Engine (Comandante Quantitativo, Alocação $10.000 Cross 50X)"]
        TitanDualTier["Dual-Tier Engine: Grau 1 SMA8 Sniper vs Grau 2 SMA21 Sweep Exaustão"]
        TitanRadar["Titan Radar (Scanner Universal 507 Pares OKX + Farol BTC 2H)"]
        AltPump["AltPumpIgnition Engine (Triple Confluence: BTC.D Drop + Pearson < 0.45 + 1C-EXP >= 70)"]
        BTCSpecialist["BTCSpecialist (Farol BTC 2H: SMA 8 x SMA 21 & Veto Bull/Bear)"]
        SignalGen["SignalGenerator (Pearson 15h/4h Return Correlation & Decorrelation Hunter)"]
        Kronos["KronosScorer (AAAI 2026 Temporal Trajectory)"]
        LayaFlow["LayaFlowService (OKX Rubik LSR & OI Delta)"]
        OKXUniverse["OKXUniverseService (507 Pares OKX + TickSz/LotSz/CtVal Engine)"]
        MarketIntel["MarketIntelEngine (Universal Screener 507 Pares, 1C-EXP, 1C-RANGE)"]
        StopLadder["OrderProjectionService (Dual Breakeven V218 45/60 & Elastic Trailing 50%)"]
        SanityGate["Price Sanity & Structural ATR Stop Gate (1.8% - 3.8%)"]
        MarketBreadth["Market Breadth Engine (SMA21 2H Universe 534 Tickers / 31 Titãs)"]
        CoinglassHeatmap["CoinglassHeatmapService (Liquidation HeatMap Matrix & Whale Magnet Vector)"]
        TelemetryEngine["TelemetryService (Sub-ms Ingestion, Throughput, Net Worth Tick-a-Tick)"]
    end

    subgraph Sandbox_Labs["Execution Fleet Labs"]
        ScalpLab["SandboxService (Frota Soberana 8 Slots 50X Margem Cruzada - $10k Cada)"]
        SwingLab["SandboxSwingService (Swing Lab - Paused / SWING_SCAN_ENABLED=False)"]
    end

    subgraph Ingestion_Layer["Market Ingestion Layer"]
        OKX_WS["OKXWSPublic (Live WS Tickers, Extreme Low/High 120s)"]
        OKX_REST["OKXRest (Batch 507 SWAP Tickers & Contract Instruments)"]
        CoinGecko["CoinGecko/CoinCap API (Global BTC.D Live Oracle)"]
    end

    subgraph Data_Layer["Data & Persistence Layer"]
        DB_SQLite["SQLite WAL (local_sniper.db)"]
        DB_Postgres["PostgreSQL (Production SSOT)"]
        DB_Firebase["Firebase RTDB / Firestore (Mirroring)"]
        DB_Galaxy["Obsidian Vault (vault_galaxy)"]
        Docs_Blueprints["Blueprints (docs/blueprint/ 01 a 09)"]
    end

    UI_Cockpit --> R_Slots
    UI_Cockpit --> R_State
    UI_Cockpit --> R_Pulse
    UI_Cockpit --> R_Breadth
    UI_Cockpit --> UI_BreadthGauge
    UI_Cockpit --> UI_ProtectionHUD
    UI_Cockpit --> UI_Screener
    UI_Charts --> R_Kronos
    UI_Screener --> R_Intel
    R_Breadth --> MarketBreadth
    MarketBreadth --> OKXUniverse

    MCP_Bridge --> ScalpLab
    MCP_Bridge --> DB_SQLite
    MCP_Bridge --> RAG_Engine
    MCP_Bridge --> OpenViking_Engine
    MCP_Bridge --> MarketIntel
    MCP_Bridge --> OKXUniverse
    R_RAG --> RAG_Engine
    RAG_Engine --> DB_Galaxy
    RAG_Engine --> Docs_Blueprints

    OpenViking_Engine --> DB_Galaxy
    OpenViking_Engine --> Docs_Blueprints
    R_Viking --> OpenViking_Engine
    R_ML --> ML_Trainer
    R_MCP --> MCP_Bridge

    R_Slots --> ScalpLab
    R_State --> DB_SQLite
    R_Pulse --> TitanEngine
    R_Intel --> MarketIntel
    R_Precision --> OKXUniverse

    TitanEngine --> TitanDualTier
    TitanEngine --> TitanRadar
    TitanEngine --> AltPump
    TitanEngine --> BTCSpecialist
    TitanEngine --> SignalGen
    TitanEngine --> OKXUniverse
    TitanEngine --> MarketIntel
    TitanEngine --> LayaFlow
    TitanEngine --> Kronos
    TitanEngine --> RAG_Engine
    TitanEngine --> SanityGate
    TitanEngine --> CoinglassHeatmap
    R_Heatmap --> CoinglassHeatmap
    SanityGate --> ScalpLab

    CoinGecko --> BTCSpecialist
    OKX_WS --> ScalpLab
    OKX_WS --> TitanEngine
    OKX_REST --> OKXUniverse
    OKX_REST --> MarketIntel

    ScalpLab --> StopLadder
    ScalpLab --> OKXUniverse
    ScalpLab --> DB_SQLite
    DB_SQLite -.-> DB_Postgres

    UI_Telemetry --> R_Telemetry
    R_Telemetry --> TelemetryEngine
    TelemetryEngine --> OKX_WS
    TelemetryEngine --> ScalpLab
    TelemetryEngine --> LayaRouter
```

---

## 2. Invariantes Soberanas e Constantes Principais

### 2.0 Invariantes Rígidas de Risco e Trading (Escritas em Pedra)
1. **Margem Cruzada Soberana (Cross Margin 50X - Escala Institucional $100k)**:
   - Toda e qualquer operação do 1Crypten opera estritamente sob **Margem Cruzada 50X**. A banca de **$100.000,00** atua como colateral garantidor soberano.
   - É terminantemente proibido calcular limites de stop loss ou alegar risco de liquidação baseado em fórmulas de margem isolada (1.8%). Margem fixa de $10.000,00 por lote (exposição nocional de $500.000,00). Stops pertencem à estrutura técnica (topo/fundo no 2H/4H ou SMA 21) com respiro livre de 12h a 24h (amplitude de até 3.8% no preço à vista).
2. **Regra de Expansão em Bola de Neve (2 + 2 + 2 + 2)**:
   - **Risco Inicial (Máx 2 Ordens)**: Máximo de 2 ordens abertas simultâneas em risco não protegido ($20.000 de margem comprometida = 20% da banca; 80% ou $80.000 livres em colateral garantidor na Margem Cruzada 50X).
   - **Expansão Autofinanciada (Slots 3 a 8)**: A 3ª, 4ª, 5ª, 6ª, 7ª e 8ª ordens só abrem conforme ordens anteriores atinjam Breakeven Soberano (+60.0% ROI / +1.2% de preço a favor com stop travando +30.0% ROI líquido / +$3.000.00 fixos).
   - **Ápice da Frota (8 Slots Cheios)**: Exatamente 6 ordens com Risco Zero (lucro travado) e no máximo 2 ordens em risco ativo vivo.
   - **Cadência Ágil de Despacho (45s)**: Intervalo de 45 segundos entre entradas, garantindo formação ordenada da frota sem sobreposição no livro.
3. **Alvo Chão +300% de ROI (+$30,000.00)**:
   - O alvo mínimo de realização por trade é +300% de ROI, garantindo pelo menos +200% de lucro travado no Degrau 5 (+$20.000.00 fixos garantidos), deixando o trailing correr solto com colchão largo (>= 100% ROI de respiro livre) até a exaustão da tendência no gráfico de 4H.
   - Desativação do trailing aritmético de 70% abaixo dos +300% ROI para evitar asfixia prematura no ruído de 5 minutos.
4. **Never Give Back**: Stops progressivos só sobem, nunca recuam. Piso Soberano em $85.000,00.
5. **Veto Soberano Farol BTC 2H (Tolerância Zero)**: Quando o Bitcoin não estiver estritamente em regime BULL (SMA 8 > SMA 21 e viés comprador positivo no 2H), compras de QUALQUER altcoin são sumariamente VETADAS (`VETO_FAROL_BTC`). Sem exceções para estratégias secundárias (Liquidity Hunt ou reversões 15M). A frota opera 100% em SHORT a favor do fluxo ou mantém capital em HOLD.
6. **Módulo de Fricção Real Institucional (Hi-Fi)**: Simulação com fidelidade total ao mercado real da OKX, aplicando slippage dinâmico de livro de ofertas por tiers de liquidez em ordens de $500k nocionais (Tier 1: 0.025%, Tier 2: 0.05%, Tier 3: 0.10%), débito/crédito real de Funding Rates a cada 8 horas (00:00, 08:00, 16:00 UTC) e Stop Gap Penalty em rompimentos voláteis.

| Constante | Valor | Fonte |
|-----------|-------|-------|
| `LEVERAGE` (Titan Soberano) | 50x (Cross Margin Soberana) | `MASTER_ARCHITECTURE.md` / AGENTS.md |
| `BANCA_BASE_SOBERANA` | $100,000.00 USD Pristine | `config.py` / `database_service.py` |
| `PISO_SOBERANO_PROTEGIDO` | $85,000.00 USD (85% da banca base) | `sandbox_service.py` / Never Give Back |
| `MAX_FLEET_SLOTS` | 8 Slots Simultâneos (2 em risco vivo + 6 em expansão Breakeven) | `laya_router_service.py` / V206 |
| `UNPROTECTED_RISK_LIMIT` | 2 Ordens em Risco Simultâneo ($20.000 margem = 20% banca) | `laya_router_service.py` / V206 |
| `FLEET_DISPATCH_CADENCE` | 45 Segundos entre aberturas | `laya_router_service.py` / V204 |
| `MARGIN_PER_TRADE` (Titan) | $10.000.00 Fixo por Ordem (50X Cruzada = $500k nocional) | `laya_router_service.py` / V217 |
| `BREAKEVEN_1_TRIGGER_ROI` | +45.0% ROI (+0.90% no preço em 50X) | `order_projection_service.py` / V218 |
| `BREAKEVEN_1_LOCK_ROI` | +18.0% ROI (+0.36% no preço / Risco Zero Real +$300 a +$900) | `order_projection_service.py` / V218 |
| `BREAKEVEN_2_TRIGGER_ROI` | +60.0% ROI (+1.20% no preço em 50X) | `order_projection_service.py` / V218 |
| `BREAKEVEN_2_LOCK_ROI` | +30.0% ROI (+0.60% no preço / +$3.000.00 fixos garantidos) | `order_projection_service.py` / V218 |
| `ELASTIC_TRAILING_GAP` | 50.0% ROI de folga a partir de +100% ROI (`max(50.0, max_roi - 50.0)`) | `sandbox_service.py` / V217 |
| `ALVO_CHAO_MIN_ROI` | +300% ROI (+$30.000.00 por ordem) | `order_projection_service.py` / V217 |
| `PROFIT_LOCK_CHAO_ROI` | +200% ROI (+$20.000.00 fixos garantidos) | `order_projection_service.py` / V217 |
| `STRUCTURAL_STOP_DIST` | Até 3.8% de preço (Buffer estrutural topo/fundo 2H/4H) | `laya_router_service.py` / V197 |
| `STOP_LOSS_QUARANTINE` | 7200s (2 Horas Anti-Reincidência) | `laya_router_service.py:885` / V159 |
| `WHITELIST_TITANS_30` | Top 30 Altcoins de Elite Institucional + BTC Flagship | `okx_universe_service.py:42` / V215 |
| `BTC_ROLE` | Ativo Flagship Negociável + Farol Macro 2H Soberano | `laya_router_service.py` / V215 |
| `SWING_SCAN_ENABLED` | **False (PAUSADO / GATE SOBERANO)** | `config.py:166` / V146 |
| `MCP_MOUNT` | `/mcp` (`/mcp/sse`, `/mcp/tools` - 16 Ferramentas) | `backend/main.py:707` / V144 |
| `RAG_ROUTER` | `/api/v1/hermes/rag` (`/search`, `/status`, `/reindex`) | `backend/routes/rag_routes.py` |
| `ML_ROUTER` | `/api/v1/ml` (`/generate-dataset`, `/train-laya`, `/status`) | `backend/app/api/v1/endpoints/ml.py` |
| `OPENVIKING_FS` | `viking://` Virtual FS (L0/L1/L2 Progressive Disclosure) | `backend/services/openviking_context_service.py` |

### 2.1 Motor Soberano Laya V160 (Metodologia Encryptos: Top 30 Altcoins & BTC Oráculo)
1. **Top 30 Altcoins de Elite Institucional da OKX**:
   - `ETH`, `SOL`, `NEAR`, `SUI`, `AVAX`, `ADA`, `XRP`, `LINK`, `DOT`, `SEI`, `TON`, `ARB`, `OP`, `ZK`, `XPL`, `POL`, `UNI`, `AAVE`, `MKR`, `PYTH`, `ONDO`, `INJ`, `PENDLE`, `RENDER`, `FET`, `TIA`, `ICP`, `AR`, `DOGE`, `LTC`.
   - Proibido varrer pares ruidosos, memecoins ilíquidas ou ativos de baixa capitalização.
2. **BTC como Oráculo Macro Exclusivo (Zero Trades no BTC)**:
   - Monitoramento contínuo de `BTC-USDT` (Spot) vs `BTC-USDT-SWAP` (Perpétuo) para capturar o *Lead-Lag* institucional.
   - O BTC atua como a bússola/farol de tendência e dominância, sendo estritamente vetado para abertura de posições de trade para concentrar o capital e os 15x de alavancagem na assimetria elástica das altcoins.
3. **Matriz de Clima por Dominância do Bitcoin (BTC.D) e Farol Macro**:
   - `ALTCOIN_EXPANSION`: BTC.D em queda (< 56.5% ou FALLING) + BTC estável/positivo -> Compras agressivas (LONG) em 15x liberadas; Vendas (SHORT) vetadas.
   - `ALTCOIN_BLOODBATH`: BTC.D subindo (>= 58.5% ou RISING) + BTC em queda (< -1.0%) -> Veto total de compras (LONG); Apenas SHORTS autorizados a favor da sangria.
   - `BTC_DRAINAGE`: BTC positivo (>= +0.3% ou trend bias positivo) com Dominância elevada (>= 59.0% ou RISING) -> O Bitcoin atua como sucção de liquidez: VETO TOTAL DE SHORTS EM ALTCOINS (proibido shortar altcoins no rali do BTC).
   - `CONSOLIDATION_CHOP`: Mercado lateral -> Caça de liquidez em extremidades. Se BTC.D >= 58.0% e BTC > +0.2%, SHORTs em altcoins também são preventivamente vetados.
4. **Tríade de Blindagem Institucional da Laya (V162)**:
   - **Circuit Breaker Global Anti-Tilt**: Se 3 stops quaisquer ocorrerem em janela de <= 90 minutos (5.400s), todas as novas aberturas são congeladas por 45 minutos (2.700s), resfriando a banca contra liquidações de mercado.
   - **Descorrelação Setorial entre os 4 Slots**: Carteira dividida em 5 clusters (`L1_BLUECHIP`, `L2_ROLLUPS`, `DEFI_ORACLE`, `AI_DEPIN`, `MEME_SPEC`). Limite rígido de no máximo 2 posições simultâneas do mesmo cluster para evitar drawdown de ativos correlacionados.
   - **Confirmação de Agressão / CVD no Suporte/Resistência**: Toques em suportes H1 com agressão vendedora violenta (`taker_sell_ratio >= 1.40x`) são vetados por *Faca Caindo*. Toques em resistências com agressão compradora (`taker_buy_ratio >= 1.40x`) são vetados por *Pressão Compradora Ativa*.
5. **Quarentena Rígida Anti-Reincidência (2 Horas)**:
   - Todo ativo que sofrer Stop Loss entra em quarentena inegociável de 7200 segundos (2h), impedindo perdas repetidas no mesmo par.
6. **Stops Estruturais de Borda H1 (Eliminação de Ruído)**:
   - Distância de Stop Loss ancorada em `max(0.028, min(0.045, (atr_pct * 1.8) / 100.0))`.
   - Stops calibrados para 2.8% a 4.5% fora da acumulação, eliminando violinadas de 15 segundos causadas por micro-ruído de spread.
   - `stop_roi` calibrado proporcionalmente à alavancagem (`calculate_roi`), eliminando o bug de capping a -3.5% ROI que correspondia a -0.23% de preço.
6. **Hierarquia Integrada de 5 Setups Soberanos da Laya (V190)**:
   - **Camada 0: Fusão Águia + Encryptos (`LAYA_AGUIA_FUSION`)**: Confluência de rompimento e alinhamento de médias no 2H combinada com indicadores Encryptos.
   - **Camada 1: Saída de Acumulação H1 (`LAYA_SMART_MONEY_H1`)**: Rompimento com volume e expansão para fora da faixa de consolidação de 1H, confirmado por capital novo (`OI Delta > +0.5%`) e proporção favorável de baleias (`LSR <= 1.15` em LONG ou `>= 1.25` em SHORT).
   - **Extirpação Permanente da Reversão Intermediária 15M (`LAYA_INTERMEDIATE_REVERSAL_15M`)**: O módulo de reversão em 15M foi sumariamente extirpado. 100% das ordens operam sob a subordinação macro do 2H (SMA 8 x SMA 21) + 30M Pullback Hunter (`LAYA_PULLBACK_HUNTER_2H_30M`), eliminando entradas precipitadas contra a tendência que causavam stopouts cheios.
   - **Isenção do Veto de Ímã de Liquidez para Pullback Hunter e Águia Fusion (V215)**: O `[VETO IMA DE LIQUIDEZ]` foi isentado para `LAYA_PULLBACK_HUNTER_2H_30M` e `LAYA_AGUIA_FUSION` tanto na Camada 1 quanto no Portão Final de Execução. Estratégias que operam a exaustão de pullback em resistências (toque na SMA 8 de 2H) não são bloqueadas pela presença de muralhas de liquidação de sweep acima do preço.
   - **BTC Flagship Trading 50X & Farol Macro Duplo (V215)**: O Bitcoin (`BTC-USDT-SWAP`) foi plenamente integrado à cesta dos Titãs de Elite negociáveis sob 50X Margem Cruzada ($1.000 margem / $50.000 nocional) com slippage zero e máxima liquidez, mantendo sua função primária e inviolável de Farol Macro 2H para todo o ecossistema. Suas próprias entradas respeitam estritamente a tendência de seu gráfico de 2H (SMA 8 x 21).
   - **Camada 2: Reversão nos Extremos da Faixa (`LAYA_RANGE_REVERSAL`)**: Atua diretamente nos regimes de `CONSOLIDATION_CHOP` / `MEAN_REVERSION` (ADX < 25). Quando o preço testa o piso (`pos <= 25%` ou a menos de 1.5% do suporte H1), dispara **LONG** de absorção com Stop Loss estrutural abaixo do suporte. Quando o preço testa o teto (`pos >= 75%` ou a menos de 1.5% da resistência H1), dispara **SHORT** de exaustão contra o varejo em FOMO.
   - **Camada 3: Momento Mola 15M (`LAYA_MOMENTO_MOLA`)**: Detecta compressão extrema de volatilidade das Bandas de Bollinger (`bb_width_pct <= 6.5%`) nos extremos de canal de 15 minutos, armando disparos elásticos direcionais com proteção contra fundos falsos.
   - **Camada 4: DVWAP Reversion 5M (`LAYA_DVWAP_REVERSION`)**: Opera desvios elásticos contra a VWAP intradiária (`diff_pct >= 1.5%`), ancorada no preço típico ponderado por volume `(High + Low + Close) / 3`, vetando compras contra quedas do Bitcoin e protegendo contra taxas adversas via Funding Shield.
7. **Motor de Projeção & Singleton SSOT**:
   - `order_projection_service.py` padronizado como singleton único (`order_projection_service`) com alias canônico `proj_service`, unificando a projeção de ROI, cálculo de Stops escalonados (Never Give Back) e metadados de execução para o Sandbox e Cockpit.

8. **Invariante de Alavancagem Obrigatória (15X a 20X) [V172]**:
   - Todas as ordens autônomas abertas pela Laya Soberana operam **exclusivamente em 15x ou 20x** (sem valores intermediários).
   - Proibição Absoluta: Nenhuma ordem pode ser aberta com alavancagem inferior a 15x (veto irrestrito a 5x, 8x, 9x ou 10x).
   - Clamp Matemático de Execução: `leverage = 20 if (calc_lev >= 18 or chosen.get("score", 0) >= 90) else 15` com `target_stop_roi = 35.0` ancorado na distância estrutural de Stop Loss de preço H1.
   - Compatibilização de Stop ROI: O stop financeiro inicial é mantido proporcionalmente na faixa de -30% a -38% de ROI, garantindo proteção de capital sem encurtar a distância técnica do canal H1.

### 2.2 Radar Universal Encryptos V163 (507 Contratos OKX & Detecção de Ignição de Robôs)
1. **Varredura Universal dos 507 Pares OKX (`market_intel_engine.py`)**:
   - Ingestão atômica de 100% dos contratos perpétuos USDT-SWAP da OKX em única requisição (<300ms).
   - Filtro de higiene institucional: descarta contratos zumbis (volume 24h < $500k USD).
2. **Algoritmo de Aceleração Smart Money (`1C-EXP` & `bot_ignition`)**:
   - Detecta a ativação repentina de robôs institucionais/Market Makers (volume spike 5m, compressão de volatilidade e delta de OI).
   - Ativos com `1C-EXP >= 70` recebem a chancela `bot_ignition = True`.
3. **Controle Integrado por Laya e Hermes**:
   - **Laya**: Injeta automaticamente as altcoins em ignição institucional na esteira autônoma de execução (`scan_and_execute_autonomous`), validando contra a tríade de blindagem, stops de 2.8% a 4.5% ATR e Never Give Back.
   - **Hermes**: Comando operacional direto no chat para auditar quais robôs estão ligados no mercado hoje, gerando relatórios executivos em tempo real.
4. **UI Cockpit**:
   - Modal do Screener com alternância em 1 clique entre **Universal (507 Pares)** e **Titãs (30)**.

### 2.3 Motor de Precisão e Quantização Inviolável de Contratos OKX (V165)
1. **Dicionário Dinâmico de 507 Especificações Canônicas (`okx_universe_service.py`)**:
   - Carregado na inicialização via `/api/v5/public/instruments?instType=SWAP`.
   - Indexa `tickSz`, `lotSz`, `minSz`, `ctVal` e `ctMult` para cada par.
2. **Quantização Matemática de Preço por Tick Size**:
   - `format_price_by_tick(price, symbol)`: Converte o preço float para o múltiplo exato do `tickSz` do par (ex: BTC com `0.1` -> `82450.1`, PEPE com `0.00000001` -> `0.00000985`).
   - Elimina rejeições de ordem OKX por `Invalid price precision`.
3. **Quantização de Lotes e Contratos por `lotSz` e `ctVal`**:
   - `quantize_order_contracts(notional_usd, mark_price, symbol)`: Converte o valor nocional em dólares para a quantidade exata de contratos inteiros ou fracionários permitidos.
   - Trata automaticamente memecoins com `ctVal = 10.000.000` (ex: PEPE) e pesos-pesados com `ctVal = 0.01` (ex: BTC).
4. **Governança Hermes e MCP 2.x**:
   - Ferramenta MCP `get_contract_precision_audit(symbol)` disponível para agentes externos e Claude Desktop.
   - Comando `auditar contrato <SIMBOLO>` no Hermes para inspeção operacional instantânea pelo trader.

### 2.4 Arquitetura Dual Breakeven V218 (+45% / +60%), Fricção Real & Gap Elástico 50%
1. **Degrau 1 — Breakeven Protetivo Fricção OKX $500k (+45.0% ROI / Trava +18.0% ROI)**:
   - Disparo: Acionado quando o ROI atinge **`+45.0%`** (+0.90% de variação favorável no preço do ativo sob 50X Margem Cruzada).
   - Trava de Stop: O Stop Loss é puxado instantaneamente para **`+18.0% ROI`** (+0.36% de preço a favor).
   - Cobertura de Fricção Institucional: Em contratos nocionais de $500.000,00 ($10.000 de margem a 50X), taxas de taker (0.05% abertura + 0.05% fechamento = 0.10% = 5.0% de ROI) somadas ao slippage real de livro (0.03% a 0.10% = 1.5% a 5.0% de ROI) totalizam de 6.5% a 10.0% de fricção. A trava de +18.0% garante **Risco Zero Real** com lucro líquido positivo garantido no cofre de **+$300,00 a +$900,00 USD**, eliminando permanentemente a anomalia de trades que ficavam positivos e sofriam reversão para stop loss cheio (-100%).
2. **Degrau 2 — Breakeven Soberano Consolidado (+60.0% ROI / Trava +30.0% ROI)**:
   - Disparo: Acionado quando o ROI atinge **`+60.0%`** (+1.20% de deslocamento de preço em 50X).
   - Trava de Stop: Stop travado rigidamente em **`+30.0% ROI líquido`** (+0.60% de preço).
   - Garantia de Cofre: Lucro líquido imutável de **+$3.000,00 USD** fixos garantidos no cofre.
   - Destravamento da Frota: A ordem atinge o status soberano de **Risco Zero Consolidado**, liberando imediatamente vaga para a abertura de novos slots na regra de expansão autofinanciada 2+2+2+2.
3. **Trailing Dinâmico com Gap Elástico de 50% de ROI**:
   - Ativação: A partir de **`+100.0% de ROI`** (+2.0% de preço a favor), o trailing stop dinâmico passa a rastrear o preço:
     `trail_stop_roi = max(50.0, max_roi - 50.0)`
   - Elasticidade: Concede exatamente **50.0% de ROI de folga** (1.0% de oscilação livre de preço no gráfico de 2H/30M), impedindo que correções sadias de tendência estopem precocemente posições antes do Alvo Chão.
4. **Alvo Chão Obrigatório (+300.0% ROI / +$30.000,00)**:
   - Toda ordem vencedora persegue como alvo mínimo de realização institucional os **+300.0% de ROI** (+6.0% de preço a 50X).
   - Ao bater +300% de ROI, trava pelo menos **+200.0% de ROI fixos** (+$20.000,00 garantidos no cofre), mantendo o trailing livre para surfar até a exaustão macro no gráfico de 4H.

### 2.5 Arquitetura Dual-Tier Titan Engine (Grau 1 SMA 8 Sniper vs Grau 2 SMA 21 Sweep Exaustão)
1. **Grau 1 (Sniper SMA 8 - Linha Branca)**:
   - Condição: Preço toca a SMA 8 de 2H e imprime rejeição imediata com pavio de absorção no tempo de 30M/2H.
   - Proteção de Stop: Stop loss ancorado com margem de segurança além da SMA 21 de 2H (Linha Amarela).
   - Veto Anti-Surge Smart Money (`VETO_SMART_MONEY_REPIQUE`): Se a vela furar a SMA 8 com corpo direcional forte (> 40% do candle sem pavio), o Titan Engine detecta que o Smart Money está varrendo liquidez em direção à SMA 21. A entrada na SMA 8 é vetada, aguardando o teste na SMA 21.
2. **Grau 2 (Sniper SMA 21 - Linha Amarela / Sweep de Liquidez)**:
   - Condição: O Smart Money empurra o repique até a SMA 21 de 2H para estopar o varejo que entrou adiantado. O Titan Engine monitora a exaustão na SMA 21 (pavio pronunciado ou devolução).
   - Execução Sniper: A entrada ocorre no ápice do sweep na SMA 21 com preço altamente favorável e stop protegido com folga além do topo da varredura.

### 2.6 Unificação Soberana de Responsabilidades (Titan vs Laya vs Hermes)
- **TITAN ENGINE (TITAN RADAR / TITAN 360)**: É o **comandante quantitativo soberano e executor tático**. Detém o radar de 507 pares da OKX, o Farol BTC 2H, os filtros matemáticos de médias (SMA 8 x SMA 21), a gestão da Margem Cruzada 50X ($100k bankroll), a alocação de slots (2+2+2+2), o disparo de ordens e o manejo dinâmico de trailing stops.
- **LAYA NEURAL (SYSTEM 1 v0.4.31)**: Atua estritamente como a **rede neural cognitiva reflexa**. Avalia desbalanceamento de agressão de order flow, Long/Short Ratio da OKX Rubik, delta de Open Interest, sentiment e pontuação bayesiana de convicção (score 0-100%).
- **HERMES**: Atua como o **orquestrador executivo e auditor forense**. Realiza auditoria contínua de compliance contra `MASTER_ARCHITECTURE.md`, expõe a interface de comando natural e navega no cofre de conhecimento via OpenViking e RAG.

### 2.7 Tática Liquidity Snatch Entry & Farol BTC Macro Key Zones [V219]
1. **Tática Liquidity Snatch Entry (Grau 2 Sweep Exclusivo / Caçada aos Stops Retail)**:
   - *Fundamento Institucional*: O Titan Engine não entra antecipadamente no primeiro toque de repique na SMA 8 quando há risco de varredura de liquidez. Sabendo que o Smart Money caça os stops de quem vendeu na média, o sistema aguarda pacientemente a formação completa do repique na SMA 21 (Linha Amarela).
   - *Confirmação de Exaustão*: Exige pavio de rejeição superior expressivo (`upper_wick_ratio >= 0.28` ou vela de devolução bear com pavio >= 0.18).
   - *Stop Loss Cirúrgico Sniper*: O stop é posicionado com folga enxuta logo acima da máxima do sweep (`sl_price = round(max(c_high * 1.004, major_res * 1.006, c_close * 1.012), 4)`), reduzindo a distância de stop para apenas **1.0% a 1.2% de preço** (em vez de 3.5%), eliminando completamente o calor flutuante da posição e alavancando a assimetria risco/retorno.
2. **Farol BTC Macro Key Zones & Veto de Vender Fundo (`VETO_VENDER_FUNDO_SUPORTE_BTC`)**:
   - *Mapeamento Dinâmico de Níveis Estruturais*: O serviço `LayaBTCSpecialistService` rastreia continuamente os níveis redondos e estruturais de suporte e resistência macro de 4H/Diário do Bitcoin ($65.000, $62.500, $60.000, $67.500, $70.000).
   - *Veto Preventivo de Vender Fundo*: Se o BTC estiver a **<= 1.25% de distância de um suporte institucional maior** (como os $65k atuais), novas ordens de SHORT em rompimento seco de altcoins são sumariamente bloqueadas. Entradas vendidas passam a exigir obrigatoriamente o Grau 2 (Liquidity Snatch pós-sweep completo na SMA 21).

### 2.8 Tática Consolidation Ceiling Sniper & Fôlego Estrutural de Stop Loss 2H [V220]
1. **Tática Consolidation Ceiling Sniper (`VETO_MEIO_DE_ACUMULACAO_2H`)**:
   - *Diagnóstico do Problema*: Em momentos de acumulação ou consolidação lateral de 2H/4H (como o Bitcoin consolidando entre $64.000 e $65.800 em formato de cunha ou retângulo no suporte macro), candles de 30M frequentemente produzem recuos ou repiques no meio do caixote (45% a 55% da amplitude). Vender no meio da acumulação condena a ordem a ficar paralisada por 14h+ com floating PnL nulo e exposta a violinadas quando o Smart Money empurra o preço para testar a resistência superior.
   - *Mapeamento de Amplitude de 2H*: O Titan Engine calcula a amplitude máxima e mínima dos últimos 12 candles de 2H (janela de 24 horas):
     `range_pos_2h = (c_close - low_2h_window) / (high_2h_window - low_2h_window)`
   - *Veto Inegociável de Miolo e Fundo*: Se `range_pos_2h < 62.0%` em regime SHORT, a entrada é sumariamente VETADA (`VETO_MEIO_DE_ACUMULACAO_2H`). O sistema aguarda pacientemente o preço repicar até o terço superior da amplitude (>= 62%, região do teto em ~$65.400). Simetricamente, em regime LONG, se `range_pos_2h > 38.0%`, a compra no topo é VETADA (`VETO_TOPO_DE_ACUMULACAO_2H`).
2. **Preservação do Fôlego Estrutural do Stop Loss 2H & Calibração V226**:
   - *Evolução Canônica do Stop Loss*: No V220 original, o stop utilizava margem técnica além do topo da consolidação (`high_2h_window * 1.006`). No V226, para proteger a banca de $100.000 em 50X Margem Cruzada, essa fórmula foi substituída pelo Teto Rígido Institucional de 0.70% (`max_stop_dist = 0.0070` = max -35.0% de ROI), ancorado no topo do sweep da vela de 30M / SMA 21 com respiro de +0.25%, eliminando perdas anômalas de -$13.5k e mantendo respiro técnico sniper.
   - *Geração Instantânea de Lucro*: Ao entrar no teto (62%-75% do range), assim que o preço volta a recuar para o centro (50%) ou piso (30%), a ordem gera imediatamente +1.5% a +2.0% de preço a favor (+75% a +100% de ROI em 50X Margem Cruzada), atingindo instantaneamente os Degraus 1 e 2 de Breakeven (+45% e +60% ROI) sem passar por calor flutuante.

### 2.9 Protocolo Navio Almirante: BTC First & Simbiose Direcional 100% da Frota [V221]
1. **Precedência Obrigatória (BTC First no Slot 1)**:
   - *Fundamento de Mercado*: O Bitcoin concentra a maior fatia de liquidez e volume do mercado de derivativos. Abrir altcoins isoladas com a mesa zerada expõe o portfólio a ruído local antes que o ativo guia tome decisão.
   - *Regra*: Com 0 ordens ativas na frota, nenhuma altcoin pode abrir posição (`VETO_AGUARDANDO_NAVIO_ALMIRANTE_BTC`). Apenas o Bitcoin (`BTC-USDT-SWAP`) está habilitado a disparar a primeira ordem pioneira (Slot 1), validando o fluxo direcional macro.
2. **Simbiose Direcional Inviolável (100% no Sentido do BTC)**:
   - *Proibição de Hedges Canibais*: Ter o Bitcoin comprado (LONG) e uma altcoin vendida (SHORT) coloca o sistema em contradição direta, onde o repique do BTC arrasta o mercado e estopa a altcoin.
   - *Regra*: Uma vez que o BTC está posicionado em LONG, 100% dos slots subsequentes (Slot 2 até Slot 8) só podem abrir em **LONG**. Se o BTC estiver posicionado em SHORT, 100% dos slots subsequentes só podem abrir em **SHORT** (`VETO_DESALINHAMENTO_DIRECIONAL_BTC`).
3. **Expansão Autofinanciada em Bola de Neve (2+2+2+2)**:
   - *Risco Inicial*: Máximo de 2 ordens simultâneas sob risco desprotegido ($20.000 de margem = 20% da banca em 50X Margem Cruzada; 80% livre como colateral soberano).
   - *Destravamento da 3ª à 8ª Ordem*: O Slot 3 só é aberto quando o BTC ou a altcoin do Slot 2 atingir o Risco Zero (Breakeven Degrau 1 a +45% ou Degrau 2 a +60%), garantindo que a frota só se expanda com lucro travado no cofre.
4. **Kill Switch de Órfãs (Flush Protetivo)**:
   - Se o Bitcoin inverter de regime macro ou encerrar seu ciclo, quaisquer altcoins remanescentes na direção contrária são imediatamente encerradas a mercado ou puxadas para breakeven, eliminando perdas por descompasso.

### 2.10 Titan Macro Trend Lock & Purga Canônica da Águia Fusion [V222]
1. **Trava Macro de Tendência (Macro Trend Lock)**:
   - *Fundamento de Mercado*: Comprar repiques intradiários (15M ou 30M) quando o ativo maior (Bitcoin) está em tendência de baixa nos timeframes superiores (1H, 2H e 4H) ou acumulando abaixo da média de 2H é uma armadilha clássica de Smart Money. O repique atrai compradores de varejo para capturar liquidez e desaba em seguida.
   - *Regra Inegociável*: É TERMINANTEMENTE PROIBIDO abrir ordens em LONG (no Bitcoin ou em qualquer altcoin) quando o regime macro não for expressamente BULL (`btc_macro_dir != "BULL"` ou preço abaixo da SMA 21 de 2H). Veto automático disparado: `VETO MACRO TENDÊNCIA BAIXA`. Compras só são autorizadas se o Bitcoin romper formalmente a resistência macro do caixote de consolidação com confirmação técnica.
   - *Finalidade do Repique em Baixa*: Repiques intradiários em mercados de baixa servem exclusivamente para caçar entradas sniper de SHORT no topo do repique (Grau 2 na SMA 21 de 2H).
2. **Purga Canônica da Águia Fusion (`LAYA_AGUIA_FUSION` Extirpada)**:
   - A estratégia legado `LAYA_AGUIA_FUSION` operava cruzamentos intradiários de 15M e possuía isenções de liquidez que induziam compras de topo contra a maré macro.
   - Foi permanentemente purgada e descontinuada de todo o pipeline de abertura de ordens.
   - Autoridade soberana e exclusiva concedida à estratégia `LAYA_PULLBACK_HUNTER_2H_30M`.
3. **Consolidation Ceiling Sniper Preservado**:
   - Em caixas de acumulação de 2H, o SHORT exige teste do terço superior (`range_pos_2h >= 62.0%`). No V226, o Stop Loss estrutural é rigorosamente calibrado pela microestrutura local da rejeição com o teto rígido institucional de 0.70% (`max_stop_dist = 0.0070`), expurgando em definitivo qualquer ancoragem cega em `high_2h_window` que causava distâncias destrutivas de 2.61% (-135% ROI).

### 2.11 Unificação Soberana da Telemetria, Micro-Caching & Desativação do Titan 360 [V224]
1. **Micro-caching Inteligente na Telemetria**:
   - Implementação de cache de curta duração (1.2s TTL) em `/api/cockpit/telemetry` e cache atômico de `recent_trades` (5.0s TTL), reduzindo a latência média de resposta de 72 segundos para ~15-20 milissegundos.
2. **Deprecação da Rota `/laya` com Redirecionamento HTTP 301**:
   - A página legada Titan 360 (`/laya`) foi unificada na Telemetria Soberana (`/telemetry`), concentrando o stream cognitivo, o radar de liquidação institucional e a composição da frota 2+2+2+2.

### 2.12 Calibração de Gatilhos Titan Engine & Sinergia Farol BTC BEAR [V225]
1. **Calibração de Gatilhos Grau 1 (SMA8) e Grau 2 (SMA21)**:
   - Limiares de pavio e absorção calibrados para captura limpa de repiques autênticos em 30M sem vetos artificiais cegos de varredura.
2. **Breakdown 2H (Rompimento de Suporte Macro de 2H)**:
   - Quando o ativo perde o piso da acumulação de 2H (`price <= low_2h_window * 1.003` com regime de baixa confirmado), o SHORT é autorizado de imediato, dispensando a exigência de teste no teto da consolidação.
3. **Sinergia Direcional Altcoin sob Farol BTC BEAR**:
   - Se a frota estiver com 0 ordens ativas e o Bitcoin estiver em BEAR confirmado, altcoins dos Titãs (`score >= 85`) são autorizadas a abrir o Slot 1 alinhadas em SHORT.

### 2.13 Teto Rígido Institucional de Stop Loss 50X, Purga de high_2h_window & Desasfixia de Breakeven [V226]
1. **Diagnóstico Forense da Anomalia ETH (-$13.516,03)**:
   - *O Paradoxo do Risco Invertido*: No caso ETH, o stop loss foi calculado herdando a máxima de 24 horas (`high_2h_window * 1.006`), resultando em um stop a 2.61% de distância do preço de entrada ($1.762,83 -> $1.798,08). Sob alavancagem de 50X, 2.61% representou -130.5% de perda bruta + taxas/slippage, totalizando -$13.516,03 em um único lote de $10.000.
   - *Sufocamento de Operações Lucrativas*: Simultaneamente, as operações vencedoras (BTC, LINK, TIA, ENA) eram encerradas prematuramente pelo `SCRATCH_GUARD_REJECTION` (+30% ROI) e breakeven agressivo (+18% ROI), rendendo apenas +$380 a +$1.040. Essa assimetria gerava uma relação Risco:Retorno de 1:30 invertida.
2. **Invariantes Canônicas V226 (Escritas em Pedra)**:
   - **Teto Rígido Institucional de Stop Loss (`max_stop_dist = 0.0070`)**: Em 50X Margem Cruzada, a distância do Stop Loss em relação ao preço de entrada é estritamente limitada a no máximo 0.70% de preço. Isso trava a perda máxima absoluta por trade em -35.0% de ROI (-$3.500 no lote de $10.000).
   - **Purga Canônica de `high_2h_window` do Stop Loss**: O Stop Loss de entradas sniper é ancorado na microestrutura do repique atual de 30M / SMA 21 com respiro de apenas +0.25%, respeitando imperativamente o teto de 0.70%.
   - **Desasfixia de Breakeven para `LAYA_PULLBACK_HUNTER_2H_30M`**: Isenção permanente do `SCRATCH_GUARD_REJECTION` precoce em +30% ROI para a estratégia Pullback Hunter, permitindo que a posição respire a favor da tendência para capturar os Degraus 2 a 5 (+60% a +300% de ROI = +$6.000 a +$30.000).
   - **Relação Risco:Retorno Saudável (1:1.5 até 1:10)**: Restaurada a matemática da consistência institucional, onde ganhos de +$6k a +$30k superam com folga qualquer stop limitado a -$3.5k.

### 2.14 Painel Soberano de Governança & Escudos de Proteção da Banca [V226]
1. **Painel de Escudos de Proteção (Opção B - Cockpit)**:
   - Integrado de forma compacta e cirúrgica dentro do card `BANCA SOBERANA & GESTÃO DE RISCO` (`frontend/cockpit.html` e `backend/app/static/cockpit.html`).
   - Fornece visualização em tempo real dos 4 pilares inegociáveis de preservação patrimonial:
     - **Piso Soberano**: Trava patrimonial ativa em $140.089,35 (80% do lucro máximo realizado protegido no cofre). Em caso de drawdown de segurança, o motor impede qualquer sangramento de capital.
     - **Circuit Breaker Anti-Tilt**: Monitoramento de paradas consecutivas. Ao acusar 2 stops sucessivos, impõe congelamento direcional temporário de 45 minutos e coloca ativos estopados em quarentena de 2 horas.
     - **Consolidation Ceiling Sniper**: Em caixas de acumulação e mercado lateral de 2H, veto automático a vendas abaixo de 62% do range (`range_pos_2h < 62.0%`), impedindo sangramento de capital em miolo ou fundo de acumulação.
     - **Alocação de Risco Ativo (Frota 2+2+2+2)**: Trava rígida de no máximo 2 ordens simultâneas em risco aberto ($20.000 nocional / 20% da banca). Novos slots (3 a 8) só abrem autofinanciados com Risco Zero (+45%/+60% ROI) já consolidado nas ordens precedentes.

### 2.15 Manômetro de Amplitude Titan & Regime Macro OKX Universe [V226]
1. **Cálculo Universal de Amplitude de Mercado (`market_intel_engine.py` & `/api/market/breadth`)**:
   - Mede em tempo real o percentual de contratos perpétuos negociando acima da média móvel simples de 21 períodos no gráfico de 2 horas (`price > sma21_2h`).
   - Sincronização atômica com os 31 Titãs institucionais e o universo total de 534 derivativos da OKX (`okx_universe_service.sync_tickers()`).
   - Classificação estrita em 5 regimes de governança:
     - `BEAR_DOMINANT` (< 30% acima da SMA21): Pressão vendedora massiva. SHORTs prioritários, veto total a compras contra o fluxo.
     - `BEAR_MOMENTUM` (30% - 45%): Fraqueza generalizada. SHORTs autorizados em repiques Grau 1 e Grau 2.
     - `NEUTRAL` (45% - 55%): Equilíbrio de mercado / consolidação. Regime seletivo com exigência de teste no teto (>= 62%).
     - `BULL_MOMENTUM` (55% - 70%): Força compradora emergente. Apenas sob Farol BTC BULL.
     - `BULL_DOMINANT` (> 70%): Expansão compradora generalizada.
2. **Manômetro Visual Dinâmico no Cockpit (`TITAN ENGINE • COMANDO TÁTICO`)**:
   - Manômetro analógico semicircular em SVG com ponteiro dinâmico rotacionando de -60° (BEAR extremo) a +60° (BULL extremo).
   - Cores e estilização estritamente compatíveis com o padrão Lamborghini / Binance Dark (`#F6465D` Red, `#FCD535` Yellow, `#0ECB81` Green), sem emojis.
   - Atualizado a cada 1.000 ms pelo payload otimizado de `/api/cockpit/telemetry` com latência sub-20ms.

**Status Operacional Atual [V226-50X-SNIPER-RISK-CAP-SOVEREIGN]**:
- **Frota Ativa (Titan Engine)**: 100% sob **50X Margem Cruzada**, banca base de **$100.000,00 USD**, lote fixo de $10.000,00 ($500.000 nocional) e até 8 slots simultâneos na regra 2+2+2+2.
- **Protocolo V226**: Hard Risk Cap 50X (teto rígido de stop loss em 0.70% / max -35% ROI) + Purga Canônica de `high_2h_window` + Desasfixia de Breakeven para Pullback Hunter.
- **Protocolo V225**: Calibração de Gatilhos Titan Engine (Grau 1 e Grau 2) + Breakdown 2H + Sinergia Altcoin sob Farol BTC BEAR.
- **Protocolo V224**: Unificação da Telemetria (/telemetry) + Micro-caching 1.2s TTL + Redirecionamento HTTP 301 de /laya.
- **Protocolo V222**: Titan Macro Trend Lock (proibição de LONGs em repique de baixa) + Purga Definitiva da Águia Fusion + Exclusividade Soberana `LAYA_PULLBACK_HUNTER_2H_30M`.
- **Protocolo V221**: Navio Almirante (BTC First no Slot 1) + Simbiose Direcional 100% (altcoins estritamente no mesmo sentido do BTC) + Kill Switch de Órfãs.
- **Tática de Execução V220**: Consolidation Ceiling Sniper (entrada obrigatória no teto >= 62% da caixa 2H).
- **Tática de Liquidez V219**: Liquidity Snatch Entry (paciência para caçada aos stops retail) com stops sniper de 1.0%-1.2%.
- **Farol BTC Key Zones V219**: Monitoramento de Suportes/Resistências Macro do BTC e Veto de Vender Fundo.
- **Dual Breakeven Institucional**: Degrau 1 a +45% (trava +18%) e Degrau 2 a +60% (trava +30%), Alvo Chão de +300% ROI.
- **Protocolos de IA**: OpenViking Context Engine (`viking://`), Servidor MCP 2.x Starlette Mount (`/mcp` com 16 ferramentas), RAGService Híbrido e Pipeline de Fine-Tuning ML (`/api/v1/ml/*`).
- **Precisão OKX**: 100% dos 507 pares da OKX com quantização exata de tick size e lot size.

> **Semântica PAPER vs REAL**: Em PAPER, o Cockpit espelha a Banca Simulada Realizada do Sandbox (`get_sandbox_unified_balance`); em REAL, a OKX recebe as ordens e o Cockpit reflete o saldo real.

> Nota: `bankroll.py` le `settings.MARGIN_PER_TRADE_*` (0.50) e `settings.MAX_SLOTS_*` (16). Comentarios legados em `bankroll.py` citam "$2.00/$1.00" e "20/40" — esses valores NAO refletem o config atual.

---

## 3. Escadinha de Stops (fonte: `backend/services/order_projection_service.py` + `sandbox_service.py` + `sandbox_swing_service.py`)

Existem **6** escadas. A selecao e feita em `get_stop_ladder(roi, is_ranging, slot_type, strategy_class)`:
- `is_swing` = `slot_type` in (BLITZ_30M, SWING) **ou** `strategy_class` in (VELOCITY FLOW, ALPHA SHIELD, DECOR SHADOW, LAYA_SMART_MONEY_H1)
- `is_scalping` = `strategy_class`=="VWAP SNIPER" **ou** `slot_type`=="SCALPING"
- `is_laya_reversion` = `strategy_class`=="LAYA_MEAN_REVERSION"
- `is_smart_money_h1` = `strategy_class`=="LAYA_SMART_MONEY_H1" (Metodologia Encryptos: Acumulação H1, Rompimento com força, Confirmação LSR x OI, Stop Loss na borda de saída da consolidação).
- Roteamento: swing+ranging→`SWING_LATERAL` · swing→`SWING` · laya_reversion→`LAYA_REVERSION` · scalping→`SCALPING` · ranging→`RANGING` · senao→`TRENDING`.

### 3.1 `ORDER_STOP_LADDER_RANGING` (lateral scalping padrao)
| Gatilho ROI | Stop ROI | Nome | Status |
|---|---|---|---|
| 8% | 2% | GARANTIA_TAXAS | RISCO_ZERO |
| 12% | 5% | GARANTIA_LUCRO_CURTO | RISCO_ZERO |
| 20% | 10% | GARANTIA_LUCRO_MEDIO | RISCO_ZERO |
| 32% | 18% | GARANTIA_LUCRO_ALTO | RISCO_ZERO |
| 50% | 48% | ALVO_MAXIMO_LATERAL | PROFIT_LOCK |
Acima de 20% ROI em ranging, a escada sobe dinamicamente de 1% em 1% (trailing gap 5%, ou 10% se `slot_type=BLITZ_30M`).

### 3.2 `ORDER_STOP_LADDER_SCALPING` (VWAP SNIPER) [V146]
| Gatilho | Stop | Nome | Status |
|---|---|---|---|
| 10% | 2% | GARANTIA_TAXAS_SCALP | RISCO_ZERO |
| 18% | 8% | LUCRO_CURTO_SCALP | RISCO_ZERO |
| 30% | 18% | LUCRO_MEDIO_SCALP | PROFIT_LOCK |
| 45% | 32% | TRAILING_SCALP | PROFIT_LOCK |

### 3.3 `ORDER_STOP_LADDER_LAYA_REVERSION` (Laya Mean Reversion) [V147-WINRATE]
Calibração específica para reversões em consolidação com alavancagem 15x e Early Shield. Protege trades que andaram a favor antes do breakeven (evitando devoluções como no caso da ARB) e garante assimetria de retorno positiva:
| Gatilho ROI | Stop ROI | Nome | Status |
|---|---|---|---|
| 4.0% | -2.0% | EARLY_SHIELD_LAYA | RISCO_BAIXO (Corta 73% do risco inicial) |
| 6.0% | 1.5% | GARANTIA_TAXAS_LAYA | RISCO_ZERO |
| 12.0% | 6.0% | LUCRO_CURTO_LAYA | PROFIT_LOCK |
| 22.0% | 14.0% | LUCRO_MEDIO_LAYA | PROFIT_LOCK |
| 35.0% | 24.0% | PROFIT_LOCK_LAYA | PROFIT_LOCK |
| 50.0% | 38.0% | ALVO_MAXIMO_REVERSION | PROFIT_LOCK |

### 3.4 `ORDER_STOP_LADDER_SWING` (Swing 2H/4H 50X em Margem Cruzada) [V197]
Calibrada para conceder respiro amplo de 12h a 24h sem asfixia precoce. A ordem tem liberdade total de oscilação até +50% ROI (+1.0% de preço), onde o breakeven é acionado para blindar a banca em Risco Zero:
| Gatilho ROI | Stop ROI | Nome | Status | Descrição Operacional |
|---|---|---|---|---|
| **50.0%** | **5.0%** | **BREAKEVEN_2H** | **RISCO_ZERO** | Aciona após avanço real de ~1.0%. Blinda posição e libera vaga no Lote 2 |
| **100.0%** | **50.0%** | **PROTECAO_LUCRO_100** | **PROFIT_LOCK** | Garante lucro mínimo de +$500,00 no bolso |
| **200.0%** | **120.0%** | **LUCRO_CONSOLIDADO_200**| **PROFIT_LOCK** | Garante lucro de +$1.200,00 no bolso |
| **300.0%** | **200.0%** | **ALVO_CHAO_300** | **PROFIT_LOCK** | **Alvo Chão Obrigatório**: Garante +$2.000,00 mínimos por ordem |
| **400.0%** | **300.0%** | **SURFE_LIVRE_400** | **TRAIL_LOCK** | Trailing dinâmico que persegue a tendência macro |
| **500.0%** | **400.0%** | **ALVO_MACRO_4H_500** | **TRAIL_LOCK** | Rompimento até o grande suporte/resistência do 4H |
| **800.0%** | **650.0%** | **ALVO_EXPANSAO_800** | **TRAIL_LOCK** | Expansão máxima institucional |

### 3.4.1 Protocolo Soberano dos Lotes 4 + 4 em Margem Cruzada [V197]
- **Margem Fixa**: $1.000,00 por ordem em 50.0X (nocional $50.000,00). Lastreada pelo saldo total de $100.000,00 em Margem Cruzada (`mgn_mode="cross"`).
- **Lote 1 (Risco Ativo)**: A Laya abre no máximo 4 posições com risco vivo simultâneo (exposição máxima de $4.000,00 ou 4.0% da banca).
- **Gatilho de Desbloqueio (Lote 2)**: Os slots 5 a 8 permanecem estritamente bloqueados até que ordens do Lote 1 atinjam Breakeven (+50% ROI / Risco Zero). Conforme uma ordem zera seu risco, uma nova vaga é destravada para o Lote 2, mantendo uma esteira contínua sem nunca ultrapassar 4 ordens em risco vivo.
- **Stop Estrutural Livre (2H/4H)**: O Stop Loss é ancorado nos topos/fundos reais do 2H/4H em até 3.8% de distância de preço, sem tetos artificiais de scalping que causem violinadas.
- **Alvo Chão de +300%**: Toda ordem vencedora busca no mínimo +300% de ROI (+$3.000,00 brutos), estendendo o ganho até os suportes/resistências do 4H via trailing stop de 2H.

### 3.5 `ORDER_STOP_LADDER_SWING_LATERAL` (swing em lateral)
| Gatilho | Stop | Nome |
|---|---|---|
| 5% | 1.5% | BREAKEVEN_LATERAL |
| 15% | 5% | PRE_UNIT1_LATERAL |
| 30% | 15% | UNIT1_GARANTIDO |
| 60% | 30% | EMANCIPADO_LATERAL |
| 100% | 80% | TRAILING_LATERAL |

### 3.6 `ORDER_STOP_LADDER_TRENDING` (tendencia)
14/2, 25/10, 40/20, 60/40, 80/60, 100/80, 130/110, 150/110, 200/150, 300/220, 400/280, 500/350, 600/420, 700/500, 750/600, 800/650, 1000/800, 1200/1000.
Acima de 1200% ROI (APEX): niveis `ULTRA_*` a cada +200% ROI, stop = gatilho − 200%.

`ORDER_STOP_LADDER` (sem sufixo) e um alias de `TRENDING` para compatibilidade com o compliance do Hermes.

### 3.7 `ORDER_STOP_LADDER_IGNITION` (Super-Runners & Ignição Altcoin) [V181]
Escadinha exclusiva para estratégias de ignição e expansão institucional (`ALT_PUMP_IGNITION`, `LAYA_LIQUIDITY_HUNT`, `LAYA_SWEEP_AND_FLIP`).
Evita o sufocamento precoce por ruído de microestrutura 5M, conferindo fôlego para o ativo surfar tendências explosivas:
| Gatilho ROI | Stop ROI | Nome | Status |
|---|---|---|---|
| 16.0% | +3.5% | GARANTIA_TAXAS_IGNITION | RISCO_ZERO (Cobre taxas e dá folga) |
| 30.0% | +18.0% | LUCRO_CONFIRMADO | PROFIT_LOCK (+US$ 18 garantidos) |
| 50.0% | +35.0% | EXPANSAO_ALVO | PROFIT_LOCK (+US$ 35 garantidos) |
| 80.0% | +60.0% | SUPER_PUMP_80 | PROFIT_LOCK (+US$ 60 garantidos) |
| 120.0% | +95.0% | SUPER_PUMP_120 | PROFIT_LOCK (+US$ 95 garantidos) |
| 200.0% | +160.0% | PUMP_LENDARIO_200 | PROFIT_LOCK |
| 350.0% | +280.0% | MOON_RUNNER_350 | TRAIL_LOCK |
| 500.0% | +420.0% | SUPERNOVA_500 | TRAIL_LOCK |
| 1000.0% | +850.0% | GOD_MODE_1000 | TRAIL_LOCK |

### 3.8 Time-Stop Preventivo Anti-Sangria (45 Minutos) [V181]
- Se um trade de ignição não demonstrar força e permanecer estagnado por mais de **45 minutos (2700s)** com `ROI <= -8.0%` e pico inferior a `+6.0%`:
  - O motor encerra preventivamente a mercado com status `CLOSED_TIME_STOP`.
  - Estanca as perdas em cerca de **-US$ 8 a -US$ 10**, impedindo que a posição sangre passivamente até o stop cheio de -21%.

### 3.9 Protocolo Sweep & Flip e Colheita no Topo [V182]
Mecanismo de captura dupla de liquidez em ciclos de exaustão institucional de Smart Money:
1. **Identificação de Sweep**: Quando uma ordem ativa em LONG atinge expansão (`max_roi >= 18%` ou `pnl >= 15%`) e o micro-timeframe 5M imprime pavio superior pronunciado ($\ge 35\%$) com vela fechando para baixo (`cl <= o`), confirmando rejeição de topo.
2. **Confirmação do Ímã**: O Heatmap de Liquidação da OKX/Coinglass confirma muralha de liquidez institucional dominante posicionada **ABAIXO** do preço.
3. **Colheita de Lucro (`CLOSED_SWEEP_HARVEST`)**: A posição de LONG é encerrada a mercado no pico, travando os lucros máximos de topo.
4. **Virada de Mão (`LAYA_SWEEP_AND_FLIP`)**: A Laya abre imediatamente um SHORT no mesmo par:
   - **Stop Loss Cirúrgico**: Posicionado 1 tick acima da máxima do pavio do sweep (~0.8% a 1.2% de distância).
   - **Take Profit**: Projetado no bolsão de liquidação dominante inferior.
   - **Relação R:R**: $\ge 3:1$ a $4:1$.

### 3.7 Proteções Adicionais (Scalping/Swing/Laya Sandbox)

**GARANTIA_4 / GARANTIA_6 — Risco Zero Imediato [V133 / V135-RR / V136-SWING / V145]** (`sandbox_service.py:1571-1583`):
Quando `max_roi >= threshold` e `current_stop_roi < 0%`, stop vai a 0% ROI (break-even).
- **Laya Mean Reversion [V145]**: threshold = **+6.0% ROI** → stop sobe imediatamente para **+1.5% ROI** (lucro mínimo garantido contra reversões).
- **Scalping Geral**: threshold = **+4%** (V135-RR).
- **Swing**: threshold = **+12%** (V136-SWING). Breakeven mais alto para dar fôlego ao trade de médio prazo.

**GARANTIA_TRAIL — Trailing Dinâmico [V122 / V131-FIX / V133 / V135-RR / V136-SWING / V145]** (`sandbox_service.py:1588-1645`):
**[V145]** Split por tipo de trade:
- **Laya Mean Reversion**: `max_roi >= 6.0%` → stop = `max(1.5, max_roi × 0.50)` (**50%** do pico, mínimo +1.5%).
- **Swing**: `max_roi >= 12%` → stop = `max(3.0, max_roi × 0.50)` (**50%** do pico, mínimo +3%). Trades duram mais sem dar lucro embora.
- **Scalping Geral**: `max_roi >= 4%` → stop = `max(1.5, max_roi × 0.75)` (**75%** do pico, mínimo +1.5%).
- **Stop Inicial Máximo [V145]**: Capado rigidamente em **-7.5% ROI** (0.50% de variação no preço com 15x de alavancagem), assegurando assimetria R:R $\ge$ 4:1 com alvos de +30% a +36%.
- **Scalping**: `max_roi >= 4%` → stop = `max(1.5, max_roi × 0.75)` (**75%** do pico, mínimo +1.5%). Inalterado.
**[V135-RR]** Apertado de 60% para 75% do pico (Scalping) — avg give-back era 4.0pp.
**[V131-FIX]** Correção de bug crítico: a condição `current_stop_roi < 0.0` impedia o trailing de avançar após a GARANTIA_8 mover o stop para 0%. Removida a condição.
**[V133]** Breakeven de ativação igualado para 8% em ambos modos — antes 12% no Scalping, 8% no Swing. **[V135-RR]** Reduzido para 4% (Scalping). **[V136-SWING]** Swing elevado para 12%.

### 3.7 Equity Defense — Defesa Progressiva de Patrimônio [V128]

Sistema de proteção do saldo consolidado da banca Sandbox. Rastreia o pico da equity e protege
80% do lucro acumulado com stops progressivos por nível.

**Config** (`config.py:193-203`):
- `EQUITY_DEFENSE_LOCK_RATIO = 0.80` — 80% do lucro do pico é protegido
- `EQUITY_DEFENSE_STOP_L1 = 7.0%` — L1 LEVE: stop = pico - 7%
- `EQUITY_DEFENSE_STOP_L2 = 5.0%` — L2 MODERADO: stop = pico - 5%
- `EQUITY_DEFENSE_STOP_L3 = 3.0%` — L3 FORTE: stop = pico - 3%
- `EQUITY_DEFENSE_MIN_ROI = 5.0%` — ROI mínimo do trade para defesa aplicar (evita fechar trades com ROI baixo)

**Níveis de defesa** (`sandbox_service.py:1333-1368`):

| Banca (profit %) | Nível | Ação |
|---|---|---|
| < +3% | 0 OFF | Stop segue escadinha normal |
| +3% a +4.9% | 1 LEVE | Stop = pico - 7% |
| +5% a +9.9% | 2 MODERADO | Stop = pico - 5% |
| >= +10% | 3 FORTE | Stop = pico - 3% |
| abaixo do piso | 4 CRITICO | Fecha todos os trades |

**Piso protegido** (`database_service.py:296-301`):
```
peak = maior saldo já visto
peak_profit = peak - base ($10.000)
floor = base + (peak_profit × 0.80)

Exemplo: peak $10.900 → floor = $10.000 + ($900 × 0.80) = $10.720
```

**Enforcement** (`sandbox_service.py:1497-1527`, `flash_agent.py:507-547`):
- L1/L2/L3: sobe stop para `peak_roi - stop_pct` (só se > stop atual E max_roi >= 5%)
- CRITICO: fecha trade imediatamente com status `CLOSED_EQUITY_DEFENSE`
- Threshold: defesa só aplica quando ROI máximo do trade >= 5% (evita fechar trades marginais)
- Regra "só sobe": defense_stop só aplica se > stop atual da escadinha

**UI** (`sandbox.html`):
- Badge `[DEFESA]` ao lado de `[LOCK-IN]` no card de Banca
- Cores: L1=azul, L2=amarelo, L3=laranja, CRITICO=vermelho+pulse
- Trade rows: indicador `EQUITY_L1/L2/L3/CRITICO`
- Tooltip: Pico | Piso | Banca | Stop%

### 3.8 Stops Iniciais

**Scalping Lab — VWAP SNIPER [V127.2 / V132 / V133]** (`sandbox_scalping_engine.py:47`):
- `_MAX_STOP_ROI = -12.0%` (0.24% preço com 50x). **[V133]** Aumentado de -8% para -12% para dar mais runway ao trade.
- **[V133]** **Filtro de R:R Mínimo**: trades com `projected_rr < 1.5` são rejeitados (target = 3x risk, mínimo 15% ROI).
- GARANTIA_4 ativa em +4% ROI → stop vai a 0%. **[V135-RR]** Antecipado de 8% para 4%.

**Scalping Lab — Stop Adaptativo [V123 / V135-RR]** (`sandbox_service.py:321-400`):
- Tenta stop estrutural 30M (swing low/high + buffer) — aprovado se ROI entre **-12% e -6%** (mais apertado = melhor R:R). **[V135-RR]** Antes aceitava -40% a -25%.
- Fallback: **-12% ROI** (0.24% preço com 50x). **[V135-RR]** Antes -25% (0.5% preço) — era a causa do avg loss -19.4% vs avg win +7.2%.
- Teto rígido: **-12% ROI** (0.24% preço). **[V135-RR]** Antes -30%.
- Fallback ATR (ranging): clamp entre **-8% e -12%**. **[V135-RR]** Antes -12% a -15%.

**Swing Lab — Stop Configurável e Micro-Gatilho [V133]** (`sandbox_swing_service.py`):
- Alavancagem padrão de 50x com stop inicial rígido de **-20% ROI** (equivalente a 0.4% no preço). **[V133]** Reduzido de -35% para -20% para melhorar R:R (1:2+ vs 1:0.28).
- **[V133]** Threshold ADX elevado de 25 para 30 — exige confirmação de tendência mais forte antes de abrir trade.
- Análise baseada inteiramente no timeframe de **2H (120m)** com scan a cada 30 minutos (1800s).
- **Filtro de Entrada de Alta Precisão (15m):** Os sinais de 2H só iniciam o trade se o Stochastic RSI no gráfico de 15m estiver alinhado com a direção do trade.
- Zero-Risk Stacking regulado para no máximo 2 posições sob risco de mesa simultâneas.

**Execution Protocol — Breakeven Adaptativo [BLITZ]** (`execution_protocol.py:430-494`):
- DNA do ativo via Librarian: wick_multiplier e is_retest_heavy.
- Ativo limpo: breakeven em +30% ROI.
- Ativo instável: breakeven em +50% ROI.
- Pavio extremo/retest: breakeven em +60% ROI.

---

## 4. Fluxo de Execucao

```
Sinal (SignalGenerator / DECOR_HUNTER / Swing Lab / Scalping Lab)
    v
CaptainAgent (captain.py) — Quality gate + regime gating + consenso de frota
    | Consenso: Macro 15% + Whale 25% + SMC 30% + OnChain 30% + Kronos 18%
    | Quartermaster classifica o wick -> leverage
    v
BankrollGuardian (bankroll_guardian.py) — autorizacao
    | Regime gating por ADX + limites de slots + memoria por par
    v
Bankroll (bankroll.py) — execucao
    | Stop inicial adaptativo (teto 30% ROI) + ExecutionCapacityGate + OKXCommandQueue (anti-429)
    v
FlashAgent (flash_agent.py) — gestao de stops, ciclo 1s (escadinha)
    v
FleetAudit (fleet_audit.py) — reconciliacao 20s, Early ROI Panic, ghost cleanup
```

---

## 5. Filtro de Regime de Mercado (OracleAgent)

- Grade ADX: `< 25` = LATERAL (RANGING); `>= 25` = TENDENCIA (TRENDING). Estabilizacao 150s.
- DECOR SHADOW opera **apenas em LATERAL** (estrategia de reversao/exaustao).
- ALPHA SHIELD e VELOCITY FLOW operam em qualquer regime.
- BLITZ / Swing 30M (`slot_type=BLITZ_30M` ou `is_blitz=True`) faz bypass do gating em LATERAL (`captain.py`).
- Direcao BTC: confluencia var 15m + 1h. Trend bias: BTC vs SMA 200 diaria (bearish→so SHORT; bullish→so LONG).

---

## 6. Estrategias

| Estrategia | Regime | Descricao |
|---|---|---|
| VELOCITY FLOW | Qualquer / BLITZ | Momentum, SMA8/21 alinhado + volume |
| ALPHA SHIELD | Qualquer / BLITZ | Protecao de capital: DVAP/MOLA/FAS/LRT |
| DECOR SHADOW | LATERAL / BLITZ | Reversao de exaustao, decorrelacao BTC (Pearson) |
| DECOR_HUNTER | LATERAL | Caca a pares desgrudados do BTC (watchlist propria) |
| VWAP SNIPER | Scalping (M1/M5) | EMA200 M5 + toque no VWAP diario + Stoch RSI |
| LRT / DVAP / FAS / MOLA | Qualquer | Liquidez / exaustao / funding squeeze / breakout |

Swing 2H usa `SignalGenerator.analyze_m30_swing()` (reusa DVAP/MOLA/FAS/LRT + TREND + DECOR em timeframe de 120m). O antigo `blitz_sniper.py` foi **removido** (V125.3).

---

## 7. Stack de Agentes / Servicos (`backend/services/agents/` + `backend/services/`)

### 7.1 Ecossistema Soberano Atual (V177)
- **LayaRouterService** (`backend/app/services/laya_router_service.py`) — Motor Soberano unificado de varredura (507 pares), confluencia de Liquidity Zones / Volume Spike / DVWAP e execucao autonoma continua.
- **KronosScorer** (`backend/services/kronos_scorer.py`) — Scoring de conviccao temporal IA.
- **Flash Agent / SandboxService** (`backend/services/sandbox_service.py`) — Trailing stops em 5 escadinhas progressivas ("Never Give Back") e gerenciamento de posicoes ativas.
- **OpenVikingContextService** (`backend/app/services/openviking_context_service.py`) — Memoria episodica e tracking de licoes de mercado.
- **HermesAgent** (`backend/services/agents/hermes_agent.py`) — Compliance, telemetria, RAG semantico e supervisao MCP 2.x.
- **Plutus / DatabaseService** (`backend/services/database_service.py`) — Camada unica de persistencia relacional SQLite/Postgres.
- **AIService** (`backend/services/agents/ai_service.py`) — Wrapper de inferencia LLM (Gemini, DeepSeek, OpenAI).

### 7.2 Agentes Legados Descomissionados (V177 Purge)
Em conformidade com a simplificacao arquitetural V177, 18 agentes legados foram removidos do disco e seus loops desativados:
- `captain.py`, `fleet_audit.py`, `bankroll_guardian.py`, `ambush.py`, `execution_auditor.py`, `flash_agent.py`, `jarvis_brain.py`, `librarian.py`, `librarian_auditor.py`, `macro_analyst.py`, `market_data.py`, `onchain_whale_watcher.py`, `oracle_agent.py`, `quartermaster.py`, `sentiment_specialist.py`, `slot_operator.py`, `trade_analyst.py`, `whale_tracker.py`.
- Todas as rotas FastAPI (`market.py`, `chat.py`, `system.py`, `admin.py`, `sandbox.py`, `backtest_routes.py`) foram desacopladas para rotear exclusivamente pela Laya Soberana e Hermes.

Iniciados no startup (`backend/main.py`): okx_ws_public_service, telegram_service, hermes_agent, laya_autonomous_loop, slots_broadcast_loop, sentinel_auditor, sandbox_service, sandbox_swing_service.

---

## 8. Laboratorios de Forward-Testing

### 8.1 SandboxService (`services/sandbox_service.py`) — ciclo 1s **[V131-FIX]**
- Espelha o sistema real. Recebe sinais via `on_radar_pulse` → `_process_radar_signals`.
- Stop adaptativo por regime (fallback): LATERAL -8% ROI / TRENDING -10% ROI; capping -10%.
- Margem adaptativa por win rate do par: $1.00–$2.50 (`_get_adaptive_margin`).
- Cooldown pos stop-out **por (simbolo, direcao)**: **1800s** no 1o stop, **3600s** em stops consecutivos (>=2) — `sandbox_service.py:735`.
- Cooldown de transicao fria (tendencia→lateral): **900s** (`:551`).
- Confirmacao 5M (2/3 candles alinhados), Entry Sanity Check (70% do stop), auto-blocklist (PnL<-15% E WR<35% apos 3+ trades).
- Espelhamento real (V124.4): se `OKX_API_KEY_MASTER` + modo REAL, replica ordens; auditado pelo ExecutionAuditorAgent.
- **[V131-FIX] Limite de slots corrigido de 10 para 5** (`sandbox_service.py:709`): o limite do Radar estava em `>= 10` enquanto o VWAP SNIPER usa `_MAX_SLOTS=5`. Agora consistentes.
- **[V131-FIX] Anti-hedge via Radar** (`sandbox_service.py:751`): bloqueado trade em direção oposta se o par já tem trade ativo. Evita LONG+SHORT simultâneos no mesmo par.
- **[V131-FIX] GARANTIA_TRAIL desbloqueado** (`sandbox_service.py:1571`): removida condição `current_stop_roi < 0.0` que travava o trailing em 0% após GARANTIA_8 ativar.
- **[V131-FIX] `AttributeError: self.dynamic_margin` corrigido** (`sandbox_service.py:1546`): atributo inexistente substituído por leitura dinâmica de `trade.contract_meta["margin"]` com fallback $200.

### 8.2 Scalping Lab — VWAP SNIPER (`services/sandbox_scalping_engine.py`) **[V133]**
- Scan 30s. Filtro tendência EMA200 (M5); toque no VWAP diário (M1, tol 0.30%).
- **[V132-REFINADO] Gatilhos e confluência:**
    *   **BTC Trend Bias (15m):** Bloqueia LONGs se variação de 15m do BTC for < -0.40% e SHORTs se for > 0.40% (evita entrar contra fluxo).
    *   **Stochastic RSI (1m):** Exige cruzamento real de linhas: %K cruza acima de %D (LONG, k<35) ou cruzamento abaixo (SHORT, k>80).
    *   **Volume Relativo de 5m:** Rejeita novas entradas se o volume de 5m estiver < 1.1x acima da média simples de 20 períodos (evita mercados estagnados).
- **[V133] Filtro de R:R Mínimo:** Trades com `projected_rr < 1.5` são rejeitados. Target = 3x risk (mínimo 15% ROI). Garante que cada trade tenha potencial de lucro significativamente maior que o risco.
- **Leverage/Stops:** 50x isolada, margem dinâmica baseada em score (30%, 60% ou 100% da margem base de 2% da banca consolidada), stop inicial em **-12% ROI** (aumentado de -8% para dar mais runway).

### 8.3 Swing Lab — 2H (`services/sandbox_swing_service.py`) **[V133]**
- Scan a cada 30min no timeframe de **2H (120m)** via `SignalGenerator.analyze_m30_swing()`.
- Banca consolidada dinâmica (Juros Compostos), margem inicial $200/trade (2% da banca total recalculado dinamicamente), 50x.
- **[V133] Stop inicial -20% ROI** (`SWING_STOP_ROI=20.0`): `stop_price = entry × (1 - 0.20/50) = entry × 0.996` (0.4% de oscilacao do preco). Reduzido de -35% para -20% para melhorar R:R.
- **[V133] ADX Threshold elevado de 25 para 30:** Exige confirmação de tendência mais forte antes de abrir trade, filtrando sinais em mercados laterais ou fracos.
- **Filtro de Entrada de Alta Precisão (15m):** Setup de 2H só entra se o Stochastic RSI no gráfico de 15m confirmar a direção do momentum (LONG `k_15m > d_15m`, SHORT `k_15m < d_15m`).
- **Zero-Risk Stacking (cap 2):** Permite no máximo 2 posições sob risco de mesa ao mesmo tempo. Novas entradas exigem que pelo menos uma das ordens ativas já tenha atingido o break-even (risco zero).

### 8.4 Constantes de banca do Sandbox UI (`routes/sandbox.py`)
`BANCA_BASE`=$10.000 (:20) · `MARGEM_SCALP`=dinâmica (2% da banca total) · `MARGEM_SWING`=dinâmica (2% da banca total) · alocacao maxima = 40% da banca consolidada total.

### 8.5 Protocolo Lock-In (Proteção de Banca — V126)
- **Objetivo**: Proteger o capital simulado acumulado quando a banca atinge a meta mínima de crescimento.
- **Ativação**: Ocorre automaticamente quando o saldo consolidado (banca + PnL aberto de Scalp e Swing) grows 10% (gatilho configurado em `SANDBOX_LOCK_IN_TRIGGER_PERCENT` padrão 10.0%, ou seja, >= $11.000).
- **Ação**: O stop loss das ordens ativas passa a ser recalculado de forma colada a 5% de recuo da margem de entrada por trade (`SANDBOX_LOCK_IN_STOP_PERCENT` padrão 5.0%), equivalente a 5.0% de ROI ou 0.10% de oscilação do preço do ativo a partir do pico.
- **Identificação**: O stop é marcado no banco e na UI como `LOCK-IN_5%` na fase de `DEFESA`.
- **Desativação**: O protocolo só é inativado caso a banca consolidada recue abaixo do saldo inicial de $10.000.

### 8.6 Espelho PAPER → Cockpit (V127 / V127.1 / V129)

Em modo `PAPER`, o Cockpit (`cockpit.html`) espelha o Sandbox integralmente, para que o operador veja a carteira simulada como se fosse a real:

- **Net Worth (Banca)**: vem da **Banca Simulada Realizada do Sandbox** calculada por `DatabaseService.get_sandbox_unified_balance()` (`services/database_service.py`): `10000 + Σ(pnl_pct/100 × margin_at_opening)` sobre **APENAS trades FECHADOS** (status `CLOSED_SL`, `CLOSED_TRAILING` ou `EMANCIPATED`) de Scalping Lab e Swing Lab. O PnL nao realizado dos trades ativos e calculado separadamente pelo `bankroll_guardian._live_bankroll_snapshot()`.
  - **[V127.1] Fix de dupla contagem**: Anteriormente (V127), `get_sandbox_unified_balance()` somava TODOS os trades (fechados + ativos), causando inflacao artificial do equity quando combinado com o `realized_pnl` do Guardian. Agora, o saldo realizado do Sandbox ja e o `base_balance` do Guardian, e o PnL dos slots ativos e adicionado apenas uma vez via `_live_bankroll_snapshot()`.
  - Consumido por: `bankroll.update_banca_status` (`saldo_total`/`configured_balance`/`paper_equity` = saldo realizado do Sandbox; `saldo_real_okx` forçado a `0.0` em PAPER), `system.get_banca_data` (PAPER), e `bankroll_guardian.evaluate_bank_health` (PAPER, que define o `equity` exibido como Net Worth).
- **Painel de Custodia (Ordens)**: `GET /api/slots` (`routes/trading.py`) e o broadcast WS `live_slots` (`main.py:slots_broadcast_loop`, a cada 5s) mesclam em PAPER as ordens ativas do Sandbox como slots:
  - Scalping Lab → `slot_type="SCALPING"`; Swing Lab → `slot_type="SWING"`.
  - Mapeamento via `_map_sandbox_trade_to_slot` (direction→side; entry_price/stop_loss/target → entry_price/current_stop/target_price; margin $200; leverage do settings).
  - O PnL ao vivo de cada ordem e recalculado no `GET /api/slots` via `build_projection` (preco real da OKX); o WS mantem symbol/entry entre os polls.
- **Net Worth no frontend**: `liveEquity` (`cockpit.html:6442-6449`) usa `guardianEquity` quando `guardianReport.equity > 0` — por isso o `equity` do Guardiao (saldo realizado + PnL slots ativos em PAPER) e a fonte do Net Worth, e nao o `saldo_total` cru.

> **Caveat conhecido**: o header "Slots X/20" / `available_slots_count` ainda reflete os slots reais (0 em PAPER), nao o count do Sandbox. Apenas o Painel de Custodia (posicoes) e o Net Worth sao espelhados.
> **Nota V127.1**: o endpoint `/api/sandbox/unified-state` continua retornando o saldo consolidado com todos os trades (fechados + ativos) para fins de monitoramento no sandbox.html. Apenas o cálculo do Guardian (que alimenta o Cockpit) usa apenas trades fechados.

---

## 9. Watchlists (fonte: `backend/config.py`)

- **ELITE_40_MATRIX** (`:194`) — **35** pares elegiveis 50x OKX.
- **RADAR_WATCHLIST** (`:212`) — **26** pares (V126 removeu SAND, BCH, SOL, STX, EGLD).
- **DECOR_WATCHLIST** (`:233`) — **89** pares para o DECOR_HUNTER.
- **ASSET_BLOCKLIST** (`:266`) — set com ~58 simbolos bloqueados (inclui BTC/ETH como monitor-only, memecoins, stablecoins, metais, e pares de performance negativa no sandbox: AAVE, CRV, SUI, TRX, TIA, LINK, AVAX, SOL, JUP, ONDO, INJ, XLM, GRT, etc.). **[V133]** Adicionados INJUSDT, XLMUSDT, GRTUSDT.

---

## 10. Endpoints da API (routers registrados em `backend/main.py:821-834`)

| Prefixo | Router | Endpoints principais |
|---|---|---|
| `/api/auth` | `auth.py` | `/login`, `/register`, `/refresh`, `/logout`, `/me`, `/change-password`, `/users`, `/users/{id}/role`, `/users/{id}/approve`, `/users/{id}/block` |
| `/api/admin` | `admin.py` | `/users`, `/stats`, `/user/{username}/status`, `/lockdown`, `/reset-system` |
| `/api/sandbox` | `sandbox.py` | `/unified-state` (Banca Simulada Consolidada — fonte do espelho PAPER), `/trades`, `/stats`, `/patterns`, `/analytics`, `/clear`, `/swing/trades`, `/swing/stats`, `/swing/patterns`, `/swing/analytics`, `/swing/clear`, `/swing/mirror-status`, `/swing/mirror-toggle` |
| `/api/vault` | `vault.py` | `/save`, `/status` |
| `/api/sentinel` | `sentinel.py` | Auditoria de execucao |
| `/api/v1/market` | `market_intel.py` | `/screener-matrix` (Matriz 30 Titãs com 1C-EXP e 1C-RANGE), `/ai-context` (Exportação Semântica para IA) |
| `/api/memory` | `memory_routes.py` | Memory Galaxy |
| `/api/account` | `tokens.py` | Credenciais OKX por usuario |
| `/api` | `market.py` | `/elite-pairs`, `/btc/regime`, `/radar/pulse`, `/radar/grid`, `/radar/librarian`, `/radar/regimes`, `/captain/tocaias`, `/trend/{symbol}`, `/market/klines`, `/system/state`, `/market/study` |
| `/api` | `trading.py` | `/slots` (em PAPER mescla ordens ativas do Sandbox: Scalp→SCALPING, Swing→SWING — Secao 8.6) |
| `/api` | `chat.py` | `/hermes/chat`, `/hermes/compliance`, `/hermes/status`, `/hermes/sessions` (GET/POST), `/hermes/sessions/{id}` (GET/DELETE/PATCH), `/chat`, `/chat/manual`, `/chat/reset`, `/chat/status`, `/tts`, `/tts/voices`, `/logs` |
| `/api` | `system.py` | `/test`, `/debug/test`, `/health` |
| — | `dashboard.py`, `aios.py`, `backtest_routes.py` | SPA / AIOS / backtest |

---

## 11. Camadas de Dados

| Banco | Funcao | Tabelas principais |
|---|---|---|
| PostgreSQL | SSOT persistente | `slots`, `radar_pulse`, `banca_status`, `sandbox_trades`, `moonbags`, `chat_sessions`, `chat_messages` |
| Firebase Firestore | Multi-tenant, sync nuvem | `users`, `trade_history`, `trade_analytics`, `fleet_intelligence`, `vault_history` |
| Firebase RTDB | Estado em tempo real | `system_state`, `active_slots`, `radar_pulse`, `chat_status`, `banca` |
| SQLite | Cache de klines (librarian) | `klines` |

---

## 12. Memory Galaxy & Hermes Chat

- **Memory Galaxy** (`services/galaxy_memory_service.py`): cofre Obsidian em `vault_galaxy/` com subpastas `trades/`, `journal/`, `strategies/`. Gravacao disparada em `database_service.save_trade_history_item`, transicoes de regime (`oracle_agent`) e chats do Hermes.
- **Hermes Chat** (`frontend/hermes-chat.html`, rota `/hermes`): cascade NVIDIA → DeepSeek → AIService (Gemini/OpenRouter). Persiste em Postgres (`chat_sessions`, `chat_messages`).
- **Contexto do Hermes**: le este `MASTER_ARCHITECTURE.md` (primeiros 8000 chars, cache 10min) + busca por keyword em `vault_galaxy/{journal,trades,strategies}/*.md` + intel wiki + compliance + dimensoes do JarvisBrain.

---

## 13. Deploy

| Componente | Valor |
|---|---|
| Plataforma | Railway + Docker |
| Python | 3.12-slim |
| PORT | 8085 |
| Entry (todos) | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 1` |
| Health Check | `GET /api/health` |
| VERSION / DEPLOYMENT_ID | `V218-TITAN-DUAL-BREAKEVEN-45-60-SOVEREIGN` / `V218_TITAN_SOVEREIGN_SYSTEM` (`backend/main.py:83-84`) |

---

## 14. Observacoes Tecnicas Conhecidas

1. Multiplas versoes coexistem nos cabecalhos (V20.5 captain, V110.x services, V124–V126 features). O DEPLOYMENT_ID oficial e `V124.7`.
2. **[V134-CLEANUP]** Referencias Bybit removidas de 26 arquivos. `from pybit.unified_trading import HTTP` removido. `okx_rest.py` agora usa `okx_service` nativo em vez de sessao pybit. `pybit==5.8.0` removido do `requirements.txt`.
3. `get_slot_type()` em `bankroll.py` retorna sempre "DVAP" (V110.950) — diferenciacao de tipo de slot e vestigial.
4. `radar_pulse` nao e arquivo: e estrutura de dados em `database_service`, `firebase_service` e `websocket_service`.
5. Comentarios legados em `bankroll.py` ($2/$1, 20/40) divergem do `config.py` atual (0.50, 16/16) — o `config.py` prevalece.
6. **[V127] Espelho PAPER Sandbox→Cockpit** (refinamento sobre o V124.7): em PAPER o *Net Worth* e o *Painel de Custodia* do Cockpit representam o Sandbox (Banca Simulada Consolidada via `get_sandbox_unified_balance` + ordens ativas Scalp/Swing como slots). `saldo_real_okx` e forçado a `0.0` em PAPER em `update_banca_status`. `OKX_SIMULATED_BALANCE` deixa de ser o saldo exibido em PAPER (subsituido pelo saldo do Sandbox), mas segue como base de sizing/guardian. Ver Secao 8.6.
7. **[V127] Swing Stop refinado**: stop inicial configuravel via `SWING_STOP_ROI` (padrao 5.0 = -5% ROI = 0.1% preco). Escadinha BREAKEVEN em +10% ROI (antes +30%). Confirmação de entry: candle 5m fecha na direcao + volume ≥ 1.5x media. Trade INJUSDT +15.7% (+$31.40) e DOTUSDT -5.3% (-$10.68) validaram o sistema (R:R 1:2.94).
8. **[V128] Swing Lab otimizado por simulacao**: STOP=10% (0.2% preco), BE=+2% (protecao rapida), regime filter (bearish→SHORT, bullish→LONG), hour filter (pausa 14-15 UTC), blacklist dinamica (auto-bloqueio apos 3+ trades com WR<20%). Simulacao mostrou que SHORTs tem 50% WR vs LONGs 10%.
9. **[V127.1] Fix de dupla contagem de PnL**: Corrigido bug onde o equity do Guardian era inflado por somar o PnL realizado duas vezes (via `get_sandbox_unified_balance` que incluia TODOS os trades + `realized_pnl` do Firebase). Agora, `get_sandbox_unified_balance()` filtra APENAS trades fechados (`CLOSED_SL`, `CLOSED_TRAILING`, `EMANCIPATED`), e `_live_bankroll_snapshot()` em PAPER NAO soma `realized_pnl` novamente. Correções em: `database_service.py:1195-1223`, `bankroll_guardian.py:342-371`. Ver Secao 8.6.
10. **[V128→V127.2] Swing Stop restaurado para 5% ROI (0.1% preço)**: `SWING_STOP_ROI=5.0` (config.py:181). O V128 aumentou para 25% ROI (0.5% preço), causando 100% de trades Swing em stop (-25% cada). Restaurado para 5% (0.1% preço) para dar fôlego ao trade. Breakeven restaurado de +4% para +10% ROI.
11. **[V127.2] Scalping Stop restaurado para -8% ROI (0.16% preço)**: `_MAX_STOP_ROI=-8.0` (sandbox_scalping_engine.py:47). O V128 aumentou para -15% (0.3% preço), causando R:R 1:3 e expectancy negativa (-2.08% por trade). Restaurado para -8% (0.16% preço) para R:R ~1:1.
12. **[V127.2] GARANTIA_8 (antes GARANTIA_5)**: Threshold de proteção subiu de +5% para +8% ROI. Stop vai a 0% quando trade atinge +8% ROI. Evita violinada em lucros marginais.
13. **[V122] GARANTIA_TRAIL: trailing 60% do pico**: Quando max_roi >= 8% e stop < 0%, stop = max(1.5, max_roi × 0.60). Trade com pico +21% tem stop em +12.6% (não +1.5% fixo). Protege lucro sem travar cedo demais.
14. **[V128] Breakeven adaptativo BLITZ**: Execution Protocol usa DNA do ativo (Librarian) para definir breakeven: ativo limpo +30% ROI, instável +50%, pavio extremo +60%.
15. **[V128] Equity Defense — Defesa Progressiva de Patrimônio**: Protege o saldo consolidado da banca Sandbox. Rastreia o pico (`equity_peak`) e calcula um piso protegido = base + (peak_profit × 0.80). Níveis: OFF (<3%), L1 LEVE (+3%, stop=pico-7%), L2 MODERADO (+5%, stop=pico-5%), L3 FORTE (+10%, stop=pico-3%), CRITICO (abaixo do piso, fecha tudo). Enforcement em `sandbox_service.py:1497-1527` e `flash_agent.py:507-547`. Telemetria em `GET /api/sandbox/unified-state`. Badge UI no sandbox.html.
16. **[V129] Correção do Filtro de Regime e Filtro de Gás/Volume em LATERAL**: Corrigido bug que bloqueava ordens SHORT no regime LATERAL (usava `not is_bearish` incorretamente bloqueando o SHORT). Adicionada exigência de "gás" para o regime LATERAL: novos trades Swing exigem score >= 80 e volume_ratio >= 1.5x para garantir rompimentos fortes com momentum.
18. **[V131] Correções críticas de bugs identificados via diagnóstico do PostgreSQL Railway** (2026-07-18, banca em $9.537 = -4.63%):
    - **Leverage/Stop inconsistentes**: `_LEVERAGE` estava em 10x (V130) mas `sandbox_service.py` monitora com 50x real. Restaurado: `_LEVERAGE=50.0`, `_MAX_STOP_ROI=-8.0` (0.16% de preço).
    - **Hedge LONG+SHORT no mesmo par**: Detecção anti-duplicata em `_try_open_trade` bloqueava apenas mesma direção. Corrigido para bloquear qualquer trade ativo no par. Idem em `sandbox_service._process_radar_signals`.
    - **Race condition — mais de 5 slots abertos**: Resolvido com `asyncio.Lock()` (`_open_lock`) + refetch atômico dentro do lock.
    - **Limite de slots Radar era 10 (deveria ser 5)**: Corrigido para `>= 5`.
    - **GARANTIA_TRAIL travado em 0%**: Condição `current_stop_roi < 0.0` impedia o trailing de avançar após GARANTIA_8 mover stop para 0%. Removida a condição.
    - **`AttributeError: self.dynamic_margin`**: Corrigido para usar `trade.contract_meta["margin"]` com fallback $200.

19. **[V132] Otimização de R:R no Scalping Lab** (2026-07-18):
    - **Limpeza de Base de Dados**: Encerramento manual via script SQL de dois trades travados há >8.5h (`SOLUSDT` e `VETUSDT`).
    - **Garantia de Risco Zero a +12% ROI**: Elevação do patamar do break-even de +8% para +12% no VWAP SNIPER para dar mais runway contra ruídos de preço.
    - **Escadinha de Scalping afrouxada**: Nova escala `ORDER_STOP_LADDER_SCALPING` configurada como (+6%/+1.5%, +10%/+3.5%, +15%/+8.0%, +22%/+15.0%) para dar distância entre o preço atual e o stop, maximizando a captura de lucros e pagando as perdas de -8% de forma estatisticamente lucrativa.
20. **[V132-REFINADO / V132-SWING-2H] Otimização e Refinamento do Sandbox** (2026-07-20):
    - **Scalping Lab:** Injetados os filtros de confluência inteligente: *BTC Trend Bias* no gráfico de 15m, *cruzamento real do Stochastic RSI (K/D)* na sobrevenda/sobrecompra, e *Volume Relativo de 5m* mínimo de 1.1x.
    - **Swing Lab:** Transicionado o motor autônomo para operar no gráfico macro de **2H (120m)** com alavancagem forçada de **50x** e stop loss inicial rígido de **-35% ROI** (0.7% no preço). Scan executado a cada 30min (1800s).
    - **Micro-Gatilho de Precisão (15m):** As ordens de 2H do Swing Lab agora são filtradas na entrada pelo alinhamento do Stochastic RSI no tempo menor de 15m.
    - **Escadinha de Swing 2H 50x:** Atualizada a escala `ORDER_STOP_LADDER_SWING` para gatilho de break-even a +15% ROI, e níveis escalonados (+35%/+10%, +70%/+35%, +120%/+80%, +200%/+150%, +350%/+280% de lucro).
    - **Risco de mesa do Swing:** Mantido limite rígido de no máximo 2 posições sob risco de mesa simultâneas.
21. **[V133] Otimizações de R:R e Risco — Sandbox** (2026-07-24):
    - **Swing Lab — Stop reduzido:** `SWING_STOP_ROI` de -35% para **-20% ROI** (0.4% preço com 50x). Melhora R:R de 1:0.28 para 1:2+.
    - **Swing Lab — ADX elevado:** Threshold de `btc_adx >= 25` para `>= 30`. Exige confirmação de tendência mais forte, filtrando mercados laterais.
    - **Scalping Lab — Stop aumentado:** `_MAX_STOP_ROI` de -8% para **-12% ROI** (0.24% preço com 50x). Dá mais runway ao trade contra ruídos.
    - **Scalping Lab — Filtro de R:R:** Novo filtro rejeita trades com `projected_rr < 1.5` (target = 3x risk, mínimo 15% ROI). Garante potencial de lucro significativamente maior que o risco.
    - **GARANTIA_TRAIL — Breakeven igualado:** `GARANTIA_TRAIL_THRESHOLD` elevado para 8% em ambos modos (Scalping e Swing). Antes 12% no Scalping, 8% no Swing.
    - **Blocklist expandida:** Adicionados INJUSDT, XLMUSDT, GRTUSDT ao `ASSET_BLOCKLIST`.

22. **[V135-RR] Correção de R:R no Scalping Lab — Stop Cap, Breakeven e Trailing** (2026-08-01):
    - **Diagnóstico (Postgres Railway, 150 trades fechados 28/07–01/08):** WR 70.7%, avg win +7.17%, avg loss **−19.41%** → expectancy **−0.62%/trade** (soma −93.6%). Causa raiz: **55% dos stops (24/44) estiveram no lucro (+1% a +8%) e caíram até −25%**; VELOCITY FLOW −98%; LONGs −127% vs SHORTs +33.6%.
    - **Simulação `sim_rr.py` sobre os 150 trades reais:** Cenário A (breakeven +4%, trailing 75%, stop −12%) → **expectancy +3.23%/trade, +487.7pp, WR 76.2%**, avg loss −12%. Atual = −1.02%/trade.
    - **Breakeven antecipado** (`sandbox_service.py:1586`): GARANTIA_8 → **GARANTIA_4**, stop vai a 0% ROI em **+4%** (ambos modos). Protege os 55% de trades que atingiam +1~+8% e revertiam.
    - **Trailing apertado** (`sandbox_service.py:1608`): 60% → **75% do pico** (`max(1.5, max_roi × 0.75)`). Trava mais lucro nas costas do trade sem matar home runs.
    - **Stop inicial capado em −12%** (`sandbox_service.py`): fallback `−25%` → **−12%**, teto estrutural `−15%` → **−12%**, range estrutural `[−40,−25]` → **[−12,−6]**, clamp ATR `[−12,−15]` → **[−8,−12]**.
    - **Resultado esperado:** avg loss −19.4% → ~−12%, expectancy negativa → **+3.2%/trade** em PAPER (validado pela simulação sobre os trades reais).

23. **[V136-SWING] Swing Lab — Trades de 1-7 dias, TP por S/R e Padrões Gráficos** (2026-08-06):
    - **Trailing suave Swing** (`sandbox_service.py:1582-1620`): GARANTIA_TRAIL agora aplica **50% do pico** para Swing (era 75%统一). Breakeven antecipado de +4% para **+12%** no Swing. Min trail +3% (era +1.5%). Scalping inalterado (75%/+4%/+1.5%).
    - **Fix leverage** (`config.py:175`): `SWING_LEVERAGE=50` (era 10, conflito com `sandbox_service.py` que usava 50).
    - **Janela preço 30min** (`okx_ws_public.py`): Nova função `get_conservative_price_swing()` usa janela de 1800s (30min) — evita fechar em wicks de 2min. FlashAgent rota Swing para esta função.
    - **Take Profit baseado em S/R** (`sandbox_swing_service.py:549-633`): `_calculate_swing_tp()` detecta resistências acima (LONG) ou suportes abaixo (SHORT) e cria stop ratchet progressivo. Configs: `SWING_TP_ENABLED=True`, `SWING_TP_MIN_DISTANCE=5%`, `SWING_TP_MAX_DISTANCE=100%`.
    - **Detecção de padrões gráficos** (`backend/services/patterns/`): Triângulos (simétrico/ascendente/descendente), Topo/Fundo Duplo, Head & Shoulders. PatternDetector unificado com boost +10 a +25 pontos no score do sinal.
    - **Resultado esperado:** Trades Swing duram 1-7 dias (não fecham prematuramente), TP alvo em S/R, score boostado por padrões gráficos confirmados.

24. **[V140-LAYA-WHALE-RADAR] Laya Sovereign Brain & Radar Institucional de Baleias e Sardinhas** (2026-09-26):
    - **Cérebro Soberano Unificado**: Laya assumiu o loop decisório de entrada e saída, absorvendo as responsabilidades táticas do CaptainAgent e FlashAgent.
    - **LayaFlowService (`backend/app/services/laya_flow_service.py`)**: Monitora endpoints públicos da OKX Rubik (`long-short-account-ratio` e `open-interest-volume` com candles de 5m).
    - **Matriz de Fluxo Baleia vs Sardinha**: Cruza o delta de preço com o delta de Open Interest e o Long/Short Ratio:
        * `RETAIL_TRAP_LONG`: Varejo eufórico em Long (LSR > 1.35). Emite veto automático de compra e prepara scalps de venda a favor do dump das baleias.
        * `LONG_LIQUIDATION_BOTTOM`: Preço caindo com OI despencando (varredura de stops de sardinhas). Quando o preço rejeita a mínima e o OI estabiliza, Laya autoriza compra de reversão institucional com score 93%+.
        * `INSTITUTIONAL_ACCUMULATION`: Rompimento com dinheiro novo (+OI) e varejo equilibrado (LSR < 1.15).
    - **Cockpit HUD e Telemetria**: Visualização nos 4 gráficos do Cockpit com badges em tempo real (`LSR`, `OI Delta` e `Regime de Fluxo`), além de terminal de fluxo de consciência da Laya com atualização a cada 3s.

25. **[V141-SUPERPOWERS-METHODOLOGY] Metodologia Superpowers & Framework de Engenharia Agêntica** (2026-10-02):
    - **Governança de Agentes Autônomos**: Integração formal da metodologia `obra/superpowers` ao 1Crypten.
    - **Regras Canônicas (`.agents/rules/superpowers_methodology.md`)**: Enforçamento de TDD estrito (Red-Green-Refactor), Never Give Back em stops progressivos, anti-hedge rígido e verificação empírica antes de qualquer encerramento de tarefa.
    - **Catálogo de 7 Skills (`.agents/skills/`)**: `brainstorming_blueprint`, `writing_plans`, `test_driven_development`, `subagent_driven_development`, `systematic_debugging`, `verification_before_completion` e `session_forensics`.
    - **AGENTS.md**: Ponto de entrada canônico na raiz para orientar qualquer harness de IA (Antigravity, Claude Code, Cursor, Hermes, OpenCode).

26. **[V142-LAYA-KRONOS-CONFLUENCE] Matriz Bidimensional de Confluência: Laya (Fluxo) + Kronos (Tempo)** (2026-10-02):
    - **LayaKronosConfluenceService (`backend/app/services/laya_kronos_confluence_service.py`)**: Cruza em tempo real a psicologia do fluxo de baleias vs sardinhas da OKX Rubik (LSR e ΔOI) com a previsão geométrica autorregressiva de séries temporais do Kronos (AAAI 2026).
    - **Veto de Euforia de Varejo (`RETAIL_TRAP_VETO`)**: Se o LSR >= 1.35 (varejo eufórico comprando topo), veta automaticamente ordens LONG mesmo que o modelo neural preveja alta.
    - **Super Gatilho Sniper Long/Short**: `LONG_LIQUIDATION_BOTTOM` + Kronos `UP` (+15 pts score boost, 50x liberado); `SHORT_SQUEEZE_EXHAUSTION` + Kronos `DOWN` (+15 pts boost).
    - **Teto Dinâmico de Alavancagem por Dispersão de Trajetórias**: Quando a dispersão entre caminhos probabilísticos do Kronos >= 0.035, capa alavancagem em 20x contra wicks.
    - **Endpoint de Telemetria**: `GET /api/v1/laya/kronos-confluence` integrado ao Hermes e ao Cockpit.

27. **[V143-KRONOS-CHART-PROJECTION & MULTI-ASSET-ROTATION] Projeção Visual Kronos nos Gráficos & Rotação de 14 Pares** (2026-10-02):
    - **Visualização de Alvos Kronos no Cockpit (`cockpit.html`)**:
        * **Linhas de Preço Tracejadas Roxas Neon (`#B388FF`, `LargeDashed`)**: Cada quadrante G1–G4 renderiza em tempo real a projeção do alvo calculada pelo Kronos (`❖ KRONOS ALVO`), além das linhas amarela (entrada), vermelha (stop loss) e verde (take profit).
        * **Badges de Convicção nos Headers**: Exibição dinâmica de `❖ KRONOS: {SIDE} {CONVICTION}%` no cabeçalho de cada gráfico.
        * **Overlay HUD Tático Flutuante**: Linha dinâmica no canto superior esquerdo dos 4 gráficos com `❖ KRONOS: $alvo ({change_pct}%)`.
    - **Pool de 14 Ativos Institucionais com Rotação Anti-Monopólio**:
        * Expansão da varredura Laya para 14 pares de elite (`SOL`, `AVAX`, `NEAR`, `LINK`, `ETH`, `SUI`, `XRP`, `ADA`, `DOT`, `APT`, `ARB`, `OP`, `INJ`, `RENDER`).
        * Aplicação de penalidade de rotação (-8.0 pts para a última moeda operada), impedindo o monopólio de `SOLUSDT` e distribuindo as ordens ativas simultaneamente entre os 4 quadrantes.
    - **Novo Endpoint REST de Projeção**: `GET /api/v1/hermes/laya/kronos-projection?symbol={symbol}&side={side}&current_price={price}`.
    - **Otimização Concorrente & Cache Não-Bloqueante**:
        * Ativação de concorrência SQLite em modo WAL (`PRAGMA journal_mode=WAL; PRAGMA busy_timeout=30000;`) eliminando travamentos de escrita/leitura.
        * Caches em memória com TTL de 2 a 3.5s nas rotas `/api/sandbox/unified-state`, `/api/slots` e `/api/radar/pulse` para manter tempo de resposta abaixo de 50ms sob polling massivo do frontend.

28. **[V144-MCP2-RAG-FINETUNING-PIPELINE] MCP 2.x, RAG Semântico Unificado & Fine-Tuning** (2026-10-02 / Validado 2026-10-06):
    - **Model Context Protocol (MCP 2.x) Nativo (`backend/services/mcp_bridge.py`)**:
        * Montagem nativa a nível de módulo FastAPI em `/mcp` (`app.mount("/mcp", ...)`).
        * Suporte a clientes SSE MCP 2.x em `/mcp/sse` e `/mcp/messages`, com endpoint de auditoria em `/mcp/tools`.
        * Exposição de 5 ferramentas oficiais de trading para OKX SWAP (`get_balance`, `get_positions`, `get_radar_signals`, `evaluate_asset`, `get_system_snapshot`).
        * Suporte standalone via `backend/mcp_server.py` para Claude Desktop, Cursor e n8n.
    - **Motor RAG Semântico Unificado (`backend/services/rag_service.py` & `backend/routes/rag_routes.py`)**:
        * Indexação em memória de 120+ seções canônicas de `MASTER_ARCHITECTURE.md`, `vault_galaxy/` (Obsidian Vault: journal, trades, strategies), `AGENTS.md` e `.agents/rules/`.
        * Algoritmo de busca semântica BM25/TF-IDF sub-milissegundo (~60ms de indexação).
        * Integração ativa com o `HermesAgent` e `routes/chat.py`: injeção dinâmica de contexto nos prompts do operador.
        * Endpoints REST ativos: `GET /api/v1/hermes/rag/search?q={query}`, `POST /api/v1/hermes/rag/reindex` e `GET /api/v1/hermes/rag/status`.
    - **Pipeline de Datasets & Fine-Tuning (`backend/app/ml/fine_tuning/` & `backend/app/api/v1/endpoints/ml.py`)**:
        * **DatasetGenerator (`dataset_generator.py`)**: Exportação automática de histórico de trades do Sandbox/OKX e fluxo Rubik em formato JSONL supervisionado para Laya (`laya_decision_dataset.jsonl`) e sequências temporais de 24→12 velas para Kronos (`kronos_series_dataset.jsonl`).
        * **LayaFineTuneTrainer (`laya_finetune_trainer.py`)**: Calibração empírica Bayesiana / Temperature Scaling sobre as probabilidades de decisão (BUY/SELL/HOLD) por regime de mercado, gerando `laya_calibrated_weights.json`.
        * **KronosAdapterTrainer (`kronos_adapter_trainer.py`)**: Calibração de dispersão probabilística de trajetórias e incerteza para as K-lines da OKX (`kronos_adapter.json`).
        * **Integração em Produção**: `LayaRouterService` carrega dinamicamente `laya_calibrated_weights.json` na inicialização e modula a confiança das decisões de entrada.
        * Endpoints REST ativos: `POST /api/v1/ml/generate-dataset`, `GET /api/v1/ml/dataset-stats`, `POST /api/v1/ml/train-laya`, `POST /api/v1/ml/train-kronos` e `GET /api/v1/ml/status`.

29. **[V145-ASYMMETRIC-RR-REALTIME-PRICE-INTEGRITY] Calibração de Risco/Retorno Assimétrico 4:1, Escada Laya e Integridade de Preços em Tempo Real** (2026-10-04):
    - **Expectativa Matemática Positiva (R:R 4:1)**:
        * Limitação estrita da perda máxima por operação em `stop_dist = 0.005` (0.50% no preço = **-7.5% ROI** com alavancagem 15x).
        * Alvos calibrados em `target_dist >= 0.020 a 0.024` (+30.0% a +36.0% ROI), revertendo a assimetria anterior deficitária (de 0.36:1 para **4:1**).
        * Reversão da expectativa matemática líquida de -10.63% para **+4.93% por trade** mesmo com taxa de acerto conservadora de 35%.
    - **Nova Escadinha Dedicada `ORDER_STOP_LADDER_LAYA_REVERSION`**:
        * Inclusão formal da 6ª escadinha no motor (`order_projection_service.py`): Breakeven antecipado a +6.0% ROI travando +1.5%, subindo progressivamente (+10%/+4%, +15%/+8%, +22%/+15%, +30%/+25%).
        * Roteamento automático no Sandbox (`sandbox_service.py`) quando `strategy_class == "LAYA_MEAN_REVERSION"`.
    - **Integridade de Cotações em Tempo Real (Zero Phantom Fallbacks)**:
        * Remoção de todos os preços estáticos fixos em `laya_router_service.py` (antigos INJ a $18.50 e ADA a $0.35 eliminados).
        * Resolução em cascata: WebSocket `okx_ws_public` -> Cache REST -> Batch SWAP tickers (`https://www.okx.com/api/v5/market/tickers?instType=SWAP`) com contingência AWS.
        * Se o preço for <= 0 ou indisponível, o ativo é sumariamente ignorado pela Laya. Nunca mais abre ordem com preço sintético.
        * Cálculo de suporte/resistência para Mean Reversion baseado no ponto médio real das últimas 24h: `(high24h + low24h) / 2.0`.
    - **Correção Visual no Cockpit e Deduplicação no Multi-Chart Grid**:
        * Refatoração do hook `gridSymbols` em `frontend/cockpit.html`, garantindo 4 pares distintos e eliminando a duplicação entre G1 e G3.
        * Traçado de linhas de entrada e stop garantido dentro da amplitude visível das velas (resolvendo o problema das linhas "invisíveis" que ficavam 2.5x acima da tela).
    - **Reativação Concorrente do Swing Lab**:
        * Inicialização do `sandbox_swing_service.start()` no `backend/main.py`, permitindo operação paralela de até 15 slots de swing com 4 slots de scalping.
    - **Otimização de Latência em `/api/slots`**:
        * Configurado `fetch_contract=False` em `database_service._attach_order_projections`, reduzindo o tempo de resposta da rota de 10s para < 200ms.

30. **[V146-PROFITABILITY-PIVOT] Re-calibração Estrutural de Risco/Retorno Positivo (R:R > 2:1), Eliminação da Asfixia do Trailing e Desacoplamento do Viés Direcional** (2026-10-05):
    - **Diagnóstico Forense do Déficit Estrutural (`local_sniper.db`)**:
        * Auditoria sobre 68 trades de Scalp revelou Win Rate de 48.5%, ganho médio de +4.57% (+$9.13) e perda média de **-9.55% (-$19.09)**.
        * Payoff ratio de **1 : 2.09 INVERSO** (derrota média 2x maior que vitória), exigindo mais de 67.6% de acerto apenas para breakeven.
        * No Swing Lab, perdas atingiram -22.46% (FETUSDT) e 28.91% de lucro foi devolvido da máxima (THETA bateu +32% e saiu no 0.00%).
        * Viés artificial: 80.9% dos trades eram SHORT empurrados pela regra fixa de `if lsr >= 1.35`.
    - **Inversão Matemática das Escadinhas (`order_projection_service.py`)**:
        * **`ORDER_STOP_LADDER_LAYA_REVERSION`**: Fim da asfixia precoce em +6%. Novo Nível 1: Disparo em +10% ROI -> Stop +2% (breakeven real cobrindo taxas). Nível 2: Disparo em +18% ROI -> Stop +8% (lucro real garantido). Nível 3: +28%/+18%. Nível 4: +42%/+30%. Trailing: +60%/+45%.
        * **`ORDER_STOP_LADDER_SWING`**: Proteção contra devolução total de lucros. Nível 1: +15%/+2%. Nível 2: Disparo em +25% ROI -> Stop +12% (impossibilita devoluções de trades de +30% para zero). Nível 3: +40%/+25%. Nível 4: +65%/+45%.
        * **`ORDER_STOP_LADDER_SCALPING`**: Nível 1: +10%/+2%, Nível 2: +18%/+8%, Nível 3: +30%/+18%, Trailing: +45%/+32%.
    - **Redução e Capagem Estrita de Stops Iniciais**:
        * Scalping Lab (`sandbox_service.py`): `fallback_roi` reduzido de -12.0% para -6.5%; `limit_roi` travado no teto rígido de **-7.0% ROI**; ATR clamp ajustado para `[-7.0%, -5.0%]`.
        * Swing Lab (`sandbox_swing_service.py`): `stop_roi_target` reduzido de 20.0% para **10.0% ROI**.
    - **Eliminação do Viés de Venda e Dinamização de Canais (`laya_router_service.py`)**:
        * Remoção dos suportes e resistências fixos defasados (`base_sr` estático de 2024 removido).
        * Análise por posição de canal: Se preço estiver na metade inferior (`diff_pct <= -0.2%`), prioridade total para **LONG** (comprar fundo no suporte). Se estiver esticado no topo (`diff_pct >= +0.2%`), prioridade para **SHORT**.
31. **[V147-BINANCE-ORBS-INTELLIGENCE] Redesign Binance Design System, Thinking Orbs em 15 Pontos, RAG Semântico e MCP 2.x Bridge** (2026-10-09):
    - **Identidade Visual Binance Design System (getdesign.md/binance/design-md)**:
        * Paleta oficial Binance aplicada rigorosamente em `backend/app/static/css/lamborghini.css` e templates frontend: Deep Canvas `#0B0E11`, Superfícies e Cards `#1E2329` / `#181A20`, Bordas `#2B3139`, Amarelo Ícone Binance `#FCD535` (`#F0B90B` no hover), Verde Trading `#0ECB81` e Vermelho Trading `#F6465D`.
        * Cantos polidos com raio sutil (`border-radius: 4px`), eliminando a estética opaca antiga e conferindo acabamento de terminal institucional.
    - **Motor Matemático 2D Thinking Orbs (marcondes-orbs.vercel.app)**:
        * Implementação pura em Canvas 2D sem dependências pesadas (`thinking_orbs.js`), com suporte aos 9 estados dinâmicos (`working`, `searching`, `solving`, `listening`, `connecting`, `weaving`, `composing`, `breathing`, `shaping`) e DPR dinâmico.
        * **15 pontos estratégicos** em execução no Cockpit:
            1. Banner Laya Soberana (`solving`, `#FCD535`)
            2. Net Worth & Equity (`breathing`, `#FCD535`)
            3. Slots & Capacidade (`working`, `#0ECB81`)
            4. Regime & Oracle (`solving`, `#FCD535`)
            5. Kronos Conviction (`searching`, `#B388FF`)
            6. Flash Map Container (`working`, `#FCD535`)
            7-10. Headers dos 4 Gráficos G1, G2, G3 e G4 (`weaving`, `#FCD535`)
            11. Banca Consolidada (`breathing`, `#FCD535`)
            12. Ordens Abertas (`working`, `#0ECB81`)
            13. Laya Soberana Consciência (`solving`, `#FCD535`)
            14. Painel de Custódia Geral (`working`, `#FCD535`)
            15. Histórico de Auditoria (`solving`, `#FCD535`)
        * Header Global (`shell.js`): Orb de sistema (`solving`) e Pulso da Frota (`listening`).
        * Hermes Intelligence Console (`hermes.html`): Orb no header (`solving`) e orbs de composição.
    - **Protocolos de Inteligência & Memória Unificada**:
        * **RAG Semântico (`RAGService`)**: Indexação vetorial BM25/TF-IDF cobrindo `MASTER_ARCHITECTURE.md`, o cofre Obsidian `vault_galaxy/` e regras `.agents/rules/` com recuperação sub-milissegundo integrada diretamente no prompt do Hermes e da Laya.
        * **MCP Bridge 2.x (`mcp_bridge.py`)**: Montagem nativa em `/mcp` com suporte a SSE (`/mcp/sse`) e ferramentas expostas: `get_balance`, `get_positions`, `get_radar_signals`, `evaluate_asset`, `get_system_snapshot`.
        * **Memória Única e Persistência de Conversas**: Gravações de voz via Whisper e interações de chat registradas automaticamente no Obsidian Vault (`vault_galaxy/journal/`), garantindo que tanto o Hermes quanto a Laya possuam histórico compartilhado contínuo e sem alucinações.

32. **[V148-PROFITABILITY-TURNAROUND] Inversão Estrutural do Payoff (R:R Realizado 1.81:1, Profit Factor 2.32), Resolução Multi-Variante de Símbolos, TP1 Inteligente (+8.0% ROI), Capping Rígido (-3.5% ROI) e Liquidação Disciplinada de Alvos** (2026-10-10):
    - **Diagnóstico Forense de Produção (`scratch/analyze_performance.py`)**:
        * Baseline inicial com 12 trades: 58.3% Win Rate (7W / 5L), porém PnL negativo de **-5.06%** (-$142.51) com Payoff invertido de **0.56:1** (ganho médio +2.69% vs perda média -4.77%).
        * Perdas extremas de -9.66% e -9.46% consumiam 4 vitórias consecutivas.
        * Viés de 100% SHORT gerado por falha no cálculo de `mid_prices` no `laya_router_service.py` (que só rodava para ativos faltantes no cache).
        * Ordens zumbis no Sandbox (ex: XRP a 1.40 com stop em 1.05) nunca disparavam stop porque `okx_ws_public` armazenava `XRPUSDT`, enquanto o Sandbox consultava `XRP-USDT-SWAP` e recebia preço 0.0.
        * O loop do Sandbox checava apenas stops, sem nenhuma verificação de alcance de alvos de lucro (`trade.target`).
    - **Inversão Matemática do Risco/Retorno & Novo Teto Rígido de Stop Loss**:
        * **Capping Estrito de Stop Loss**: `_calculate_adaptive_stop` travado no limite rígido de **-3.5% ROI** (anteriormente permitia até -7.5%, atingindo -9.66% com custos operacionais).
        * **TP1 Inteligente (+8.0% ROI)**: Realização parcial de 50% da margem em +8.0% ROI, elevando o stop da metade restante para **+2.5% ROI** (lucro garantido em ambos os lados).
        * **Liquidação Disciplinada de Alvos (`CLOSED_TARGET`)**: Implementada validação de direção (`target > entry` para LONG, `target < entry` para SHORT) e fechamento instantâneo no alvo estipulado.
    - **Resolução Multi-Variante de Símbolos (`backend/services/okx_ws_public.py`)**:
        * `_resolve_symbol_variants()` mapeia transparentemente `XRPUSDT`, `XRP-USDT`, `XRP-USDT-SWAP` e `XRPUSDT.P`.
        * Preços e cotações extremas são propagados em todas as variantes, eliminando falhas de cotação 0.0 e stops fantasmas.
    - **Filtro Protetivo de Momentum e Simetria LONG/SHORT (`backend/app/services/laya_router_service.py`)**:
        * Busca em lote de tickers SWAP agora calcula `mid_prices` e `change_24h_pct` para **todos os 14 ativos da frota** em todo ciclo de varredura.
        * `evaluate_channel_position` bloqueia SHORTs contra momentum quando a variação de 24h for >= +1.8% ou LSR < 1.10.
        * Redimensionamento de ordens: Margem de **$150.0** e Alavancagem de **12x** (nocional $1.800), reduzindo o impacto de taxas OKX + slippage de 1.95% para **1.56%**.
    - **Evidência Empírica Pós-Turnaround**:
        * **16 trades fechados**: 9 vitórias (56.2%), 7 derrotas (43.8%).
        * Lucro Bruto: **+80.92%** | Prejuízo Bruto: **-34.87%**.
        * **PnL Líquido Acumulado**: **+46.06%**.
        * **Gain Médio**: **+8.99%** | **Loss Médio**: **-4.98%**.
        * **Payoff Ratio Realizado**: **1.81:1** (a favor do sistema).
        * **Profit Factor**: **2.32**.
        * 100% de aprovação na suíte de testes de invariantes (`test_laya_stop_ladder.py`, `test_laya_stop_invariants.py`, `test_profitability_pivot.py`).

33. **[V149-UNIFIED-BANCA-RESET] Correção Estrutural do Reset da Banca, Desacoplamento de Auth Local e Purga Consolidada de Sandbox/Cockpit** (2026-10-10):
    - **Diagnóstico da Falha do Botão Reset**:
        * **Falha de Autorização 401**: No `auth_service.py`, a regra de bypass dev exigia simultaneamente `secrets_manager.environment.value == "dev"` e `settings.DEBUG`. Como em desenvolvimento local `settings.DEBUG` estava `False`, chamadas a `/api/admin/reset-system` eram rejeitadas com `401 Unauthorized`.
        * **Desincronização de Estado (Escopo Incompleto)**: A rota antiga limpava apenas o Postgres/Slots legados, mantendo intactas as tabelas `sandbox_trades` e `sandbox_swing_trades` no SQLite `local_sniper.db`. Como o Cockpit calcula o saldo simulado via `get_sandbox_unified_balance() = 10000.0 + total_pnl_usd`, a banca mantinha o valor anterior mesmo após o reset.
        * **Caches In-Memory Órfãos**: `sandbox_service.base_balance_cache`, `_peak_roi_cache`, `equity_peak` e `equity_floor` não eram zerados.
    - **Solução Implementada**:
        * **Correção no `auth_service.py`**: Bypass em dev ativado para `secrets_manager.environment.value == "dev" or settings.DEBUG`, concedendo `SOVEREIGN_USER` (admin) para requisições locais.
        * **Purga Nuclear em `database_service.reset_system_data()`**: Limpa `SandboxTrade`, `SandboxSwingTrade`, `Slot` (reseta para status LIVRE), `Moonbag`, `TradeHistory`, zera `equity_peak = 10000.0`, `equity_floor = 10000.0`, e reseta `sandbox_service` e `sandbox_swing_service`.
        * **Nova Rota Direta `POST /api/banca/reset`**: Endpoint unificado para restauração instantânea da banca para $10,000.00 com retorno do saldo sincronizado.
        * **Atualização na UI (`SettingsPage.js` e `cockpit.html`)**: Fallback automático entre rotas de reset, purga de `localStorage` (`banca_cache`, `cockpit_cache`), e adição de botões de reset rápido nos cards de Patrimônio Líquido e Net Worth do Cockpit.

34. **[V150-MCP-RAG-FINETUNING-CONSOLIDATION] Consolidação Canônica de MCP 2.x, RAG Semântico e Fine-Tuning Supervisionado H1** (2026-10-12):
    - **Documentação Técnica Canônica**: Publicada formalmente em [`docs/07_MCP_RAG_FINE_TUNING.md`](file:///c:/Users/jonat/Desktop/Sistemas%202026/2%20-%201C-SET26/docs/07_MCP_RAG_FINE_TUNING.md).
    - **Model Context Protocol (MCP 2.x)**:
        * Montagem ASGI FastAPI em `/mcp` (`/mcp/sse`, `/mcp/messages`, `/mcp/tools`) + Servidor Stdio Standalone em `backend/mcp_server.py`.
        * Catálogo de 5 ferramentas para OKX SWAP: `get_balance`, `get_positions`, `get_radar_signals`, `evaluate_asset`, `get_system_snapshot`.
    - **RAG Semântico Unificado (Second Brain)**:
        * Indexação vetorial BM25/TF-IDF sub-milissegundo cobrindo `MASTER_ARCHITECTURE.md`, `vault_galaxy/`, `AGENTS.md`, `.agents/rules/` e `docs/`.
        * Injeção de contexto em tempo real no prompt do `HermesAgent` e na rota `/chat`. Endpoints `/api/v1/hermes/rag/search`, `/reindex` e `/status`.
    - **Pipeline de Datasets & Fine-Tuning / Calibração**:
        * Exportação supervisionada de trades para JSONL (`laya_decision_dataset.jsonl`, `kronos_series_dataset.jsonl`).
        * Calibração Bayesiana e Temperature Scaling ($T = 0.85$) com fatores de escala por regime (`laya_calibrated_weights.json`).
        * Integração com a nova tese **LAYA_SMART_MONEY_H1** (saída de acumulação 1H, confluência LSR x Open Interest e stop loss blindado alimentando o pipeline contínuo de aprendizado).

35. **[V151-PLUTUS-ARCA-PASSIVE-INCOME-ENGINE] Agente Plutus, Método ARCA e UI Dedicada Binance Design System** (2026-10-12):
    - **Blueprint e Especificação Técnica**: Registrado em [`docs/blueprint/07_PLANO_AGENTE_PLUTUS_ARCA.md`](file:///c:/Users/jonat/Desktop/Sistemas%202026/2%20-%201C-SET26/docs/blueprint/07_PLANO_AGENTE_PLUTUS_ARCA.md).
    - **Motor do Agente Plutus (`backend/services/plutus_agent.py`)**:
        * Matemática reversa para viver de renda: calcula o patrimônio exato necessário a partir de qualquer meta mensal desejada (ex: R$ 50.000,00/mês).
        * Alocação em 4 pilares anti-frágeis do **Método ARCA** (Primo Rico / Thiago Nigro):
          1. **Real Estate (FIIs Isentos de IR)**: HGLG11, BTLG11, XPML11, KNCR11, KNHY11, HGRU11 (35%-45%).
          2. **Ações de Dividendos BR**: BBAS3, TAEE11, ITUB4, EGIE3, BBSE3 (20%-30%).
          3. **Caixa & Renda Fixa**: Tesouro IPCA+ c/ Juros Semestrais, Debêntures Incentivadas, Tesouro Selic (10%-25%).
          4. **Ativos Internacionais (Dólar)**: Realty Income (O - dividend mensal), SCHD, VNQ, IVVB11 (15%-20%).
        * Integração com APIs públicas gratuitas (AwesomeAPI / Yahoo / BCB) com fallback canônico auditado.
        * Orquestração nativa com o **Hermes Intelligence** para parecer executivo e confluência macroeconômica.
    - **Rotas FastAPI (`backend/routes/plutus_routes.py`)**:
        * `POST /api/v1/plutus/simulate`: Cálculo financeiro reverso, cotas a comprar e fluxo de caixa de 12 meses.
        * `GET /api/v1/plutus/universe`: Catálogo de ativos de elite da ARCA.
        * `POST /api/v1/plutus/hermes-diagnosis`: Parecer institucional emitido pelo Hermes.
        * Página estática servida em `/plutus` e `/plutus.html`.
    - **Interface Dedicada Binance Design System (`backend/app/static/plutus.html`)**:
        * 100% aderente aos tokens oficiais de `getdesign.md/binance/design-md`: Fundo Canvas `#0b0e11`, cards `#1e2329`, bordas `#2b3139`, amarelo `#fcd535`, verdes/vermelhos de trading `#0ecb81` / `#f6465d`, zero emojis e fontes mono para finanças.
        * Input interativo de renda mensal, seletor de perfil, 4 cards de KPIs, visualizador dos pilares da ARCA, tabela detalhada cota por cota e diagnóstico do Hermes.
    - **Integração no Shell Unificado & Menu Lateral (`backend/app/static/shell.js` e `cockpit.html`)**:
        * **Sidebar Drawer Retrátil (`#app-sidebar`)**:
          - Seção *Páginas do Sistema*: `PLUTUS (VIVER DE RENDA)` com badge dourado `[ARCA]` e ícone SVG monetário.
          - Seção *Agentes da Frota*: `PLUTUS · MÉTODO ARCA` com status `ON`.
        * **Barra Superior Desktop (`desktop-nav`)**: Atalho direto `PLUTUS` ao lado do Cockpit, Hermes, Radar e Docs.
        * **Frota no Header (`header-fleet-pills`)**: Telemetria visual exibindo `HERMES • CAPTAIN • FLASH • KRONOS • PLUTUS`.
        * **Barra Inferior Mobile (`app-bottom-bar`)**: Item de acesso tátil rápido `Plutus`.
        * **Cockpit Tático (`cockpit.html`)**: Card de destaque no topo da coluna esquerda (Mesa Tática) e badge direto no banner superior horizontal com transição de hover em ouro Binance.

36. **[V152-LAYA-MULTI-TIMEFRAME-MULTI-SETUP-ENGINE] Matriz Multi-Timeframe (H1, 15M, 5M) e Orquestração Concorrente de Setups** (2026-10-12):
    - **Diagnóstico da Limitação Anterior**: A Laya rodava exclusivamente a busca por rompimento de consolidação em 1H (`evaluate_h1_breakout`). Como o mercado passa 85% do tempo consolidando no H1, o sistema ficava inativo de braços cruzados emitindo mensagens de `HOLD` contínuas, descartando oportunidades intradiárias.
    - **Arquitetura Hierárquica Multi-Timeframe Implementada (`backend/app/services/laya_router_service.py`)**:
        * **Camada 1 (Prioridade 1 - H1)**: `LAYA_SMART_MONEY_H1` — Saída de acumulação institucional no H1 com confirmação de fluxo (OI novo + LSR descompassado) e stop loss colado na borda da acumulação para anular falsos rompimentos.
        * **Camada 2 (Prioridade 2 - 15M)**: `LAYA_MOMENTO_MOLA` — Compressão de volatilidade máxima (Bollinger Width $\le 1.8\%$) no suporte ou resistência da consolidação de 1H, operando o disparo elástico pré-explosão com stop curto no extremo.
        * **Camada 3 (Prioridade 3 - 5M/1M)**: `LAYA_DVWAP_REVERSION` — Quando o preço está dentro do range de 1H, mas esticado $\ge 1.0\%$ a $2.5\%$ longe da média móvel ponderada por volume (VWAP intradiária), captura o retorno magnético ao centro com alvo na própria linha da VWAP.
        * **Camada 4 (Diagnóstico Integrado no Thought Stream)**: Quando nenhum setup qualifica, o radar não fica em silêncio; emite telemetria das 3 camadas ao vivo: `CONSOLIDAÇÃO H1 ($sup - $res) | DVWAP: diff% | MOLA: BBW%. Aguardando gatilho de borda.`
    - **Roteamento de Stops & Gestão de Risco (`backend/services/order_projection_service.py`)**:
        * As novas classes `LAYA_DVWAP_REVERSION` e `LAYA_MOMENTO_MOLA` foram integradas no roteamento de `ORDER_STOP_LADDER_LAYA_REVERSION` com Early Shield (corte de 73% do risco em +4.0% ROI), breakeven rápido e Trailing Stop Never Give Back.
    - **Evidência Empírica TDD**: Suíte de testes criada em [`tests/test_laya_multi_setup.py`](file:///c:/Users/jonat/Desktop/Sistemas%202026/2%20-%201C-SET26/tests/test_laya_multi_setup.py) com 100% de aprovação (4/4 testes passando, mais 12 testes do ecossistema intactos).

37. **[V153-LAYA-ANTI-FALLING-KNIFE-CALIBRATION] Blindagem Anti-Faca Caindo, Farol Macro do BTC, Circuit Breaker Direcional e Stop Folgado** (2026-10-12):
    - **Diagnóstico da Causa Raiz de Perdas no Sandbox**:
        * A Laya abriu operações de compra LONG sucessivas em altcoins (ETH, INJ, AVAX, DOT) que resultaram em perdas de -3.6% de ROI por trade durante um movimento acentuado de queda do Bitcoin ($87k \to $83.8k).
        * Causa 1: O gatilho de DVWAP disparava com desvio prematuro de apenas 1.0% sem exigir confirmação da tendência do Bitcoin.
        * Causa 2: O stop loss ficava colado demais a 0.6% do preço (`current_price * 0.994`), sendo estopado pelo ruído natural das velas com 15x de alavancagem ($0.6\% \times 15 = 9.0\%$).
        * Causa 3: Ausência de correlação macro com o Bitcoin (`btc_trend_bias`), levando a Laya a comprar faca caindo em altcoins enquanto o BTC derretia.
    - **As 5 Blindagens Implementadas (`backend/app/services/laya_router_service.py` & `sandbox_service.py`)**:
        * **1. Farol Macro do Bitcoin (`btc_trend_bias`)**: Cálculo em tempo real ponderando a variação de 24h e a distância do preço médio do BTC. Se o BTC estiver em viés de queda ($< -0.3\%$), compras de reversão e saídas de acumulação em LONG nas altcoins são vetadas sumariamente (`[BTC MACRO VETO]`).
        * **2. Endurecimento do DVWAP Reversion**: Limiar de desvio elástico elevado de $1.0\%$ para $\ge 2.0\%$ de esticamento da VWAP intradiária, assegurando reversão genuína de sobrevenda institucional.
        * **3. Afastamento do Stop Loss Anti-Ruído**: Distância mínima de stop loss aumentada para pelo menos $1.5\%$ de folga de preço (em vez de $0.6\%$), protegendo a operação de mechas espúrias.
        * **4. Circuit Breaker Direcional**: Rastreador em janela rolante de 45 minutos. Se 2 stops na mesma direção ocorrerem no período, essa direção é travada por 45 minutos (`is_direction_in_cooldown`), impedindo sequências destrutivas.
        * **5. Debounce no Thought Stream**: Supressão de mensagens redundantes repetidas a cada 3 segundos com o mesmo símbolo e ação, mantendo a telemetria clara e limpa.
    - **Evidência Empírica TDD & Operacional**:
        * 100% de aprovação na suíte de testes [`tests/test_laya_multi_setup.py`](file:///c:/Users/jonat/Desktop/Sistemas%202026/2%20-%201C-SET26/tests/test_laya_multi_setup.py) cobrindo Farol Macro do BTC, Circuit Breaker Direcional e limiar de 2.0%.
        * Banca simulada resetada com sucesso para **$10,000.00** via `/api/banca/reset` e verificada em `/api/sandbox/unified-state`.

38. **[V154-LAYA-PREDATORY-INSTITUTIONAL-UPGRADE] Funding Rate Shield, Stop Loss por ATR Dinâmico e Blindagem Diária de Lucro** (2026-10-14):
    - **Diagnóstico da Devolução de Lucro em Sistemas Quantitativos**:
        * Identificação dos 3 fatores que fazem um sistema vencedor devolver o lucro acumulado ao mercado:
          1. *Taxas Invisíveis de Financiamento (Funding Rates)*: Comprar quando o varejo está eufórico pagando taxas às baleias (> +0.03% a cada 8h) ou vender em euforia de baixa (< -0.03%).
          2. *Stop Hunting por Falta de ATR*: Stops fixos a 0.3%–0.5% em moedas de alta volatilidade sendo caçados pelo ruído de velas de 1 minuto antes do movimento ocorrer.
          3. *Overtrading Pós-Meta*: Não travar o capital ganho e continuar expondo a banca a 4 slots em horários de liquidez degradada.
    - **As 3 Inovações Predatórias Implementadas (`backend/app/services/laya_router_service.py`)**:
        * **1. Funding Rate Shield (`funding_rate_map`)**:
          - Consulta em tempo real das taxas de financiamento da OKX SWAP oficial via `okx_rest_service.get_funding_rate(pair)`.
          - Se `funding_rate > +0.0003` (+0.03%): Veto imediato de LONG (`[VETO FUNDING RATE]`). A Laya recusa-se a pagar aluguel às baleias.
          - Se `funding_rate < -0.0003` (-0.03%): Veto imediato de SHORT (`[VETO FUNDING RATE]`). Evita a armadilha clássica de Short Squeeze institucional.
        * **2. Stop Loss Estrutural por ATR Dinâmico (`calculate_atr_pct`)**:
          - O stop loss não é mais uma porcentagem fixa cega. Ele calcula o Average True Range real de 14 períodos das velas de 1H de cada par.
          - Distância mínima de stop calibrada em $\max(1.2\%, 1.2 \times ATR\_pct)$, impedindo que ativos pesados como ETH ou SOL tenham stops asfixiados a menos de $1.2\%$.
        * **3. Trava de Meta Diária de Preservação de Capital (Capital Preservation Lock)**:
          - A Laya consulta o saldo consolidado da Sandbox em tempo real.
          - Se o lucro diário atingir $\ge +2.5\%$ (+$250): Reduz a capacidade de slots para 2 (em vez de 4) e eleva a nota de corte `MIN_ENTRY_SCORE` de 84 para 92 (Modo Sniper Seletivo).
          - Se o lucro diário atingir $\ge +5.0\%$ (+$500): Trava 100% de novas aberturas (`max_allowed_slots = 0`), garantindo que o dinheiro conquistado não volte para o mercado no overtrading.
    - **Evidência Empírica TDD & Operacional**:
        * 100% de aprovação na suíte de testes [`tests/test_laya_multi_setup.py`](file:///c:/Users/jonat/Desktop/Sistemas%202026/2%20-%201C-SET26/tests/test_laya_multi_setup.py) com 11 de 11 testes unitários passando.

39. **[V155-OKX-MARKET-UNIVERSE-AND-TARGET-GEOMETRY] Catálogo Universal da OKX (489 Contratos USDT-SWAP), Blindagem Geométrica de Alvos e Expurgamento de Código Legado** (2026-10-14):
    - **Diagnóstico do Bug Crítico de Geometria de Alvo**:
        * Ordens de SHORT abertas pelo motor legado `sandbox_service.py` (`VELOCITY FLOW`, ex: `FETUSDT` e `IMXUSDT`) calculavam o alvo cegamente como `entry_price * 1.5` (+50% para cima).
        * Consequência: Em operações vendidas (SHORT), a linha de Take Profit ficava desenhada no topo do gráfico no sentido de LONG, e a checagem `current_price <= target_price` nunca disparava porque o alvo estava acima da entrada.
    - **As 4 Soluções Estruturais Implementadas**:
        * **1. Correção Universal da Geometria de Alvo e Stop (`sandbox_service.py` & `cockpit.html`)**:
          - Se `LONG`: Alvo $= \text{Entrada} \times 1.035$ (Acima) | Stop $= \text{Entrada} \times 0.988$ (Abaixo).
          - Se `SHORT`: Alvo $= \text{Entrada} \times 0.965$ (Abaixo) | Stop $= \text{Entrada} \times 1.012$ (Acima).
          - Cockpit HUD e Chart PriceLines possuem trava geométrica sanitizadora que impede visualização invertida mesmo sob anomalias de dados legados.
        * **2. Catálogo Universal de Mercado OKX (`backend/app/services/okx_universe_service.py`)**:
          - Mapeamento universal em lote de 489 contratos USDT-SWAP da OKX (`GET /api/v5/public/instruments?instType=SWAP`).
          - Resolução precisa de especificações canônicas: `instId`, `ctVal`, `tickSize`, `lotSize`, `minSz`.
          - Consulta dinâmica de tickers (`GET /api/v5/market/tickers?instType=SWAP`) trazendo preços reais, volumes 24h e variações.
          - A Laya Soberana não está mais limitada a uma lista fixa de 14 moedas; ela opera sobre os ativos de maior liquidez e volume ranqueados em tempo real (`okx_universe_service.get_tradable_universe()`).
        * **3. Expurgamento de Bypass Legado (`firebase_service.py`)**:
          - Desativado o hook obsoleto `sandbox_service.on_radar_pulse(signals)`, assegurando soberania única e exclusiva da Laya para autorização de trades.
        * **4. Sanitização do Banco de Dados Operacional (`local_sniper.db`)**:
          - Executada rotina de correção imediata das ordens ativas com alvo no céu, restaurando a conformidade dos trades ativos.

40. **[V156-LAYA-HIGH-THROUGHPUT-CONCURRENCY-AND-DUST-SHIELD] Otimização de Concorrência de Alta Vazão da Laya, Blindagem Anti-429 e Filtragem de Ativos Não-Cripto** (2026-10-14):
    - **Diagnóstico da Latência e Bloqueio de Execução**:
        * Identificado `ZeroDivisionError` em moedas de pó microscópicas (preço $< 0.001$) no cálculo de VWAP.
        * Identificado afunilamento assíncrono em `laya_flow_service.py` causado por lock global desnecessário que serializava consultas a todas as moedas.
        * Identificado rate-limiting (HTTP 429) em endpoints OKX Rubik por requisições paralelas não cacheadas.
        * Presença de ativos não-cripto da OKX (ações e commodities sintéticas: `NVDA`, `XCU`, `CL`, etc.) causando fallback de candles.
    - **As 4 Soluções Estruturais Implementadas**:
        * **1. Resiliência Matemática no Cálculo de VWAP (`laya_router_service.py`)**:
          - Proteção estrita contra divisão por zero para moedas de pó (`if cum_vol <= 0 or cum_tpv <= 0: return ...`, `if vwap <= 0: return ...`).
        * **2. Blindagem Anti-429 e Conexão com Rate Limiter Canônico (`laya_flow_service.py`)**:
          - `laya_flow_service` agora utiliza os métodos oficiais e rate-limitados de `okx_rest_service.get_account_ratio` e `get_open_interest`, com TTL de 120 segundos.
          - Removido o lock global serializador, liberando concorrência de alta vazão para os 12 ativos da Matrix Elite.
        * **3. Filtragem de Ativos de Pó e Ações/Commodities (`okx_universe_service.py`)**:
          - Adicionados filtros contra tokens de pó (`< 0.001`, `SATS`) e derivativos não-cripto (`NVDA`, `AAPL`, `TSLA`, `XAU`, `CL`, etc.).
        * **4. Abertura Autônoma e Gestão Validada no Sandbox**:
          - Execução validada em tempo real com abertura de ordens e stops posicionados rigorosamente abaixo da entrada em LONG.

41. **[V157-ANTI-DUPLICATION-IDEMPOTENCY-SHIELD] Trava Anti-Duplicidade Rígida, Idempotência de Ordens e Concorrência de Execução** (2026-10-15):
    - **Diagnóstico da Duplicação Concorrente**:
        * Ordens duplicadas podiam ocorrer quando comandos manuais ou assíncronos disparavam a varredura (`scan_and_execute_autonomous`) no mesmo instante em que o loop do backend (`laya_autonomous_loop`) executava seu ciclo periódico.
        * Ambos consultavam `active_trades == 0` antes do commit de persistência, abrindo ordens duplicadas simultâneas para o mesmo par no SQLite e refletindo múltiplos cards no Cockpit.
    - **As 4 Camadas de Proteção Implementadas**:
        * **1. Trava Anti-Duplicidade Atômica no Banco de Dados (`backend/services/database_service.py`)**:
          - Antes de qualquer inserção com status `ACTIVE`, o método `save_sandbox_trade` consulta as ordens ativas existentes e rejeita qualquer inserção cujo símbolo ou moeda base (`base_coin`) já possua uma ordem aberta.
        * **2. Lock Assíncrono de Varredura e Filtragem de Ativos Ativos (`backend/app/services/laya_router_service.py`)**:
          - Inicializado `self._scan_lock = asyncio.Lock()` garantindo que nenhuma execução paralela de varredura ocorra simultaneamente.
          - Normalização de `active_symbols` para contemplar tanto o ID canônico (`FET-USDT-SWAP`), par compacto (`FETUSDT`) quanto a moeda base (`FET`), eliminando candidatos ativos da lista de elegíveis.
        * **3. Deduplicação Rígida na Rota de Slots do Cockpit (`backend/routes/trading.py`)**:
          - No endpoint `GET /api/slots`, filtro `seen_slot_keys` garante defesa em profundidade, impedindo que a UI exiba mais de 1 slot por moeda base mesmo sob qualquer resquício histórico.
        * **4. Blindagem de Caminho Absoluto do SQLite Local**:
          - O fallback do SQLite agora resolve o caminho absoluto do arquivo `backend/local_sniper.db` a partir de `__file__`, eliminando a criação acidental de bancos paralelos na raiz.

42. **[V158-ELITE-50-UNIVERSE-AND-HIGH-THROUGHPUT-FUNNEL] Cesta Oficial de 50 Ativos de Elite Institucional, Funil em 3 Estágios e Farol Macro do Bitcoin** (2026-10-15):
    - **Diagnóstico do Afunilamento e Infiltração de Memecoins**:
        * Embora o sistema possuísse o mapeamento de 489 contratos USDT-SWAP da OKX, a Laya operava com uma trava de `limit=12`, mantendo a frota restrita a poucas moedas repetitivas.
        * A ordenação pura por volume inseria memecoins e tokens microscópicos (`FARTCOIN`, `PENGU`, `TRUTH`, `WAL`, `RSR`), que violam o perfil de trading institucional do sistema.
        * A telemetria do Bitcoin ficava com variação zerada (`0.0%`) porque `BTCUSDT` não estava na lista de pares processados do batch de tickers, permitindo que a Laya comprasse faca caindo (`NEAR`, `FET`) em dias de sangria de mercado.
    - **As 4 Soluções Estruturais Implementadas**:
        * **1. Cesta Canônica de 50 Ativos de Elite Institucional (`backend/app/services/okx_universe_service.py`)**:
          - 50 ativos distribuídos estrategicamente: L1s (15), L2s (8), DeFi & Oráculos (12), IA & Big Data (10), Gaming & Web3 (5).
          - Bloqueio rígido de memecoins, tokens de zoeira, derivativos sintéticos e ativos com preço $< $0.05.
          - Requisito de volume diário $> $3M USD.
        * **2. Funil de Alta Vazão em 3 Estágios (`backend/app/services/laya_router_service.py`)**:
          - *Estágio 1*: 1 única requisição HTTP em batch (`GET /api/v5/market/tickers`) captura preços e variações dos 50 ativos e do Bitcoin simultaneamente (100ms).
          - *Estágio 2*: Coleta de métricas profundas (Klines H1, Flow Radar e Funding) com semáforo de concorrência (`asyncio.Semaphore(10)`).
          - *Estágio 3*: Deep dive com o modelo neural Kronos focado apenas nos top candidatos qualificados.
        * **3. Farol Macro do Bitcoin (Trend Alignment Shield)**:
          - Inclusão mandatória de `BTCUSDT` no lote de tickers.
          - Quando o BTC estiver em tendência baixista (`btc_trend_bias < -0.3%`), compras (LONG) de reversão à média (`LAYA_DVWAP_REVERSION`) são vetadas, autorizando apenas operações vendidas (SHORT) a favor do fluxo.
        * **4. Persistência no Segundo Cérebro (RAG)**:
          - Documentado em `vault_galaxy/strategies/elite_50_universe_and_funnel.md` para indexação em tempo real pelo RAG e memória soberana.

43. **[V161-UNSTRANGLED-ASYMMETRIC-PAYOFF-AND-UNIFIED-RESET] Trailing Stop Desestrangulado, Simetria Direcional e Unificação Atômica de Reset** (2026-10-18):
    - **Eliminação do [V148-TP1] Estrangulador**: Removida a liquidação de 50% a +8% ROI que travava posições vitoriosas em míseros +$3.30. Posição agora corre 100% com Breakeven a +10% e Trailing de 65% do pico a partir de +14% ROI, permitindo capturas assimétricas de +60% a +73% (ex: PENDLE, FET, TIA).
    - **Reset Atômico da Banca (SSOT)**: Unificação dos endpoints `/api/sandbox/reset-all` e `/api/banca/reset` com purga síncrona do SQLite, memória RAM do broker OKX e instâncias de cache. Botão da UI com feedback instantâneo de processamento.

44. **[V162-TRIAD-SHIELDING-AND-BTCD-DRAINAGE-VETO] Tríade de Blindagem Institucional e Veto Soberano por Dominância do BTC** (2026-10-19):
    - **Veto Implacável por Dominância do BTC (BTC.D)**:
        * Quando o BTC estiver no verde (>= +0.3%) com dominância elevada (>= 59.0% ou subindo), o regime `BTC_DRAINAGE` veta 100% dos SHORTs em altcoins, impedindo que o motor seja estopado no vácuo de alta do Bitcoin.
        * Se a dominância for >= 58.0% em mercado lateral, SHORTs também são vetados preventivamente caso o BTC esteja positivo (> 0.2%).
    - **Circuit Breaker Global Anti-Tilt**:
        * Rastreador rolante de perdas. 3 stops consecutivos em <= 90 minutos ativam congelamento geral de novas entradas por 45 minutos (2.700s), protegendo a banca contra drawdowns em cascata.
    - **Descorrelação Setorial entre os 4 Slots**:
        * Divisão dos ativos em 5 clusters canônicos (`L1_BLUECHIP`, `L2_ROLLUPS`, `DEFI_ORACLE`, `AI_DEPIN`, `MEME_SPEC`). Teto estrito de no máximo 2 posições ativas do mesmo cluster.
    - **Confirmação de Agressão / CVD no Suporte e Resistência**:
        * Toques em suportes H1 com agressão vendedora violenta (`taker_sell_ratio >= 1.40x`) são vetados por faca caindo. Toques em resistências com agressão compradora (`taker_buy_ratio >= 1.40x`) são vetados por pressão compradora de topo.
    - **Validação Empírica**:
        * 100% de aprovação na suíte de testes `pytest backend/tests/test_stop_loss_cap.py` (12 testes passando).

45. **[V165-UNIVERSAL-ENCRYPTOS-PRECISION] Screener Universal de 507 Pares OKX, Motor de Precisão de Contratos, RAG Semântico Blueprints 01-09 e MCP 2.x Bridge** (2026-10-23):
    - **Screener Universal de 507 Pares Perpétuos OKX**:
        * Expansão da frota analisada de 50 para os 507 contratos ativos da OKX, calculando `1c_exp` (explosão algorítmica) e `1c_range` (canal H1).
    - **Motor de Precisão & Quantização Inviolável (`OKXUniverseService`)**:
        * Resolução exata de `tickSize` e `lotSize` da OKX via `format_price_by_tick` e `quantize_order_contracts`, eliminando ordens rejeitadas por granularidade.
    - **Segundo Cérebro RAG Indexando Blueprints 01-09**:
        * Indexação semântica completa de todos os blueprints arquiteturais em `docs/blueprint/` para consulta via RAG e assistentes inteligentes.
    - **Bridge Nativa MCP 2.x com 10 Ferramentas Registradas**:
        * Integração Starlette em `/mcp/sse` e `/mcp/tools` para interoperabilidade total de IA.

46. **[V166-UNIVERSAL-ALT-PUMP-CALIBRATION] Tríplice Confluência Alt Pump Ignition, 8 Slots Day Trade (1H) e Buffer Estrutural Anti-Violinada** (2026-10-23):
    - **Sensor Institucional de Alt Pump Ignition (`evaluate_alt_pump_ignition`)**:
        * Disparo de prioridade máxima quando confluem: Queda da Dominância do BTC (`dominance_trend == "FALLING"`, `altcoin_climate == "ALTCOIN_EXPANSION"` ou `btc_dominance < 56.5%`), Descolamento Estatístico Pearson com BTC (`correlation < 0.45` em 15h) e Robôs de Market Maker Ativados (`1C-EXP >= 70.0` e `bot_ignition == True`).
        * Bônus tático de +25 pontos na esteira de triagem e prioridade primária de slot em `eligible.sort()`.
    - **Expansão para 8 Slots Day Trade (1H) com Margem de $100 ($800 Alocado)**:
        * 8 slots simultâneos permitindo ampla diversificação de fluxo nos 507 pares, com limite de 3 slots por cluster setorial.
    - **Buffer Estrutural Anti-Violinada (Stop Loss H1)**:
        * Respiro mínimo de 1.8% a 2.8% além das bordas de resistência e suporte H1, com Sanity Gate ajustado para mínimo de 1.8% e máximo de 3.5% de preço.
    - **Filtro de Rejeição de Fluxo (Anti-Entrada Prematura)**:
        * Veto de shorts se houver pressão compradora persistente no topo (`taker_buy_ratio >= 1.25x`) e veto de longs se houver absorção vendedora no fundo (`taker_sell_ratio >= 1.25x`).
    - **Interface Cockpit Atualizada**:
        * Badge dourado de precisão vetorial `ALT IGNITION` exibido em tempo real nas posições disparadas pela tríplice confluência.

47. **[V174-ENCRYPTOS-LIQUIDITY-ZONES] Motor de 3 Zonas de Liquidez, Heatmap O(1) e Régua Tática no Cockpit 360** (2026-10-27):
    - **Máquina de Estados de 3 Zonas (classify_liquidity_lifecycle)**:
        * Implementada em coinglass_heatmap_service.py governada pela distância até o bolsão de liquidao dominante:
            1. **ZONA 1 (HUNT - Atração Ativa)**: Distância >= 1.5% -> Entrada a favor do ímã permitida (alvo no bolsão).
            2. **ZONA 2 (DEAD_ZONE - Veto de Entrada)**: Distncia entre 0.3% e 1.5% -> Veto total de novas entradas para impedir compras atrasadas no topo/fundo.
            3. **ZONA 3 (EXHAUSTION - Varredura & Reversão)**: Distncia < 0.3% -> Gatilho de reversão pós-varredura institucional condicionado a pavio de absorção >= 30% (TICK_REJECTION_INDEX).
    - **Régua Tática e Stepper Dinmico na UI da Laya**:
        * Rgua vetorial de 3 segmentos renderizada diretamente no canvas de alta resolução Retina.
        * HUD Chip expandido no topo esquerdo do gráfico com vetor de liquidao, badge da zona atual e ação recomendada em tempo real.
        * Stepper de 3 estágios (1. CAÇADA ▶ 2. VETO ▶ 3. SWEEP) sincronizado na barra de título do gráfico.
    - **Telemetria Instantânea em Memória (< 3ms)**:
        * Endpoint /api/v1/hermes/laya/360-telemetry devolvendo o bloco canônico liquidations.lifecycle.

48. **[V175-WS-DYNAMIC-SYNC-IMMEDIATE-PRICE-GUARD] Sincronização Dinâmica WebSocket, Guarda Imediata de Stop e Filtros de Pullback** (2026-10-28):
    - **Sincronização Dinâmica WebSocket (`okx_ws_public_service.sync_topics`)**:
        * Toda ordem ativa no Sandbox ou em REAL é automaticamente inscrita no WebSocket público da OKX durante o loop de monitoramento de 1 segundo.
        * Elimina chamadas REST síncronas para ticker no loop de inspeção, neutralizando erros de HTTP 429 e latência de rede.
        * Resilient fallback: caso o preço em tempo real retorne 0.0, o sistema recorre ao cache local de preços (`_last_prices`), impedindo o congelamento de ordens com `ACTION=SKIP`.
    - **Guarda Imediata de Preço de Stop (RAM O(1) Sub-5ms)**:
        * Implementada em `sandbox_service.py` (`[V175-IMMEDIATE-PRICE-GUARD]`): se `direction == LONG` e `current_price <= stop_loss`, ou se `direction == SHORT` e `current_price >= stop_loss`, `stop_hit` é acionado imediatamente em memória.
        * Garante execução atômica do Trailing Stop e Stop Loss sem depender de requisições de rede secundárias no momento do toque.
    - **Filtro de Pullback Intra-Range & Rejeição Mínima de 25%**:
        * Em regime `MEAN_REVERSION` (ADX < 20), proibidas entradas cegas a mercado:
            - `SHORT`: Exige que o preço esteja na metade superior da consolidação (`c_range >= 50%` ou `price >= vwap`), vetando entradas vendidas estritamente no fundo do range (`c_range < 35%`).
            - `LONG`: Exige que o preço esteja na metade inferior da consolidação (`c_range <= 50%` ou `price <= vwap`), vetando compras no topo do range (`c_range > 65%`).
        * Rejeição mínima de pavio em 5M mantida em 25% (`wick_ratio >= 0.25`), garantindo confirmação estrutural do fluxo contra o bolsão de liquidez.

49. **[V176-BILATERAL-SPIKE-GUARD] Auditoria Bilateral de Volume Institucional de 3x em H1 (Anti-Pump & Anti-Dump)** (2026-10-28):
    - **Auditoria de Volume Anômalo (Spike >= 3.0x & Direção)**:
        * Em `laya_router_service.py`, calcula a razão de volume em relação à média das últimas 10 velas (`vol_ratio = max_recent_vol / avg_hist_vol`).
        * Detecta a direção da vela do spike: `BULLISH` (vela verde, compradores ativos) ou `BEARISH` (vela vermelha, vendedores ativos).
    - **Proteção Bilateral em Caçadas de Liquidez (`LAYA_LIQUIDITY_HUNT`)**:
        * **Veto Anti-Pump (SHORT)**: Proibido abrir SHORT se `bot_ignition == True`, `1c_exp >= 70.0` ou se houver volume spike $\ge 3	imes$ de alta (`BULLISH`).
        * **Veto Anti-Dump (LONG)**: Proibido abrir LONG se houver volume spike $\ge 3	imes$ de baixa (`BEARISH`) ou se o preço estiver esticado abaixo da VWAP ($\le -6\%$), impedindo compra de faca caindo.
    - **Trava de Disparo na Lista de Elegíveis (`eligible`)**:
        * Bloqueio global antes do envio da ordem:
          - Se `direction == SHORT` e `is_pump_ignition == True`, ordem descartada.
          - Se `direction == LONG` e `is_dump_ignition == True`, ordem descartada.

50. **[V177-COMPOUND-MILESTONE-LADDER] Dimensionamento Dinâmico em Degraus de $1.000 (Abordagem B)** (2026-10-28):
    - **Fórmula da Escadinha de Milestones (Juros Compostos Anti-Martingale)**:
        * Em `laya_router_service.py`, a margem por slot escala dinamicamente a cada $1.000 de saldo realizado unificado:
          $$\text{milestone} = \max\left(5, \, \lfloor \frac{\text{realized\_balance}}{1000} \rfloor\right) \times 1000$$
          $$\text{margin} = \text{milestone} \times 0.01 = \frac{\text{milestone}}{1000} \times 10.0$$
        * Escala transparente para auditoria do operador no Cockpit:
            - $9.000 a $9.999: Margem de $90.00 por slot.
            - $10.000 a $10.999: Margem de $100.00 por slot.
            - $11.000 a $11.999: Margem de $110.00 por slot.
            - $12.000 a $12.999: Margem de $120.00 por slot.
            - $15.000 a $15.999: Margem de $150.00 por slot.
            - $20.000 a $20.999: Margem de $200.00 por slot.
    - **Invariante de Risco Estritamente Constante (8.0% Total)**:
        * Em qualquer nível da escadinha, a exposição nocional máxima somando os 8 slots é rigorosamente 8.0% do capital de milestone ($8 \times \text{margin} / \text{milestone} = 0.08$).
    - **Cálculo Baseado em Saldo Realizado (Never on Floating)**:
        * Apenas lucros encerrados incrementam o degrau de margem. Oscilações de PnL flutuante não expandem posições prematuramente.
    - **Piso de Segurança Inviolável ($50.00)**:
        * Garante conformidade técnica com o lote mínimo (`minSz` e `lotSz`) da OKX mesmo em drawdowns profundos.




51. **[V177-SOVEREIGN-FLEET-PURGE] Purge de 18 Agentes Legados e Unificação Soberana na Laya & Hermes** (2026-10-28):
    - **Extirpação de Código Zumbi (-8.169 linhas)**:
        * 18 arquivos de agentes legados deletados de `backend/services/agents/`: `captain.py`, `fleet_audit.py`, `bankroll_guardian.py`, `ambush.py`, `execution_auditor.py`, `flash_agent.py`, `jarvis_brain.py`, `librarian.py`, `librarian_auditor.py`, `macro_analyst.py`, `market_data.py`, `onchain_whale_watcher.py`, `oracle_agent.py`, `quartermaster.py`, `sentiment_specialist.py`, `slot_operator.py`, `trade_analyst.py`, `whale_tracker.py`.
    - **Desarmamento de 17 Loops de Background Paralelos**:
        * Desativados em `backend/main.py` todos os loops de polling arcaicos que concorriam com o motor da Laya e causavam timeouts de conexões.
    - **Desacoplamento Universal de Rotas**:
        * Todas as rotas de backend (`market.py`, `chat.py`, `system.py`, `admin.py`, `sandbox.py`, `backtest_routes.py`) e serviços core (`bankroll.py`, `sandbox_service.py`, `signal_generator.py`) agora roteiam deterministicamente através dos motores soberanos `LayaRouterService` e `HermesAgent`.
    - **Ecossistema Soberano Final**:
        * Apenas 6 componentes soberanos compõem o sistema: `LayaRouterService`, `KronosScorer`, `Flash Agent / SandboxService`, `OpenVikingContextService`, `HermesAgent` (RAG & MCP), `Plutus / DatabaseService`.

52. **[V177-TELEMETRY-OBSERVATORY-UPLOT] Observatório Widescreen de Telemetria de Infraestrutura & Consciência Laya (uPlot 60 FPS)** (2026-10-28):
    - **Layout Widescreen Ultrawide Modular em 3 Colunas (100vw Full-Bleed)**:
        * Em `frontend/observatory.html` e `backend/app/static/observatory.html`, superada a visualização vertical legada através de um grid CSS responsivo de 3 colunas (`310px 1fr 340px`) com altura calculada (`height: calc(100vh - 86px)`) e zero scrollbars de página.
        * **SubHUD Tático**: Farol Macro BTC (preço e variação 24h), Regime & ADX da Laya Soberana, Throughput em tempo real (ticks/s), Ping OKX (ms) e status de Circuit Breaker Anti-Slippage.
    - **Conexão Orgânica Cockpit & Consciência Laya**:
        * **Coluna 1 (Painel de Custódia em Tempo Real)**: Cards vivos dos 4 slots ativos do Cockpit (`POL`, `SOL`, `TIA`, `UNI`) espelhando alavancagem 15x, preço de entrada, stop loss dinâmico e PnL flutuante ($ e %) atualizado a cada 1 segundo.
        * **Coluna 2 (Laboratório de 3 Gráficos uPlot Canvas)**:
            1. *Latência WebSocket OKX vs Vazão de Fluxo*: Escala dupla (ms no eixo esquerdo e ticks/s no direito) com detecção de picos de rede.
            2. *Performance de Varredura da Laya vs Latência Neural*: Duração do ciclo de varredura dos 507 pares em segundos versus tempo de inferência da Laya.
            3. *Curva Contínua de Patrimônio Líquido (Tick-a-Tick)*: Reflete a banca realizada do Sandbox consolidada somada à flutuação tick-a-tick dos trailing stops de custódia.
        * **Coluna 3 (Sismógrafo de Titãs Laya & Vitais Uvicorn)**: Tabela de radar dos 10 Titãs da Laya (Postura `BEARISH/BULLISH/NEUTRAL`, `1C-EXP` e Robôs ON/OFF) combinada com métricas de CPU, RAM e contadores de amostragem do Uvicorn.
    - **Integração no Shell Universal (`shell.js`)**:
        * Link `OBSERVATÓRIO (TELEMETRIA uPlot)` injetado no drawer lateral (`app-sidebar`), no header superior para desktop (`desktop-nav`) e na barra de navegação mobile através de `frontend/shell.js` e `backend/app/static/shell.js`.
    - **Motor de Telemetria Backend (`TelemetryService`)**:
        * Implementado em `backend/app/services/telemetry_service.py` com buffers circulares (deques de 3.600 amostras a 1s = 1 hora contínua de memória).
        * Circuit breaker de latência: se o ping da OKX ultrapassar 150ms, alerta de risco de slippage é propagado para o motor de execução.
        * Fallback resiliente para contadores de CPU/RAM em plataformas sem o pacote opcional `psutil`.

53. **[V177-AUTONOMOUS-HERMES-EXECUTIVE-AUDIT-SKILL] Protocolo de Auditoria Forense Autônoma e Briefing Executivo sem Prints** (2026-10-28):
    - **Metodologia de 4 Camadas (Processo, Caixa, Prova, Conserto)**:
        * Em `.agents/skills/auditoria_executiva_mesa_hermes/`, implementada a arquitetura autônoma que liberta o operador humano da necessidade de enviar prints de tela para obter diagnósticos da mesa.
        * **Processo (`SKILL.md`)**: Roteiro de 5 passos na ordem canônica do olhar do operador: Banca Soberana -> Radiografia de Custódia -> Autópsia Forense de Fechamentos -> Infraestrutura e Reflexo da Laya -> Veredito do Estado da Arte.
        * **Caixa de Ferramentas (`arquivos/`)**: Template rígido parametrizado com lacunas entre colchetes (`modelo-briefing-executivo.md`), regras estritas de tom (`regras-de-tom-e-formato.md`) com zero emojis e veto absoluto a adjetivos vagos.
        * **As 7 Provas Factuais do Estado da Arte**: O Hermes só pode assinar *"Mesa 100% estável e prosperando. Zero intervenção necessária"* se comprovar matematicamente no centavo contra logs e SQLite: Prova da Banca Realizada, Prova da Margem por Slot ($100), Prova Anti-Hedge, Prova do Never Give Back, Prova da Quarentena de 2h, Prova de Latência OKX (< 120ms) e Prova de Contrato Físico (`ctVal`).
        * **Diário de Lições e Evolução Contínua (`notas.md`)**: Registro dos 4 fantasmas do passado blindados permanentemente contra regressões.
    - **Mapeamento OpenViking & RAG**:
        * A Skill é mapeada deterministicamente no sistema de arquivos virtual em `viking://agent/skills/auditoria_executiva_mesa_hermes`.
        * Indexação semântica no RAG (`RAGService`) com 425 chunks ativos e sincronização episódica com o Obsidian Vault (`vault_galaxy/journal/2026-10-28.md`).
    - **Padronização Widescreen da Página Plutus (`/plutus`)**:
        * Removido cabeçalho estático legado e injetado o Shell Universal (`shell.js`) com Drawer Lateral e Net Worth em tempo real.
        * Layout expandido para 100% Full-Bleed sem barras pretas laterais em monitores ultrawide.


54. **[V183-BREAKEVEN-10-AND-LEVERAGE-15-20X] Calibração de Breakeven a +10% ROI, Time-Stop Universal e Alavancagem 15x/20x** (2026-11-01):
    - **Breakeven Antecipado em +10.0% ROI (sandbox_service.py & order_projection_service.py)**:
        * O gatilho de ativação do Breakeven foi calibrado de +16.0% para **+10.0% ROI**, movendo imediatamente o stop para **+2.5% ROI** (garantindo o pagamento integral das comissões OKX e lucro líquido positivo).
        * A 15x de alavancagem, +10.0% ROI exige apenas 0.66% de variação de preço a favor, blindando o capital contra reversões institucionais precoces.
        * O trailing stop Never Give Back preserva 100% da capacidade de surfar tendências longas (escadinha de 50% do pico de lucro até 1.000% ROI).
    - **Time-Stop Universal sem Brechas de Retorno**:
        * Removida a trava nd max_roi < 6.0. Qualquer operação com mais de 45 minutos de duração que esteja operando em prejuízo ($\le -8.0\%$ ROI) é liquidada imediatamente a mercado (CLOSED_TIME_STOP), eliminando o sangramento lento de posições exauridas.
    - **Restauração de Alavancagem 15x Padrão e 20x com Stop Curto (laya_router_service.py)**:
        * Alavancagem padronizada em 15x para ordens padrão e 20x para operações de alta convicção institucional (score >= 95).
        * Distância de stop inicial calibrada para 1.2% a 1.4% de variação de preço (stop ROI máximo entre -18% e -20%), mantendo a integridade da banca mesmo em stops cheios.


55. **[V184-OPTIMAL-BREAKEVEN-8-AND-PROFIT-STOP-3] Calibração Ótima de Breakeven em +8.0% ROI e Stop Garantido em +3.0% ROI** (2026-11-02):
    - **Gatilho de Breakeven em +8.0% ROI (`sandbox_service.py` & `order_projection_service.py`)**:
        * Redução do gatilho de +10.0% para **+8.0% ROI** (+0.40% de movimento de preço a 20x ou +0.53% a 15x).
        * Garante que impulsos de alta que atingem +8% a +9.5% ROI (como a anomalia do CORE a +9.43%) ativem imediatamente a blindagem de capital.
    - **Stop Móvel Garantido em +3.0% ROI**:
        * Stop ajustado de +2.5% para **+3.0% ROI** ao disparar o Breakeven.
        * Absorve integralmente os custos operacionais da OKX (Taker 0.05% abertura + 0.05% fechamento + slippage 0.03% = 2.60% ROI a 20x) e ainda gera um retorno líquido positivo de **+0.40% na banca**, garantindo lucro real mesmo em reversões de mercado.


56. **[V185-SCORE-85-EXPANSION] Ativação Operacional em Score >= 85% e Alavancagem Proporcional** (2026-11-02):
    - **Abertura do Filtro de Entrada (`laya_router_service.py`)**:
        * Redução do limiar mínimo de execução autônoma de `score >= 90` para **`score >= 85`** (`MIN_ENTRY_SCORE = 85`).
        * Aumenta a vazão e amostragem de altcoins em aceleração institucional inicial nos 507 contratos OKX.
    - **Blindagem Matemática Integrada**:
        * Protegido pelo Breakeven V184 (+8.0% ROI / Stop em +3.0% ROI) e Time-Stop de 45 minutos.
        * **Alavancagem Proporcional**:
            - Score 85 a 94: operam em **15x** (seguro e elástico, Breakeven com +0.53% de preço).
            - Score >= 95: operam em **20x** (convicção máxima da Laya, Breakeven com +0.40% de preço).


57. **[V186-PARIDADE-EXECUCAO-STOP-OKX] Paridade Estrita de Execução de Stop Loss e Trailing Stop no Sandbox** (2026-11-02):
    - **Eliminação de Slippage Duplo e Preço de Polling Atrasado (`sandbox_service.py`)**:
        * Correção do cálculo de saída em `stop_hit`: ao violar o stop móvel ou de perda, a execução base ocorre exatamente no `stop_price` configurado na exchange (`exit_price = stop_price if stop_price > 0 else current_price`), espelhando a ordem condicional nativa da OKX.
        * O slippage a mercado e as comissões Taker (0.05% abertura + 0.05% fechamento + 0.03% slippage) continuam sendo rigorosamente deduzidos na fórmula matemática `operational_cost_roi`.
        * Elimina a anomalia onde ordens protegidas em Breakeven (+3.0% ROI) fechavam artificialmente negativas devido ao intervalo de amostragem (polling) do WebSocket.
    - **Evidência Empírica TDD**:
        * Teste unitário automatizado em `tests/test_v186_stop_execution_parity.py` validado com 100% de sucesso.



58. **[V187-FUSAO-AGUIA-ENCRYPTOS-SOBERANA] Fusao Soberana Aguia (Bruno Aguiar) + Encryptos (Phenix)** (2026-11-03):
    - **Metodologia Bruno Aguiar (Aguia Spread)**:
        * **Timeframe Soberano 2H**: SMA 8 (Branca) vs SMA 21 (Amarela). Alinhamento ou cruzamento no 2H define a direcao macro inegociavel da tendencia.
        * **Gatilho de Entrada 5M**: Confirmacao na vela de 5 minutos a favor da direcao sem veto do Guardiao de Microestrutura.
        * **Gestao de Risco de Alta Alavancagem e Margem Cruzada**: 50x de alavancagem em Margem Cruzada (Cross Margin), alocando estritamente **0.6% de margem por operacao** ($60 numa banca de $10.000).
        * **10 Slots Operacionais ($600 = 6% de risco total da banca)**: 94% ($9.400) do capital permanece 100% liquido como colchao de colateral unificado, empurrando o preco de liquidacao para 40% a 60% de distancia do preco de entrada.
        * **Breakeven Ultra-Rapido a 50x**: Com apenas +0.16% de movimento de preco favoravel, a operacao atinge +8.0% ROI e ativa o Breakeven (+3.0% ROI garantido), tornando o trade livre de risco imediatamente.
    - **Filtro Antifraude Encryptos (Phenix)**:
        * O setup so e acionado se houver confluencia com fluxo institucional real: `1C-EXP >= 70` ou Robos Institucionais Ligados (`bot_ignition = True`) e Farol do BTC favoravel. Elimina whipsaws e entradas em moedas sem liquidez.
    - **Telemetria Laya 360 (`/laya`) e Cockpit (`/`)**:
        * Painel visual dedicado exibindo: SMA 8 2H, SMA 21 2H, Status de Cruzamento/Alinhamento, Gatilho 5M e Racional de Fusao.
    - **Validacao Empirica TDD**:
        * Teste unitario e de confluencia automatizado em `tests/test_aguia_encryptos_fusion.py` com 6 testes aprovados com 100% de sucesso.


59. **[V187.2-UNIFIED-BRUNO-PHENIX-RISK-ENGINE] Gestao de Risco Unificada com Alavancagem Maxima da Moeda e Margem 0.6%** (2026-11-03):
    - **Alavancagem Maxima Permitida pela OKX com Teto em 50x**:
        * A alavancagem para qualquer operacao (seja Fusao direta ou antecipacao por Cacada de Liquidez / Rompimento H1) e calculada dinamicamente: `leverage = min(50.0, okx_universe_service.get_max_leverage(sym))`.
        * Se o ativo permite ate 10x, 20x ou 25x (como LAB, AKE, BEAT), abre na alavancagem maxima dele; se permite 50x, 75x ou 100x (como SOL, XRP, SUI, DOGE, PEPE), crava no teto de 50x.
    - **Margem Fixa Padronizada de 0.6% ($60 em Banca de $10.000)**:
        * Todas as ordens operam com alocacao estrita de 0.6% da banca por slot, permitindo ate 10 slots simultaneos (6% de risco total da banca em Margem Cruzada e 94% de colateral liquido).
    - **Sinergia Antecipacao (Phenix) + Confirmacao (Bruno Aguiar)**:
        * A Laya pode antecipar a entrada pelo Ima de Liquidez ou Gatilho 5M antes do cruzamento da SMA 2H; quando o Breakeven protege o trade a risco zero, o trade surfa a grande tendencia macro quando as SMAs 2H finalmente cruzam.


60. **[V187.3-COCKPIT-SMA-2H-UI-ALIGNMENT] Alinhamento Visual do Cockpit: SMA 8/21 nos 4 Gráficos, Timeframe 2H e Monitor de Banca Unificado** (2026-11-03):
    - **Médias Móveis Visuais nos 4 Gráficos Nativos (LightweightCharts)**:
        * Implementação das linhas de SMA 8 (Branca `#FFFFFF`, largura 1.5) e SMA 21 (Amarela `#F0B90B`, largura 1.5) com cálculo vetorial instantâneo (`computeSMA`) renderizado em todos os 4 gráficos (G1, G2, G3, G4) em modos Solo, Dual e Quad.
        * Atualização em tempo real via WebSocket OKX (`candle2H` / canal ativo) mantendo as médias dinamicamente atualizadas a cada tick de preço.
    - **Timeframe 2H Integrado no Cockpit e Backend**:
        * Inclusão do seletor `2H` nos cabeçalhos dos 4 gráficos (`data-tf="120"`).
        * Rota `/api/candles` em `backend.main` mapeada com suporte nativo a `bar=2H` para OKX SWAP e Binance Fallback (`2h`).
    - **Card de Banca Soberana e Gestão de Risco Alinhado ao Sistema Bruno + Phenix**:
        * Badge: `ATÉ 50X CRUZADA` (substituindo o antigo `15X ISOLADA`).
        * Monitor de Slots: `0 / 10 ATIVOS` com subtítulo dinâmico `(MAX $600 • $60/ORDEM • 6% RISCO | 94% LIVRE)`.
        * Teto de Risco da Mesa: `RISK: 0% / 6%` (substituindo o teto genérico de 40%).

61. **[V197-CROSS-MARGIN-SWING-PARADIGM-50X] Paradigma Soberano de Margem Cruzada 50X, Lotes 4+4 e Alvo Chão 300%** (2026-11-06):
    - **Invariante de Margem Cruzada Soberana (Cross Margin)**:
        * Toda e qualquer operação no 1Crypten opera estritamente em **Margem Cruzada (Cross Margin)** com banca base de **$100.000,00**.
        * A banca inteira é o colateral garantidor; é terminantemente proibido calcular limites de stop baseando-se em liquidação de margem isolada (1.8% a 50X). O stop pertence exclusivamente à resistência técnica estrutural (SMA 21 no 2H/4H ou topo anterior), permitindo folga de 2% a 4% com respiro livre de 12h a 24h sem encerramento prematuro.
    - **Regra Soberana dos Lotes 4 + 4**:
        * **Margem Fixa por Ordem**: $1.000,00 USD (50X Cruzada = Volume nocional de $50.000,00 USD por contrato).
        * **Lote 1 (Em Risco)**: Máximo estrito de 4 ordens abertas simultâneas com risco vivo (sem proteção). Risco máximo inicial da mesa: $4.000 (4% do capital).
        * **Lote 2 (Expansão até 8 Slots)**: Uma 5ª, 6ª, 7ª ou 8ª ordem só é liberada se ao menos uma das ordens anteriores atingir Breakeven (Risco Zero) ou Trailing Stop no Degrau 1 (+50% de ROI / +1.0% de preço a favor). Se houver 4 ordens desprotegidas, o motor emite `[VETO LOTE ATIVO]` e aguarda proteção antes de novas aberturas.
    - **Escadinha 50X Calibrada com Alvo Chão 300% (+$3,000.00)**:
        * *Degrau 1 (+50% ROI / +1.0% Preço)*: Stop Loss movido para o preço de Entrada (Breakeven - Risco Zero absoluto).
        * *Degrau 2 (+100% ROI / +2.0% Preço)*: Trailing Stop sobe e trava +40% de ROI (+$400.00).
        * *Degrau 3 (+150% ROI / +3.0% Preço)*: Trailing Stop sobe e trava +80% de ROI (+$800.00).
        * *Degrau 4 (+200% ROI / +4.0% Preço)*: Trailing Stop sobe e trava +120% de ROI (+$1.200.00).
        * *Degrau 5 (+300% ROI / +6.0% Preço - ALVO CHÃO)*: Stop sobe e trava +200% de ROI (+$2.000.00 garantidos no bolso), mantendo trailing ativado para surfar expansões de tendência de 4H (+500% a +800% ROI).
    - **Validação Empírica TDD**: Testes automatizados em `tests/test_cross_margin_swing_paradigms.py` validados com 100% de aprovação.


62. **[V198-LAYA-BTC-MACRO-BEAR-FILTER-AND-PULLBACK-PRECISION] Farol BTC Macro 2H e Entrada no Repique com Vela Fechada** (2026-11-06):
    - **Farol BTC Macro 2H (`VETO_FAROL_BTC`)**:
        * Leitura institucional contínua do Bitcoin no timeframe 2H via SMA 8 vs SMA 21 e inclinação de tendência.
        * Enquanto o BTC estiver em regime BEAR (SMA 8 < SMA 21 ou viés vendedor), compras de altcoin são expressamente vetadas (`VETO_FAROL_BTC`). Apenas vendas a favor da gravidade macro ou rompimentos com robôs de alta extrema comprovada (`alt_pump_ignition`) são autorizados.
    - **Entrada no Repique de Alta em Resistência (Pullback Precision)**:
        * Proibido vender fundo esticado: se o preço estiver afastado da média móvel no 2H, o trade é vetado por exaustão.
        * A Laya aguarda o repique do preço até a zona de teste da SMA 8 / SMA 21 ou resistência intraday no 30M.
        * **Gatilho de Vela Fechada e Volume Decrescente (30M)**: Exige candle de 30M fechado confirmando rejeição (não rompimento) com volume decrescente de compradores antes do disparo da ordem SHORT.
        * **Stop Loss Ancorado no Topo Estrutural**: O Stop Loss inicial é ancorado no maior entre a SMA 8 e a SMA 21 (SMA 21 no canal de baixa), com folga de 0.2% acima da resistência real, impedindo recálculos que rebaixem o stop para dentro da zona de ruído.
    - **Validação Empírica TDD**: Testes automatizados em `tests/test_laya_pullback_precision.py` validados com 100% de aprovação.


63. **[V199-MCP-SERVER-16-TOOLS-AND-NATIVE-BRIDGE] Servidor MCP Oficial FastMCP (SDK 1.x) com 16 Ferramentas Soberanas** (2026-11-06):
    - **Arquitetura do Bridge Nativo**:
        * Entrypoint: `backend/app/mcp/server.py` utilizando o framework oficial `FastMCP` (SDK 1.x).
        * Montado nativamente no FastAPI em `/mcp` sem necessidade de processo isolado ou sockets paralelos.
    - **Arsenal de 16 Ferramentas Registradas**:
        * Oráculos e Inteligência: `laya_evaluate_entry`, `laya_get_thought_stream`, `laya_get_candidates`, `kronos_predict_candles`, `hermes_audit_compliance`.
        * Liquidez e Mercado: `get_okx_orderbook_depth`, `get_okx_liquidity_zones`, `get_okx_funding_arbitrage`, `get_rubik_sentiment`.
        * Execução e Risco: `sandbox_open_trade`, `sandbox_close_trade`, `sandbox_get_unified_state`, `sandbox_set_stop_loss`, `emergency_flatten_all`.
        * RAG e Conhecimento: `hermes_query_rag`, `openviking_search_knowledge`.


64. **[V200-HERMES-RAG-AND-OPVIKING-KNOWLEDGE-INTEGRATION] Hermes RAG e OpenViking: Indexação Institucional Unificada** (2026-11-06):
    - **Rotas RAG (`/api/v1/hermes/rag`)**:
        * Endpoints de ingestão, busca semântica e auditoria de conformidade regulatória e operacional.
        * Vetorização de documentos de arquitetura, diários de bordo (`vault_galaxy/`), manuais de trading e diretrizes de risco.
    - **OpenViking Sovereign Memory**:
        * Base de conhecimento institucional permanente que armazena a verdade canônica do sistema (Margem Cruzada, Never Give Back, Lotes 4+4).
        * Elimina a perda de contexto operacional entre sessões de IA e assegura que nenhum agente execute cálculos sob premissas legadas.


65. **[V201-LAYA-NEURAL-FINETUNING-PIPELINE] Pipeline de Fine-Tuning Neural da Laya e Pesos Calibrados** (2026-11-06):
    - **Dataset Canônico de Decisões (`laya_decision_dataset.jsonl`)**:
        * Amostragem curada de decisões institucionais contendo features completas: ADX, Delta LSR, Distância SMA 8/21 2H, Regime BTC Macro, Volume Ratio e Alvo Chão.
    - **Treinador Automatizado (`laya_finetune_trainer.py`)**:
        * Script de regressão e calibração fina de pesos neurais gerando `laya_calibrated_weights.json`.
        * Alinha a função de perda (loss function) ao payoff assimétrico de 50X: alta penalização para falsos rompimentos em topos/fundos e recompensa máxima para pullbacks surfados até o Alvo Chão de 300%.

66. **[V214-SCRATCH-GUARD-REJECTION-SHIELD] Proteção contra Rejeição de Impulso Próximo ao Breakeven e Re-entry Inteligente** (2026-11-12):
    - **Diagnóstico da Zona Morta (Caso LINK -$491 e AVAX +25% devolvidos)**:
        * Identificado ponto cego entre 0% e +35% de ROI: quando o trade desenvolvia forte impulso (atingindo +20% a +34% de ROI) mas encontrava resistência antes dos +35% e revertia, o stop original continuava inalterado lá no fundo (-50% a -60%), transformando ordens vencedoras em prejuízos catastróficos.
    - **Mecanismo Scratch Guard (`SCRATCH_GUARD_REJECTION`)**:
        * Injetado no loop central de avaliação de stops (`sandbox_service.py`):
        * **Regra (Calibrada V215)**: Se `max_roi >= 20.0%` e o preço recuar para `current_roi <= 7.0%`, o motor eleva o stop loss imediatamente para **`+8.0% ROI`**.
        * Garante encerramento no verde com lucro líquido de +3.0% após abater ~5.0% de taxas e slippage da OKX (+$30 fixos por trade de $1.000 em 50X), transformando empates em ganhos reais e protegendo 100% do capital contra violinadas reversas.
    - **Tocaia de Re-entrada (Reset & Re-entry)**:
        * Em vez de aplicar a quarentena longa de 2 horas (7200s usada apenas para Stop Loss com perda), trades encerrados pelo Scratch Guard entram em quarentena tática curta de **5 minutos (300s)** para aguardar o término da vela de rejeição e o repique em suporte (SMA 21 no 30M/2H).
        * Quando o ativo reestabelecer o alinhamento técnico, a Laya re-entra com preço médio descontado e novo fôlego.

67. **[V216-SOVEREIGN-TELEMETRY-CLEAN] Telemetria em Tempo Real, Heartbeat 30s e Purga Canônica de Scalping Legado** (2026-11-14):
    - **Sinal de Vida em Tempo Real na Telemetria (`/telemetria`)**:
        * Heartbeat visual animado com contagem regressiva contínua de 30 segundos, exibição viva do stream cognitivo de pensamento da Laya com tags coloridas por regime/ação, status explícito do Farol BTC 2H (SMA 8 x 21) com permissão/veto direcional e composição viva da frota 2+2+2+2.
    - **Purga de Motores Legados**:
        * Extirpação completa de `sandbox_scalping_engine.py` (VWAP Sniper M1/M5) do ciclo de execução em favor da estratégia única vencedora `LAYA_PULLBACK_HUNTER_2H_30M`.

68. **[V217-DUAL-TIER-TITAN-ENGINE] Arquitetura Dual-Tier do Titan Engine: Grau 1 SMA8 Sniper vs Grau 2 SMA21 Sweep** (2026-11-15):
    - **Grau 1 (Sniper SMA8 - Linha Branca)**:
        * Disparo imediato no toque e rejeição na SMA 8 de 2H com confirmação de pavio no 30M e stop protegido além da SMA 21 (Linha Amarela).
    - **Veto Anti-Surge Smart Money (`VETO_SMART_MONEY_REPIQUE`)**:
        * Vetamento sumário caso a vela fure a SMA 8 com corpo direcional forte (> 40% sem pavio) buscando liquidez de stops retail na SMA 21.
    - **Grau 2 (Sniper SMA21 - Linha Amarela / Sweep de Liquidez)**:
        * Monitoramento da varredura na SMA 21 de 2H. A entrada ocorre na exaustão/sweep do topo da Linha Amarela com preço descontado e stop blindado acima da varredura.
    - **Trailing Gap Elástico de 50% de ROI**:
        * Ativado a partir de +100% de ROI (`trail_stop_roi = max(50.0, max_roi - 50.0)`), concedendo 1.0% de respiro livre no preço para buscar o Alvo Chão de +300% de ROI sem estrangulamento precoce.

69. **[V218-INSTITUTIONAL-DUAL-BREAKEVEN-45-60] Dual Breakeven Institucional (+45% Fricção OKX / +60% Soberano)** (2026-11-16):
    - **Degrau 1 (Breakeven Protetivo Fricção OKX $500k)**:
        * Dispara em **+45.0% de ROI** (+0.90% de preço a favor em 50X), travando o stop em **+18.0% de ROI** (+0.36% de preço a favor).
        * Cobre integralmente taxas taker (0.10%) e slippage real de livro (0.03% - 0.10% em nocionais de $500k), garantindo Risco Zero Real e saldo líquido positivo no cofre (+$300 a +$900).
    - **Degrau 2 (Breakeven Soberano Consolidado)**:
        * Dispara em **+60.0% de ROI** (+1.20% de preço a favor em 50X), travando o stop em **+30.0% de ROI líquido** (+$3.000,00 fixos no cofre).
        * Libera imediatamente novos slots de expansão na frota na regra 2+2+2+2.

70. **[V218-TITAN-UNIFIED-AUDIT-REPORTS] Unificação de Relatórios, Dossiê Forense e Atribuição Soberana ao Titan Engine** (2026-11-16):
    - **Dossiê Forense Institucional (`cockpit.html`, `cockpit_v2.html`, `mobile_app.html`)**:
        * Cabeçalho e comando tático formalmente atribuídos ao **TITAN ENGINE (TITAN 360)**, com a Laya Neural identificada estritamente como **Stream Cognitivo Neural (System 1)**.
    - **Sanitização de Histórico e Timelines**:
        * Histórico de eventos e flash timeline atualizados para registrar `"Titan Engine executou entrada..."` e `"[SWEEP & FLIP] Titan Engine executou reversão..."`.
        * Identificadores de trades atualizados de `laya_<timestamp>` para `titan_<timestamp>`.

71. **[V219-TITAN-LIQUIDITY-SNATCH-BTC-KEYZONES] Tática Liquidity Snatch Entry (Grau 2 Sweep) & Farol BTC Macro Key Zones** (2026-11-16):
    - **Tática Liquidity Snatch Entry (`laya_router_service.py`)**:
        * Veto a entradas afobadas na SMA 8 em repiques com ímpeto retail; o Titan Engine aguarda pacientemente a caçada aos stops além da SMA 21 (Linha Amarela).
        * Exigência de pavio de exaustão superior >= 28% no candle de 30M ou devolução bear, garantindo entrada no topo da varredura de liquidez.
        * Posicionamento de Stop Loss sniper com folga enxuta de 1.0% a 1.2% de preço logo acima da máxima do sweep, eliminando o calor da ordem e acelerando o alcance do Breakeven Protetivo (+45% ROI).
    - **Módulo Farol BTC Macro Key Zones (`laya_btc_specialist_service.py`)**:
        * Rastreamento dinâmico em tempo real de suportes e resistências estruturais de 4H/Diário ($65.000, $62.500, etc.).
        * Veto preventivo de vender fundo (`VETO_VENDER_FUNDO_SUPORTE_BTC`): proíbe novas ordens de venda em rompimento seco de altcoins quando o BTC estiver a <= 1.25% de um suporte macro institucional, exigindo obrigatoriamente o Grau 2 pós-sweep.
    - **Reset Limpo da Banca para $100.000,00 Pristine**:
        * Chamada canônica a `/api/sandbox/reset-all`, zerando histórico de ordens ativas anteriores e restaurando a banca de $100.000,00 USD para o início do novo ciclo.

---

## 15. Sistema OpenViking (`viking://`) Context Database Engine

O OpenViking é o sistema de arquivos virtual e banco de dados de contexto hierárquico do 1Crypten, projetado para conceder memória episódica, factual e procedural aos agentes de IA (Hermes, Antigravity, Claude Code, Cursor) eliminando alucinações e perda de contexto operacional entre sessões.

### 15.1 Arquitetura e Paradigma do Virtual Filesystem
O OpenViking mapeia toda a inteligência do sistema sob o protocolo `viking://`, organizado deterministicamente em três raízes canônicas:
- **`viking://resources/` (Conhecimento Factual & Arquitetura)**:
  - `viking://resources/architecture`: Mapeamento de `MASTER_ARCHITECTURE.md` e regras invioláveis.
  - `viking://resources/blueprints`: Especificações técnicas canônicas de `docs/blueprint/` (01 a 09).
  - `viking://resources/rules`: Regras da metodologia Superpowers e diretrizes de trading.
- **`viking://user/memories/` (Memória Episódica & Auto-Evolutiva)**:
  - `viking://user/memories/cases/`: Dossiês de casos reais de trades (desfechos, MFE, MAE, lições aprendidas).
  - `viking://user/memories/patterns/`: Catálogo de assinaturas gráficas, sweeps de liquidez e armadilhas de Smart Money.
  - `viking://user/memories/preferences`: Perfil de risco e preferências do operador da mesa.
- **`viking://agent/skills/` (Memória Procedural & SOPs)**:
  - `viking://agent/skills/`: Protocolos operacionais padrão de `.agents/skills/` (TDD, Debugging Forense, Auditoria Executiva Hermes, Verificação Pré-Conclusão).

### 15.2 Progressive Disclosure em Três Níveis (L0, L1, L2)
Para otimizar o uso do context window e garantir tempos de resposta ultrarrápidos, cada nó do OpenViking (`VikingNode`) expõe seu conteúdo em três níveis granulares:
1. **L0 (Executive Abstract — ~100 a 300 caracteres)**:
   - Resumo ultracompacto para tomada de decisão em frações de segundo. Utilizado em loops de alta frequência, verificações de guard rails e checagem de invariantes de risco.
2. **L1 (Operational Overview — ~1.000 a 2.000 caracteres)**:
   - Visão operacional consolidada. Contém parâmetros técnicos exatos, fórmulas, thresholds de breakeven, métricas de entrada/saída e regras táticas.
3. **L2 (Full Detail — Arquivo Completo)**:
   - Documento completo, código-fonte, evidências empíricas de teste, logs forenses e transcrições de execução.

### 15.3 Memória Auto-Evolutiva de Trading (Async Lesson Synthesis)
Ao fechar qualquer trade na OKX (seja por Breakeven, Trailing Stop, Alvo Chão, Time-Stop ou Stop Loss):
1. O evento é capturado assincronamente pelo serviço `openviking_context_service.py`.
2. O sistema calcula as métricas forenses da operação: Maximum Favorable Excursion (MFE), Maximum Adverse Excursion (MAE), tempo total de custódia, custos de fricção (taxas + slippage) e desvios em relação à projeção original.
3. Uma lição aprendida estruturada é gerada e gravada em dois destinos simultâneos:
   - **OpenViking Node**: Indexado em `viking://user/memories/cases/{trade_id}` para recuperação imediata por agentes.
   - **Obsidian Vault**: Persistido no diário de bordo executivo (`vault_galaxy/journal/YYYY-MM-DD.md`), construindo o histórico cognitivo permanente do sistema sem intervenção manual.

### 15.4 Endpoints da API OpenViking
| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/api/v1/hermes/viking/tree` | Retorna a árvore hierárquica completa do virtual filesystem `viking://` |
| `GET` | `/api/v1/hermes/viking/read` | Lê um nó específico por URI (`?uri=viking://...&level=0\|1\|2`) |
| `GET` | `/api/v1/hermes/viking/search` | Realiza busca semântica e por tags em nós indexados (`?query=...&level=1`) |
| `POST` | `/api/v1/hermes/viking/commit-lesson` | Grava uma nova lição ou síntese cognitiva diretamente no cofre de memórias |
| `POST` | `/api/v1/hermes/viking/sync` | Força a sincronização a quente entre o disco local e o grafo OpenViking |

---

## 16. Model Context Protocol (MCP 2.x) Bridge

O 1Crypten implementa suporte oficial e nativo ao **Model Context Protocol (MCP)**, permitindo que agentes de inteligência artificial locais e externos (Hermes, Claude Desktop, Antigravity, Cursor, n8n, AIOS) interajam diretamente com o motor de trading, risco, mercado e memória através de um conjunto tipado e seguro de ferramentas.

### 16.1 Arquitetura do Bridge e Montagem ASGI
- **Framework**: Implementado em `backend/services/mcp_bridge.py` utilizando `FastMCP` (SDK 1.x) com suporte retrocompatível para `MCPServer` (SDK 2.x).
- **Montagem Nativa**: Montado como uma sub-aplicação ASGI diretamente no FastAPI em `/mcp` (`backend/main.py:707`), disponibilizando endpoints SSE (`/mcp/sse`), transporte de mensagens (`/mcp/messages`) e catálogo de schemas.
- **Catálogo de Descoberta**: Exposto publicamente na rota `GET /api/v1/mcp/tools` para auto-descoberta rápida por agentes sem overhead de handshake SSE.

### 16.2 Arsenal das 16 Ferramentas Oficiais Registradas
| # | Ferramenta MCP | Categoria | Descrição Técnica |
|---|---|---|---|
| 1 | `get_balance` | Execução & Risco | Retorna a banca unificada, equity em tempo real, margem livre e colateral garantidor em Margem Cruzada 50X. |
| 2 | `get_positions` | Execução & Risco | Lista as posições ativas da frota (até 8 slots), preço de entrada, stop loss atual, target, ROI e PnL em USD. |
| 3 | `get_radar_signals` | Inteligência | Consulta os sinais ativos do Titan Radar em tempo real para os 507 pares da OKX com scores e filtros. |
| 4 | `evaluate_asset` | Inteligência | Executa avaliação completa quantitativa e reflexa sob demanda para um ativo e direção específicos. |
| 5 | `get_system_snapshot` | Telemetria | Retorna snapshot global do sistema: modo (PAPER/REAL), contadores de trades, uptime e status dos feeds. |
| 6 | `quarantine_symbol` | Gestão de Risco | Aplica quarentena manual ou preventiva a um ativo (padrão 7200s anti-reincidência ou 300s Scratch Guard). |
| 7 | `get_quarantines` | Gestão de Risco | Lista todos os pares perpétuos atualmente em quarentena com timestamps de expiração. |
| 8 | `query_rag` | Segundo Cérebro | Executa busca semântica de alta velocidade no Segundo Cérebro (Blueprints, manuais e regras da metodologia). |
| 9 | `get_market_intel_screener` | Screener Macro | Retorna a matriz do Screener Universal (507 pares OKX) com métricas `1C-EXP`, `1C-RANGE` e aceleração institucional. |
| 10 | `get_contract_precision_audit` | Precisão OKX | Audita especificações contratuais de um par na OKX: `tickSize`, `lotSize`, `minSz`, `ctVal` e `ctMult`. |
| 11 | `viking_tree` | OpenViking | Navega na árvore hierárquica do sistema de arquivos virtual `viking://`. |
| 12 | `viking_read` | OpenViking | Lê nós contextuais do OpenViking com Progressive Disclosure nos níveis L0 (Abstract), L1 (Overview) ou L2 (Detail). |
| 13 | `viking_search` | OpenViking | Busca semântica e por relevância em nós de conhecimento e memórias de trade do OpenViking. |
| 14 | `viking_commit_lesson` | OpenViking | Grava novas sínteses operacionais, lições aprendidas e casos forenses no Obsidian Vault e OpenViking. |
| 15 | `get_laya_sovereign_intelligence` | Laya Neural | Acessa o stream de pensamento cognitivo da Laya Neural System 1, regime de fluxo e score de convicção. |
| 16 | `get_liquidity_zones_heatmap` | Order Flow | Consulta o mapa de calor de liquidação Coinglass/OKX, muralhas de liquidez e vetor de atração do ímã de baleias. |

---

## 17. RAG Semântico Híbrido (`RAGService` & Segundo Cérebro)

O `RAGService` (`backend/services/rag_service.py`) provê indexação semântica e recuperação de documentos em sub-milissegundos (< 5ms) para alimentar o Hermes e os agentes cognitivos com a verdade canônica do sistema.

### 17.1 Motor de Indexação e Recuperação BM25 / TF-IDF
- **Algoritmo de Ranqueamento**: Combinação híbrida de Term Frequency (TF) normalizado e Inverse Document Frequency (IDF) ponderado no estilo BM25, com boosting para termos em títulos e cabeçalhos.
- **Chunking Semântico**: Fragmentação inteligente baseada em seções de Markdown, preservando títulos, tabelas e blocos conceituais inteiros sem quebra arbitrária de sentenças.
- **Tokenização Limpa**: Filtro contra stop-words e caracteres especiais, normalizando termos em português e inglês para cobertura técnica bilíngue.

### 17.2 Fontes de Conhecimento Indexadas
1. **`MASTER_ARCHITECTURE.md`**: Invariantes de risco, constantes soberanas, escadinhas de stop e governança operacional.
2. **`docs/blueprint/` (Blueprints 01 a 09)**: Especificações técnicas de motores de cálculo, feeds de dados e camadas de persistência.
3. **`vault_galaxy/` (Obsidian Vault)**:
   - `journal/`: Diários de bordo executivos com lições aprendidas de trades passados.
   - `trades/`: Registros históricos estruturados de ordens institucionais.
   - `strategies/`: Documentação de setups operacionais (`LAYA_PULLBACK_HUNTER_2H_30M`, Sweep & Flip, etc.).
4. **`.agents/rules/`**: Metodologia Superpowers (`superpowers_methodology.md`), diretrizes TDD e `AGENTS.md`.

### 17.3 Rotas da API RAG (`/api/v1/hermes/rag`)
- `GET /api/v1/hermes/rag/search?query=...&top_k=4`: Realiza consulta ranqueada por relevância, retornando título, conteúdo, score e caminho de origem do chunk.
- `GET /api/v1/hermes/rag/status`: Retorna telemetria do índice: total de chunks indexados, contagem de termos únicos, timestamp da última indexação e status de memória.
- `POST /api/v1/hermes/rag/reindex`: Dispara a reindexação completa a quente de todos os diretórios sem necessidade de reinício do processo Uvicorn.

---

## 18. Pipeline de Fine-Tuning, Datasets JSONL & Calibração RLCD

O módulo de Machine Learning do 1Crypten (`backend/app/ml/fine_tuning/` e `/api/v1/ml`) gerencia o ciclo contínuo de calibração, treinamento e refinamento da **Laya Neural System 1** (v0.4.31) e do adaptador temporal do **Kronos**.

### 18.1 Metodologia RLCD (Reinforcement Learning from AI Cognition & Decisions)
Em vez de depender de rotulagem humana manual lenta, o sistema opera sob calibração autônoma RLCD:
1. Durante o runtime, para cada avaliação do Titan Radar, o vetor de estado de mercado é registrado:
   `[ADX_2H, Delta_LSR, Delta_OI, Dist_SMA8, Dist_SMA21, BTC_Macro_Regime, Wick_Ratio, Volume_Ratio]`.
2. A decisão reflexa da Laya Neural (`BUY`, `SELL`, `HOLD`) e seu score de convicção (0 a 100%) são gravados em conjunto com o identificador da ordem.
3. Ao término do trade, o desfecho real de mercado (Lucro Líquido no Breakeven/Trailing vs Perda no Stop Loss) atua como o sinal de recompensa (Reward Signal).
4. O gerador de datasets classifica operações vencedoras (especialmente as que atingiram Alvo Chão de +300% ROI) como pares positivos de alta recompensa e falsos rompimentos como penalizações severas.

### 18.2 Gerador Canônico de Datasets (`dataset_generator.py`)
- **Geração Formatada JSONL**: Produz arquivos prontos para fine-tuning em frameworks padrão (HuggingFace, PyTorch, LoRA, OpenAI fine-tuning format):
  `{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "<vetor_mercado>"}, {"role": "assistant", "content": "<decisao_calibrada>"}]}`
- **Datasets Separados**:
  - `laya_decision_dataset.jsonl`: Focado na decisão direcional, timing de pullback e veto contra Smart Money.
  - `kronos_trajectory_dataset.jsonl`: Focado na projeção de trajetórias temporais de velas futuras.

### 18.3 Treinadores de Calibração e Pesos
- **`laya_finetune_trainer.py`**:
  - Ajusta a matriz de pesos neurais reflexos da Laya, salvando os coeficientes em `laya_calibrated_weights.json`.
  - Recalibra as prioridades Bayesianas de modo que a Laya aumente o rigor do filtro reflexo quando a taxa de acerto em pullbacks cair abaixo do threshold estatístico de 75%.
- **`kronos_adapter_trainer.py`**:
  - Ajusta a camada adaptativa do KronosScorer para refinar previsões de volatilidade e envelopes de expansão intradiária.

### 18.4 Endpoints de Controle ML (`/api/v1/ml`)
- `POST /api/v1/ml/generate-dataset`: Gera datasets atualizados no disco a partir do histórico consolidado de trades (`data/fine_tuning/`).
- `GET /api/v1/ml/dataset-stats`: Retorna métricas estatísticas dos datasets presentes no disco (total de amostras, balanceamento de classes, tamanho em bytes).
- `POST /api/v1/ml/train-laya`: Dispara o pipeline de calibração/fine-tuning dos pesos da Laya Neural System 1.
- `POST /api/v1/ml/train-kronos`: Dispara o treinamento do adaptador temporal do Kronos.
- `GET /api/v1/ml/status`: Consulta o status atual dos modelos de IA, data da última calibração e versões de pesos carregadas em memória.

---

## 19. Unificação de UI: Cockpit + Telemetria Soberana & Decomissionamento do Titan 360 (V224)

A arquitetura de interface do 1Crypten foi unificada em **duas páginas canônicas de alta performance** (`/cockpit` e `/telemetria`), descontinuando a página legada e sobrecarregada Titan 360 (`/laya`).

### 19.1 Roteamento e Redirecionamento 301 Permanente
- **Endpoint `/laya`**: Decomissionado e transformado em `RedirectResponse(url="/telemetry", status_code=301)` em `backend/main.py`.
- **Navegação Shell (`shell.js`)**: O botão `TITAN 360` foi purgado do menu desktop superior e da gaveta lateral (`sidebar`), consolidando a barra de navegação estritamente em: `COCKPIT` | `TELEMETRIA` | `PLUTUS` | `HERMES` | `DOCS`.

### 19.2 Enriquecimento da Telemetria com Inteligência Quantitativa do Titan 360
Todos os dados cruciais e não-duplicados que existiam no Titan 360 foram incorporados diretamente no endpoint `GET /api/telemetry/stats` (`TelemetryService.get_summary()`) e na coluna direita da Telemetria (`telemetry.html`):
1. **Muralhas de Liquidação Institucionais (Ímãs)**:
   - Identificação em tempo real das Top 6 piscinas de liquidação institucional ativas no mercado da OKX com volume acumulado em milhões de dólares (`wall_vol_m`), preço de gatilho (`wall_price`), distância percentual do preço atual (`distance_pct`) e orientação direcional (`ÍMÃ DE ALTA` vs `ÍMÃ DE BAIXA`).
2. **Order Flow & Pressão de Agressão**:
   - Exibição de Long/Short Ratio do Bitcoin (`btc_lsr`), CVD Taker Delta (`cvd_taker_delta_pct`) e viés de fluxo dominante (`BEAR` / `BULL`).
3. **Card Interativo de Microestrutura Sniper**:
   - Totalmente integrado à matriz de 30 chips do Titan Radar.
   - Ao clicar em qualquer ativo da matriz ou dos ímãs de liquidação, o card renderiza instantaneamente a posição relativa na amplitude de 2H (`range_pos_2h`), o tamanho do pavio de sweep de exaustão (`sweep_wick_pct`), a relação de médias SMA 8 x SMA 21 e o veredito tático de execução (`VETO MEIO DE ACUMULAÇÃO`, `TETO 2H APTO` ou `VETO VENDER FUNDO`).

### 19.3 Otimização Ergonômica de Espaço Widescreen
- **Purga de Elementos Redundantes**: A tabela secundária de 30 linhas que ficava na coluna direita (duplicando a matriz central) foi extirpada.
- **Condensação do Pipeline Flow**: O box horizontal estático do pipeline cognitivo foi condensado em linha única compacta, recuperando 35px verticais.
- **Visualização Completa sem Scroll Vertical**: A tela ultrawide acomoda agora o gráfico uPlot 60 FPS contínuo da banca, a matriz 6x5 de 30 chips e os cards de liquidação/microestrutura em um único viewport estável e ultraleve, reduzindo drasticamente o consumo de GPU e conexões de polling.

---

*Documento unico de arquitetura. Substitui e consolida os antigos ARCHITECTURE_REFERENCE, DOCUMENTATION_INDEX, STATE, SNIPER_PROTOCOLS, RESET_PROTOCOL, RULES e REQUIREMENTS.*

