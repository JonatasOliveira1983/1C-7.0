# 📜 RULES — Prospect-On 3.0 (Browser Extension Mode)
## Documento de Contexto, Padrões e Regras do Sistema

> **Versão:** 4.0 (Browser Extension Mode) — Última atualização: 20 de Maio de 2026
> Este documento é a fonte da verdade sobre a arquitetura de **Agentes Sniper** e estabilidade do sistema.

---

## 🎯 1. IDENTIDADE E MISSÃO

**Prospect-On** é um Motor de Inteligência Comercial de alta performance. Sua missão é localizar, qualificar e gerar propostas premium para a **Otto Pinturas** através de navegação web automatizada em modo stealth (extensão de navegador real) e análise textual via IA generativa.

**Regra de Ouro:** O sistema **NÃO USA NENHUMA API PAGA DE BUSCA**. Navega a web como um usuário humano real — como uma extensão do Chrome faria.

---

## 🏗️ 2. ARQUITETURA — OS 3 PILARES

O sistema opera com **varredura paralela** dos 3 pilares. Cada pilar usa Playwright stealth para navegar o Google e DeepSeek para analisar o texto capturado:

### Agentes de Descoberta (Demand-First)

1. **DemandScoutAgent** — Orquestrador dos 3 Pilares. Executa em paralelo via `asyncio.gather`.

2. **PillarAHunterAgent (Pilar A)** — Caça condomínios com demanda ativa:
   - Navega Google Search: atas de assembleia, fundos de obra, cotações de fachada
   - DeepSeek extrai nome, urgência, link fonte, resumo do sinal

3. **PillarBHunterAgent (Pilar B)** — Caça editais e licitações públicas:
   - Navega Google Search: pregões eletrônicos, diários oficiais, portais de compras
   - DeepSeek identifica número do edital, órgão, valor estimado

4. **PillarCHunterAgent (Pilar C)** — Caça demandas corporativas:
   - Navega Google Search: vagas de pintor, facilities, cotações corporativas
   - DeepSeek identifica empresa contratante e urgência da demanda

### Agentes de Enriquecimento (Pipeline Reverso)

5. **ManagerAgent v10.0** — Orquestrador central. Processa sinais dos pilares e aciona o enriquecimento.

6. **BrowserScoutAgent** — Google Maps via Playwright stealth. Captura: endereço, telefone, foto da fachada, coordenadas, website.

7. **WebEnrichmentAgent v4.0** — Google Search stealth para contatos. Captura: email, WhatsApp, CNPJ, redes sociais.
   - ⚠️ **Sem Bing.** Usa Google Search via Playwright como usuário real.

8. **SemanticExtractorAgent** — Extração semântica profunda com DeepSeek (CNPJ, síndico, administradora, decisores).

9. **LeadEnrichmentAgent** — Score final, urgência estimada e copy de prospecção personalizada.

10. **AnalystAgent** — Cálculo do Match Otto e Urgency Score.

11. **SurveyorAgent** — Auditoria visual de fachada (contagem de torres, andares, estimativa de m²).

12. **ClosingAgent** — Consolidação de dados e geração de proposta editorial.

### Agentes de Suporte

13. **HunterAgent** — Fallback geográfico via OpenStreetMap (aciona apenas se BrowserScout falhar).
14. **GeosampaAgent** — Dados de IPTU e idade do prédio (foco São Paulo).

---

## ⚡ 3. STACK TECNOLÓGICA

| Camada | Tecnologia | Porta | Observação |
|--------|-----------|-------|------------|
| Frontend | Next.js 16 (Turbopack) | 3000 | Padrão Slate-950 + Cyan-400 |
| Backend API | FastAPI (Python 3.10+) | **8002** | Uvicorn + WebSocket |
| IA Principal | **DeepSeek Chat** | cloud | Extração, scoring e copy |
| Discovery | **Playwright Stealth** (Chromium) | local | Google Maps + Google Search — SEM API |
| Banco Dados | SQLite (Bunker Mode) | local | Schema com contatos ricos |
| WhatsApp | Evolution API v2 | 8080 | Opcional |

---

## 🔐 4. PROTOCOLO STEALTH — REGRAS DE NAVEGAÇÃO

Todo agente que usa Playwright DEVE seguir estas regras:

