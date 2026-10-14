# 07 — PLANO DE ARQUITETURA & IMPLEMENTAÇÃO: AGENTE PLUTUS (MÉTODO ARCA)

> **Status**: Concluído & Integrado ao Menu Lateral (Shell Drawer)  
> **Versão**: 1.1  
> **Data**: 12/10/2026  
> **Orquestrador**: Hermes Intelligence  
> **Design System**: [Binance Design System](https://getdesign.md/binance/design-md) (`#0b0e11`, `#1e2329`, `#fcd535`)

---

## 1. Visão Geral do Produto

O **Plutus** é o agente autônomo do ecossistema 1Crypten especializado em **Preservação Patrimonial, Renda Passiva Líquida Previsível e Alocação Antifrágil** baseada no **Método ARCA** (Thiago Nigro / Primo Rico):
- **A**ções Brasileiras de Dividendos (25%-30%)
- **R**eal Estate / Fundos Imobiliários Isentos de IR (35%-40%)
- **C**aixa / Renda Fixa com Proventos e Reserva de Oportunidade (15%-20%)
- **A**tivos Internacionais / Dólar e REITs (15%-20%)

---

## 2. Design System: Padrão Binance Oficial (`DESIGN.md`)

Seguindo à risca os tokens de `https://getdesign.md/binance/design-md`:

- **Canvas Dark**: `#0b0e11`
- **Surface Card**: `#1e2329` (Bordas: `#2b3139`)
- **Accent Primary**: `#fcd535` (Binance Yellow)
- **Primary Active/Hover**: `#f0b90b`
- **Text Body**: `#eaecef`
- **Text Muted**: `#707a8a` / `#929aa5`
- **Trading Up (Verde)**: `#0ecb81`
- **Trading Down (Vermelho)**: `#f6465d`
- **Tipografia**: Numerais e finanças em fonte monoespaçada, zero emojis, ícones vetoriais SVG de precisão.

---

## 3. Arquitetura Técnica dos Componentes

### 3.1. Backend
1. **`backend/services/plutus_agent.py`**:
   - Engine de cálculo matemático reverso: $Patrimonio = \frac{RendaMensal \times 12}{DY_{ponderado}}$.
   - Algoritmo de distribuição nos 4 pilares da ARCA e alocação por ativo com base em liquidez, P/VP, vacância e consistência de dividendos.
   - Conexão com o `HermesAgent` para emissão de parecer executivo macroeconômico.
2. **`backend/routes/plutus_routes.py`**:
   - `POST /api/v1/plutus/simulate`: Simulação com base na renda desejada.
   - `GET /api/v1/plutus/universe`: Catálogo de ativos curados da ARCA.
   - `POST /api/v1/plutus/hermes-diagnosis`: Parecer com IA do Hermes.
3. **`backend/main.py`**:
   - Registro da rota `/api/v1/plutus` e montagem da rota estática `/plutus`.

### 3.2. Frontend & Navegação Unificada
1. **`backend/app/static/plutus.html`**:
   - Interface completa dedicada ao Plutus no padrão Binance Dark.
   - Card de Meta de Renda com input formatado em R$ e seletores de perfil.
   - 4 Stat Cards de métricas financeiras.
   - Gráfico de barras de distribuição ARCA.
   - Tabela detalhada de ativos recomendados com cotação, DY, alocação em R$ e provento mensal estimado.
   - Seção de Diagnóstico Institucional do Hermes.
2. **`backend/app/static/shell.js` (Lamborghini Unified Shell & Sidebar Drawer)**:
   - **Menu Lateral Retrátil (Drawer)**:
     - Seção *Páginas do Sistema*: `PLUTUS (VIVER DE RENDA)` com badge dourado `[ARCA]`.
     - Seção *Agentes da Frota*: `PLUTUS · MÉTODO ARCA` com status `ON`.
   - **Barra Superior Desktop (`desktop-nav`)**: Atalho direto `PLUTUS` ao lado do Cockpit.
   - **Header Fleet Pills**: `HERMES • CAPTAIN • FLASH • KRONOS • PLUTUS`.
   - **Barra Inferior Mobile (`app-bottom-bar`)**: Botão de toque direto `Plutus`.
3. **`backend/app/static/cockpit.html`**:
   - Card dedicado no topo da coluna esquerda (Mesa Tática) com botão `[ABRIR UI ➔]`.
   - Badge com link rápido no Banner Superior de Telemetria.

---

## 4. Roteiro de Microetapas de Execução

- [x] **Etapa 1**: Criar `backend/services/plutus_agent.py` com a lógica matemática da ARCA e base curada de ativos.
- [x] **Etapa 2**: Criar `backend/routes/plutus_routes.py` e plugar no `backend/main.py`.
- [x] **Etapa 3**: Criar `tests/test_plutus_agent.py` e validar via TDD (100% pass).
- [x] **Etapa 4**: Criar a interface dedicada `backend/app/static/plutus.html` no padrão Binance Dark (`#0b0e11` / `#fcd535`).
- [x] **Etapa 5**: Integrar link no menu lateral (Sidebar Drawer de `shell.js`), barra superior desktop, coluna esquerda da Mesa Tática e banner do Cockpit.
- [x] **Etapa 6**: Testar endpoints e carregar a UI com verificação empírica no terminal.
