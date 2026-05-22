# 🏗️ Arquitetura Prospect-On 3.0 (Browser Extension Mode)

Este documento descreve a arquitetura técnica, os fluxos de dados e as integrações do sistema **Prospect-On**, operando em **modo extensão de navegador real** — zero APIs pagas, zero Bing, zero Google Console.

---

## 🚀 1. Stack Tecnológica

| Camada | Tecnologia | Porta | Observação |
|--------|-----------|-------|------------|
| **Frontend** | Next.js 16 (Turbopack), TypeScript, Tailwind CSS v3.4 | 3000 | Landing Page + Dashboard Glass-Premium |
| **Backend API** | FastAPI (Python 3.10+), Uvicorn | 8002 | REST + WebSocket para logs ativos |
| **IA Principal** | **DeepSeek Chat** (deepseek-chat) | cloud | Qualificação, extração de sinais e enriquecimento textual |
| **Discovery Engine** | **Playwright Stealth** (Chromium) | local | Navega Google Maps, Google Search e sites como usuário real |
| **Banco de Dados** | SQLite (Bunker Mode) | local | Schema com contatos ricos (e-mail, telefone, CNPJ, social) |

> ⚠️ **Nenhuma API paga de busca é usada.** O sistema navega a web como extensão de navegador real.

---

## 📁 2. Estrutura do Projeto (v4.0 — Browser Extension Mode)

### Backend (`/backend`)
```
backend/
├── api.py                          # Servidor FastAPI — rotas REST e WebSocket
├── main.py                         # Entry point legado
├── auto_prospect.py                # Prospecção autônoma
├── requirements.txt                # Dependências Python
├── .env                            # Chaves de API e configurações
├── data/
│   ├── prospecton.db               # Banco SQLite
│   └── images/                     # Capturas de fachada (.png)
├── static/
│   └── vistorias/                  # Screenshots de fachada capturados pelo browser
└── src/
    ├── agents/                     # Agentes especialistas
    │   ├── manager_agent.py        # Orquestrador v10.0 — sem Places API
    │   ├── demand_scout_agent.py   # Orquestra os 3 Pilares via asyncio.gather
    │   ├── pillar_a_agent.py       # Pilar A — Condomínios (Google Search stealth)
    │   ├── pillar_b_agent.py       # Pilar B — Editais Públicos (Google Search stealth)
    │   ├── pillar_c_agent.py       # Pilar C — Corporativo/Facilities (Google Search stealth)
    │   ├── browser_scout_agent.py  # Google Maps via Playwright stealth (sem Places API)
    │   ├── web_enrichment_agent.py # Google Search stealth para contatos (sem Bing)
    │   ├── semantic_extractor_agent.py  # Extração semântica profunda com DeepSeek
    │   ├── lead_enrichment_agent.py     # Enriquecimento contextual com DeepSeek
    │   ├── analyst_agent.py        # Score final e Match Otto
    │   ├── hunter_agent.py         # Fallback geográfico via OpenStreetMap
    │   ├── surveyor_agent.py       # Auditoria visual de fachada
    │   └── closing_agent.py        # Geração de propostas e copy
    └── utils/
        ├── database.py             # Interface SQLite (Postgres-ready)
        ├── deepseek_client.py      # Cliente da API DeepSeek
        ├── vision_analyzer.py      # Análise de imagens
        ├── places_client.py        # DEPRECIADO — mantido apenas por compatibilidade
        ├── usage_monitor.py        # Monitor de uso da API DeepSeek
        ├── webhook_client.py       # Cliente webhook (WhatsApp/Evolution)
        └── logger.py               # Logger centralizado
```

---

## ⚡ 3. Fluxo de Inteligência — Os 3 Pilares (v4.0)

O sistema opera com **varredura paralela** via `asyncio.gather` dos 3 pilares, sem depender de nenhuma API de busca paga:

```
Usuário dispara varredura
         ↓
DemandScoutAgent
  ├── PillarAHunterAgent  → Google Search (Playwright stealth) → DeepSeek analisa
  ├── PillarBHunterAgent  → Google Search (Playwright stealth) → DeepSeek analisa
  └── PillarCHunterAgent  → Google Search (Playwright stealth) → DeepSeek analisa
         ↓
  [Leads com sinais de demanda identificados — dados 100% reais]
         ↓
ManagerAgent processa cada lead:
  ├── BrowserScoutAgent   → Google Maps (Playwright stealth)
  │     Captura: endereço, telefone, coordenadas, foto da fachada
  ├── SemanticExtractorAgent → DeepSeek
  │     Captura: CNPJ, síndico, administradora, decisores
  ├── WebEnrichmentAgent  → Google Search (Playwright stealth) → DeepSeek
  │     Captura: email, WhatsApp, redes sociais, website oficial
  └── LeadEnrichmentAgent → DeepSeek
        Captura: score final, urgência estimada, copy de prospecção
         ↓
Lead enriquecido → SQLite → Dashboard ✅
```

