# Estado Atual do Projeto — Prospect-On 3.0 (Seleção Dinâmica de Pilares + Manus)

## Resumo Executivo
**Data:** 2026-05-20
**Versão:** `v5.0 — Seleção Dinâmica de Pilares + Inteligência Manus`
**Estado:** `OPERATIONAL ✅`
**Motor Principal:** Playwright Stealth (Google Search + Google Maps) + DeepSeek Chat
**Bloqueios:** Nenhum. Google Places API e Bing removidos completamente.

---

## O Que Funciona Agora

### Os 3 Pilares — Varredura Real Comprovada
**Resultado:** 27 leads reais capturados em São Paulo em ~90 segundos.

| Pilar | Fonte | Portais Estratégicos (Manus) | Leads |
|-------|-------|------------------------------|-------|
| A — Condomínios | Google Search stealth | SíndicoNet, CoteiBem, uCondo | 1+ |
| B — Editais Públicos | Google Search stealth | PNCP, BEC-SP, Comprasnet | 15+ |
| C — Corporativo | Google Search stealth | oHub, Habitissimo, GetNinjas | 11+ |

**Leads reais capturados (amostra):**
- **Coren-SP** — Pregão Eletrônico nº 10/2025 — Pintura da Fachada (urgência 9/10)
- **CPTM** — Pintura Predial + Hidrojateamento — Estação Palmeiras-Barra Funda (urgência 8/10)
- **TCE-SP** — Recuperação e Pintura do Edifício Anexo II (urgência 7/10)
- **Faculdade de Medicina USP** — Pregão Eletrônico nº 06/2024 (urgência 7/10)
- **Prefeitura SP (SVMA)** — Pintura dos Parques Municipais (urgência 6/10)

### 🆕 Seleção Dinâmica de Pilares (v5.0)
O usuário pode **ativar/desativar cada pilar individualmente** no Dashboard antes de disparar a varredura:

- **Toggle Interativo:** Cada card de pilar (A, B, C) funciona como botão clicável com visual cyberpunk
- **Feedback Visual:** Pilar ATIVO → borda neon colorida + glow + badge `ATIVO` pulsante | Pilar OFF → opaco, dessaturado, badge `OFF`
- **Botão Sniper Inteligente:** Mostra pilares selecionados no texto (ex: `Iniciar Sniper · A,C Pilares`), desabilitado quando 0 pilares estão selecionados
- **Backend Condicional:** Apenas os hunters dos pilares ativados executam busca; pilares inativos retornam `[]` sem erro

#### Fluxo de Dados (Pilares Selecionáveis)
```
Dashboard (activePillars toggle) → api.ts (pilares=A,C) → api.py (query param) → ManagerAgent → DemandScoutAgent → asyncio.gather(apenas hunters ativos)
```

### 🆕 Inteligência Manus — Queries Estratégicas
Os caçadores de cada pilar foram enriquecidos com queries direcionadas a portais de alta conversão mapeados pela pesquisa Manus:

| Pilar | Portais Alvo | Tipo de Query |
|-------|--------------|---------------|
| A | `sindiconet.com.br`, `coteibem.com.br`, `ucondo.com.br` | Atas de assembleia, fundos de obra, cotações condominiais |
| B | `pncp.gov.br`, `bec.sp.gov.br`, `comprasnet.gov.br` | Licitações, pregões eletrônicos, diários oficiais |
| C | `ohub.com.br`, `habitissimo.com.br`, `getninjas.com.br` | Vagas de facilities, cotações corporativas, manutenção predial |

### Tecnologia Ativa
- ✅ **Playwright Stealth** — `navigator.webdriver=undefined`, user-agent real Chrome 124, viewport variável
- ✅ **Google Search** como fonte de busca (sem API, sem Bing)
- ✅ **Google Maps** como fonte de geolocalização (sem Places API)
- ✅ **DeepSeek Chat** para análise textual de todos os sinais capturados
- ✅ **SQLite** salvando todos os leads reais com contatos enriquecidos
- ✅ **Seleção Dinâmica de Pilares** — Frontend toggle → Backend condicional

### Servidores Ativos
- Backend FastAPI: `http://localhost:8002`
- Frontend Next.js: `http://localhost:3000`

---

## Mudanças Recentes (v5.0 — 20/05/2026)

### Adicionado (v5.0)
- ✅ **Seleção Dinâmica de Pilares no Dashboard** — Cards de pilar agora são botões toggle com visual premium cyberpunk (neon glow, badge ATIVO/OFF, barra inferior colorida)
- ✅ **Estado `activePillars`** — `{ A: true, B: true, C: true }` no React com toggle individual
- ✅ **Propagação completa do parâmetro `pilares`** — `page.tsx` → `api.ts` → `api.py` → `ManagerAgent` → `DemandScoutAgent` → `asyncio.gather` condicional
- ✅ **Botão Sniper inteligente** — Texto dinâmico mostra pilares ativos, desabilitado com aviso `⚠` quando 0 pilares estão selecionados
- ✅ **Queries Manus nos Hunters** — `pillar_a_agent.py`, `pillar_b_agent.py`, `pillar_c_agent.py` com queries focadas em portais de alta conversão
- ✅ **Logs WS detalhados** — `ManagerAgent` emite nomes ricos de pilares ativados no HUD holográfico

### Arquivos Modificados (v5.0)
| Arquivo | Tipo | Descrição |
|---------|------|-----------|
| `backend/api.py` | Backend | Rotas `/scan/start`, `/sniper/start`, `/scan-pillars` com parâmetro `pilares` |
| `backend/src/agents/pillar_a_agent.py` | Backend | Queries Manus para SíndicoNet, CoteiBem, uCondo |
| `backend/src/agents/pillar_b_agent.py` | Backend | Queries Manus para PNCP, BEC-SP, Comprasnet |
| `backend/src/agents/pillar_c_agent.py` | Backend | Queries Manus para oHub, Habitissimo, GetNinjas |
| `backend/src/agents/demand_scout_agent.py` | Backend | `scan_all_pillars(pilares)` com gather condicional |
| `backend/src/agents/manager_agent.py` | Backend | `run_full_scan(pilares)` com logs WS ricos |
| `frontend/lib/api.ts` | Frontend | `scanStart` e `scanPillars` com parâmetro `pilares` |
| `frontend/app/(system)/dashboard/page.tsx` | Frontend | Estado `activePillars`, cards toggle, botão inteligente |

### Histórico v4.0
- ✅ Modo Stealth Playwright completo em todos os agentes
- ✅ Google Search em todos os pilares (substitui Bing)
- ✅ WebEnrichmentAgent v4.0 — Google Search para contatos
- ✅ BrowserScoutAgent — Google Maps direto
- ❌ Removido: PlacesClient, Bing Search headless

---

## Comandos Rápidos

```powershell
# Testar os 3 pilares
cd backend ; python test_real_pillars.py

# Pipeline completo (todos os pilares)
cd backend ; python -c "
import asyncio
from src.agents.manager_agent import ManagerAgent
asyncio.run(ManagerAgent().run_full_scan(city='São Paulo', target_leads=3, pilares='A,B,C'))
"

# Pipeline apenas Pilar A e C
cd backend ; python -c "
import asyncio
from src.agents.manager_agent import ManagerAgent
asyncio.run(ManagerAgent().run_full_scan(city='São Paulo', target_leads=3, pilares='A,C'))
"
```
