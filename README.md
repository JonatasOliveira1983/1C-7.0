# Prospect-On 3.2 (Sniper Sovereignty)

**Motor de Inteligência Comercial** da **Otto Pinturas** — localização, qualificação e geração de propostas premium para prospecção de condomínios.

---

## 🚀 Como Rodar

### 1. Backend (FastAPI — Porta 8002)

```powershell
cd backend
pip install -r requirements.txt
python api.py
```

**Acesso:**
- API: http://localhost:8002
- Swagger UI: http://localhost:8002/docs
- WebSocket Logs: `ws://localhost:8002/ws/logs`

### 2. Frontend (Next.js 16 — Porta 3000)

```powershell
cd frontend
npm install
npm run dev
```

**Acesso:**
- Landing Page: http://localhost:3000
- Dashboard: http://localhost:3000/dashboard
- Leads Quentes: http://localhost:3000/leads-quentes
- Mapa Radar: http://localhost:3000/mapa-radar

### 3. Parar os Servidores

```powershell
Get-Process -Name "python","node" -ErrorAction SilentlyContinue | Stop-Process -Force
```

---

## ⚙️ Configuração

Copie `.env.example` para `backend/.env` e configure:

| Variável | Descrição |
|----------|-----------|
| `DEEPSEEK_API_KEY` | Chave da API DeepSeek (enriquecimento textual e copy) |
| `GEMINI_API_KEY` | Chave da API Google Gemini (auditoria visual de fachada) |
| `GOOGLE_MAPS_API_KEY` | Chave da API Google Maps (legacy — opcional) |

---

## 🏗️ Arquitetura (13 Agentes Sniper)

O sistema é composto por agentes Python especialistas orquestrados pelo **ManagerAgent**:

| Agente | Função |
|--------|--------|
| **BrowserScoutAgent** | Motor principal — Playwright/DOM Scraping do Google Maps |
| **HunterAgent** | Fallback geográfico via OpenStreetMap |
| **AnalystAgent** | Qualificação e cálculo de Match Otto |
| **SurveyorAgent** | Auditoria visual de fachada via Gemini |
| **ClosingAgent** | Consolidação e geração de propostas |
| **ContactAgent** | Enriquecimento de canais de contato |
| **LeadEnrichmentAgent** | Enriquecimento textual via DeepSeek |
| **DemandScraperAgent** | Raspagem de demandas externas |
| **GeosampaAgent** | Dados da prefeitura de SP (IPTU) |
| **HealthAgent** | Monitoramento de saúde do sistema |
| **ExtensionLauncher** | Extensão Chrome para captura manual |
| **ScoutAgent** | Scout auxiliar de reconhecimento |

---

## 📚 Documentação

| Documento | Conteúdo |
|-----------|----------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Arquitetura completa do sistema |
| [RULES.md](RULES.md) | Regras, padrões e comandos rápidos |
| [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) | Sistema de design (cores, tipografia, grid) |
| [GSD.md](GSD.md) | Protocolo GSD de desenvolvimento |
| [.gsd/PROJECT.md](.gsd/PROJECT.md) | Visão do projeto |
| [.gsd/REQUIREMENTS.md](.gsd/REQUIREMENTS.md) | Requisitos técnicos e limites |
| [.gsd/STATE.md](.gsd/STATE.md) | Estado atual do projeto |
| [.gsd/ROADMAP.md](.gsd/ROADMAP.md) | Roadmap de desenvolvimento |

---

## 🛠️ Comandos Úteis

```powershell
# Testes
cd backend ; python test_sniper.py        # Testa o motor Sniper
cd backend ; python test_gemini.py        # Testa integração Gemini
cd backend ; python test_demand_pipeline.py # Testa pipeline de demanda

# Manutenção
cd backend ; python check_db.py           # Verifica banco de dados
cd backend ; python check_usage.py        # Verifica uso de APIs
cd backend ; python src/utils/migrate_v7.py # Migração do banco v7
cd backend ; python inject_mock.py        # Injeta dados de teste
```

---

*Versão 3.2 — Maio 2026*