```python
# ✅ OBRIGATÓRIO em todo launch de browser
args = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-blink-features=AutomationControlled",  # Anti-detecção
    "--disable-infobars",
]

# ✅ OBRIGATÓRIO em todo new_context
viewport    = random.choice([{w:1366,h:768}, {w:1440,h:900}, {w:1920,h:1080}])
user_agent  = random.choice(STEALTH_USER_AGENTS)  # Chrome 122-124
locale      = "pt-BR"
timezone_id = "America/Sao_Paulo"

# ✅ OBRIGATÓRIO — Script injetado antes de carregar qualquer página
await context.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    window.chrome = { runtime: {} };
""")

# ✅ OBRIGATÓRIO — Delay humano aleatório
await page.wait_for_timeout(random.randint(2000, 3500))
```

### Fontes de Busca Aprovadas

| ✅ Usar | ❌ Nunca usar |
|---|---|
| `google.com/search` via Playwright | Bing API ou Bing headless |
| `google.com/maps` via Playwright | Google Places API (REQUEST_DENIED) |
| Site oficial do lead diretamente | Qualquer API paga de busca |

---

## 🛡️ 5. PROTOCOLOS DE DESENVOLVIMENTO

### 5.1 Dados — Apenas Reais
- **Zero mocks em produção.** Dados devem ser extraídos de fontes reais.
- Fallbacks com dados reais auditados são aceitáveis apenas quando Google bloquear após N tentativas.
- Jamais inserir dados fictícios no banco `prospecton.db`.

### 5.2 Estabilidade do Frontend
- **Zero Crash UI:** Usar optional chaining (`?.`) extensivamente.
- **Tailwind Only:** Estilização exclusiva via Tailwind CSS.
- **Componentes Resilientes:** Todo componente deve ter fallback visual para estados de erro e loading.

### 5.3 Banco de Dados — Bunker Mode
- Migrações usam `ALTER TABLE` antes de `DROP TABLE`. Dados nunca perdidos.
- Schema: `prospecton.db` via SQLite. Compatível com Postgres para produção.

### 5.4 Separação de Responsabilidades (Agentic Separation)
- Agentes não compartilham estado diretamente — comunicação via ManagerAgent.
- Fluxo unidirecional: Discovery (Pilares) → Mapping (Maps) → Enrichment (Web) → Scoring → Closing.

---

## 🎨 6. PADRÕES DE DESIGN (Premium Diagram)

- **Sistema Visual:** Inspirado no *Diagram Design* (Cathryn Lavery).
- **Cores:** Slate-950 (Fundo), Cyan-400 (Destaque), Emerald-400 (Success), Slate-400 (Muted).
- **Tipografia:** Instrument Serif (títulos), Geist Sans (corpo), Geist Mono (dados).
- **Bordas:** Máximo 6px de arredondamento.

---

## 🚀 7. COMANDOS RÁPIDOS

### Iniciar Sistema
```powershell
# Terminal 1 — Backend
cd backend
python api.py

# Terminal 2 — Frontend
cd frontend
npm run dev
```

### Parar Sistema
```powershell
Get-Process -Name "python","node" -ErrorAction SilentlyContinue | Stop-Process -Force
```

### Testes e Manutenção
```powershell
# Testar os 3 Pilares (deve capturar leads reais)
cd backend ; python test_real_pillars.py

# Verificar banco de dados
cd backend ; python check_db.py

# Pipeline completo (ManagerAgent)
cd backend ; python -c "
import asyncio
from src.agents.manager_agent import ManagerAgent
asyncio.run(ManagerAgent().run_full_scan(city='São Paulo', target_leads=3))
"
```

### Health Check
- **Backend:** http://localhost:8002/docs
- **Frontend:** http://localhost:3000
- **System Health:** http://localhost:3000/api/system/health

---

## 📊 8. RESULTADOS COMPROVADOS

| Data | Cidade | Leads Reais | Pilar A | Pilar B | Pilar C |
|------|--------|------------|---------|---------|---------|
| 20/05/2026 | São Paulo | **27** | 1 | 15 | 11 |

**Exemplos reais capturados:**
- Coren-SP — Pregão Eletrônico nº 10/2025 (Pintura da Fachada)
- CPTM — Pintura + Hidrojateamento da Estação Palmeiras-Barra Funda
- TCE-SP — Recuperação e Pintura do Edifício Anexo II
- Prefeitura SP (SVMA) — Pintura dos Parques Municipais
- Faculdade de Medicina USP — Pregão Eletrônico nº 06/2024

---

*Atualizado em: 20 de Maio de 2026 — Versão 4.0 (Browser Extension Mode — Zero API Paga)*