### O que cada Pilar busca:

| Pilar | Fonte | O que detecta |
|-------|-------|---------------|
| **A — Condomínios** | Google Search (stealth) | Atas de assembleia, fundos de obra, cotações de fachada |
| **B — Editais Públicos** | Google Search (stealth) | Pregões eletrônicos, licitações, diários oficiais |
| **C — Corporativo** | Google Search (stealth) | Vagas de pintor, facilities, cotações corporativas |

### Resultado comprovado (20/05/2026):
- **27 leads reais** capturados em uma varredura de São Paulo
- Pilar B: 15 editais reais (Coren-SP, CPTM, FMUSP, TCE-SP, Prefeitura SP...)
- Pilar C: 11 demandas corporativas reais (facilities, vagas, empresas especializadas)

---

## 🔐 4. Modo Stealth — Como o Navegador Simula um Usuário Real

Todos os agentes Playwright usam o perfil stealth para não ser detectados como bot:

```python
# Flags que desativam a detecção de automação
args = [
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
]

# Script injetado antes de qualquer página carregar
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
window.chrome = { runtime: {} };

# Contexto variável (imita monitor real)
viewport: [1366x768, 1440x900 ou 1920x1080] — aleatório
user_agent: Chrome 122 / 123 / 124 — aleatório
locale: "pt-BR" | timezone: "America/Sao_Paulo"
delay: 2.0s a 3.5s entre ações — aleatório
```

---

## 🛡️ 5. Protocolos de Estabilidade

| Camada | Comportamento |
|--------|---------------|
| **Busca primária** | Google Search via Playwright stealth (sem API paga) |
| **Google Maps** | Playwright stealth — sem Places API |
| **Fallback de dados** | Quando Google bloqueia: dados reais auditados (Copan, USP, etc.) |
| **Bunker Mode DB** | Migrações preservam dados. ALTER TABLE antes de DROP. |
| **Stealth Anti-Bot** | `navigator.webdriver=undefined` + user-agent real + delays humanos |

---

## 🔌 6. APIs Externas

| API | Uso | Status |
|-----|-----|--------|
| **DeepSeek Chat** | Extração de sinais, enriquecimento, scoring, copy | ✅ Ativo |
| **Google Search** | Navegação stealth via Playwright (SEM API) | ✅ Ativo |
| **Google Maps** | Navegação stealth via Playwright (SEM API) | ✅ Ativo |
| **Google Places API** | ~~Dados estruturados~~ | ❌ REMOVIDO (REQUEST_DENIED) |
| **Bing Search** | ~~Busca alternativa~~ | ❌ REMOVIDO (bloqueava como bot) |
| **Evolution API (WhatsApp)** | Envio de mensagens WhatsApp | ⏳ Configurado |

---

## 🖥️ 7. Como Iniciar o Sistema

### Backend (FastAPI)
```powershell
cd backend
pip install -r requirements.txt
python api.py
# Servidor em: http://localhost:8002
# Swagger UI: http://localhost:8002/docs
```

### Frontend (Next.js)
```powershell
cd frontend
npm install
npm run dev
# Servidor em: http://localhost:3000
```

### Parar os Servidores
```powershell
Get-Process -Name "python","node" -ErrorAction SilentlyContinue | Stop-Process -Force
```

---

## 📊 8. Rotas da API (Backend)

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/health` | Health check do sistema |
| `POST` | `/api/scan` | Inicia scan Sniper (3 pilares) |
| `POST` | `/api/analyze-lead` | Analisa lead individual |
| `GET` | `/api/leads` | Lista todos os leads |
| `GET` | `/api/leads/{id}` | Detalhe do lead |
| `GET` | `/api/leads/hot` | Leads quentes (qualificados) |
| `GET` | `/api/reports/{filename}` | Download de relatório PDF |
| `GET` | `/api/images/{filename}` | Download de imagem de fachada |
| `GET` | `/api/usage` | Métricas de uso do DeepSeek |
| `WS` | `/ws/logs` | WebSocket para logs em tempo real |

### Comandos de Manutenção
```powershell
# Verificar DB
cd backend ; python check_db.py

# Testar os 3 Pilares
cd backend ; python test_real_pillars.py

# Testar pipeline completo
cd backend ; python -c "import asyncio; from src.agents.manager_agent import ManagerAgent; asyncio.run(ManagerAgent().run_full_scan(city='São Paulo', target_leads=3))"
```

---

*Atualizado em: 20 de Maio de 2026 — Versão 4.0 (Browser Extension Mode — Zero API Paga)*