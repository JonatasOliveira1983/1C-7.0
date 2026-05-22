# 🎨 Sistema de Design — Prospect-On 3.0

Este documento integra os princípios do **Diagram Design** (Cathryn Lavery) com a identidade visual da **Otto Pinturas**.

---

## 🎨 PALETA DE CORES (Premium Dark)

| Papel (Background) | Tinta (Texto) | Destaque (Accent) | Sucesso | Mudo |
|---|---|---|---|---|
| `#020617` (Slate-950) | `#f8fafc` (Slate-50) | `#22d3ee` (Cyan-400) | `#34d399` (Emerald-400) | `#94a3b8` (Slate-400) |

### Cores Adicionais

| Papel | Cor |
|-------|-----|
| **Erro/Alerta** | `#f87171` (Red-400) |
| **Warning** | `#fbbf24` (Amber-400) |
| **Glass Panel BG** | `rgba(2, 6, 23, 0.8)` + `backdrop-blur-xl` |
| **Border Glass** | `rgba(148, 163, 184, 0.1)` (Slate-400 a 10%) |
| **Hover Highlight** | `rgba(34, 211, 238, 0.1)` (Cyan-400 a 10%) |

---

## ✍️ TIPOGRAFIA

### Fontes
- **Títulos (H1-H3):** `Instrument Serif` — Elegância, autoridade e sofisticação editorial.
- **Corpo/Nomes/UI:** `Geist` (Sans-serif) — Modernidade, clareza e legibilidade.
- **Dados/Técnico:** `Geist Mono` — Precisão para coordenadas, valores monetários, métricas e código.

### Escala de Tamanhos (4px Grid)
| Nível | Tamanho | Uso |
|-------|---------|-----|
| **H1** | 48px | Título principal (Hero, página) |
| **H2** | 32px | Seções principais |
| **H3** | 20px | Cards e subseções |
| **Body L** | 16px | Texto corrido, parágrafos |
| **Body** | 14px | Texto padrão de UI |
| **Small** | 12px | Labels, metadados, badges |
| **Mono** | 12px | Dados técnicos, scores, coordenadas |

---

## 📏 REGRAS DE GRID (4px)

Todas as medidas em espaçamentos e tamanhos de fonte DEVEM ser divisíveis por **4px**.

### Medidas Padrão
- **Gaps:** 4, 8, 12, 16, 24, 32, 40, 48, 64
- **Padding de Cards:** 24px
- **Border Radius:** 4px (inputs), 6px (cards, máximo permitido), 8px (modais)
- **Icon Sizes:** 16px, 20px, 24px

### Larguras de Componentes
- **Sidebar:** 240px (colapsada: 64px)
- **Modal:** 560px (máximo), 480px (padrão)
- **Card de Lead:** 320px
- **Stat Card:** 240px

---

## 🏗️ PADRÕES DE DIAGRAMA

1. **Foco Editorial:** Máximo 1-2 elementos em `Cyan-400` por diagrama/seção. O destaque deve guiar o olhar, não competir.

2. **Sem Slop Visual:** Evitar gradientes exagerados, sombras pesadas e bordas arredondadas demais.
   - Sombra máxima: `shadow-lg` (Tailwind)
   - Border radius máximo: 6px (8px apenas para modais)
   - Backdrop blur: `backdrop-blur-xl` para painéis glass

3. **Máscaras de Seta:** Rótulos de setas devem sempre ter um fundo sólido para não "atropelar" a linha.

4. **Hierarquia Clara:**
   - Background: Slate-950 (sólido, profundo)
   - Superfícies: Slate-900 (cards)
   - Glass Panels: `bg-slate-950/80 backdrop-blur-xl`
   - Borders: `border-slate-800` ou `border-slate-400/10`

---

## 🧩 COMPONENTES GLASS-PREMIUM

### Card Padrão
```
bg-slate-900
border border-slate-800
rounded-[6px]
p-6 (24px padding)
shadow-lg
hover:border-slate-700 (transição suave)
```

### Glass Panel (Modais, Dropdowns)
```
bg-slate-950/80
backdrop-blur-xl
border border-slate-400/10
rounded-[8px]
shadow-2xl
```

### Botão Primário (Cyan)
```
bg-cyan-500 hover:bg-cyan-400
text-slate-950 font-semibold
rounded-[4px] px-6 py-2
transition-all duration-200
```

### Botão Secundário (Outline)
```
border border-slate-700 hover:border-cyan-400/50
text-slate-300 hover:text-cyan-400
rounded-[4px] px-6 py-2
transition-all duration-200
```

### Badge/Status
- **Quente (Hot):** `bg-emerald-400/10 text-emerald-400 border border-emerald-400/20`
- **Morno (Warm):** `bg-amber-400/10 text-amber-400 border border-amber-400/20`
- **Frio (Cold):** `bg-slate-400/10 text-slate-400 border border-slate-400/20`
- **Erro:** `bg-red-400/10 text-red-400 border border-red-400/20`

---

## 🎬 ANIMAÇÕES E TRANSIÇÕES

- **Duração padrão:** 200ms (`duration-200`)
- **Easing:** `ease-out` para entradas, `ease-in` para saídas
- **Hover em cards:** `hover:border-slate-700 transition-colors`
- **Modal:** `animate-in fade-in zoom-in-95`
- **Loading:** Skeleton com `animate-pulse bg-slate-800`
- **Entrada de itens:** Staggered `fade-in slide-in-from-bottom-4` com delay incremental

---

## 📐 PADRÕES DE LAYOUT

### Dashboard Layout
```
┌──────────────────────────────────────────┐
│ Sidebar (240px) │  Content Area          │
│                 │  ┌───────────────────┐ │
│  Navegação      │  │  Header + Stats   │ │
│  Links          │  │  (StatCards)       │ │
│  User Info      │  │───────────────────│ │
│                 │  │  Main Content      │ │
│                 │  │  (Table/Grid)      │ │
│                 │  └───────────────────┘ │
└──────────────────────────────────────────┘
```

### Grid de Cards
- **Desktop:** `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6`
- **Gap entre cards:** 24px (`gap-6`)
- **Padding da área de conteúdo:** 32px (`p-8`)

---

## 🖼️ DIRETRIZES DE ÍCONES

Usar **Lucide Icons** (v1.8.0+) — preferir ícones estáveis:
- `Globe` — Website/Mapa
- `MessageSquare` — WhatsApp/Contato
- `Phone` — Telefone
- `Mail` — E-mail
- `MapPin` — Endereço
- `Building2` — Condomínio/Prédio
- `Search` — Busca/Scan
- `Activity` — Status/Logs
- `BarChart3` — Dashboard/Métricas
- `FileText` — Relatórios
- `Settings` — Configurações
- `Zap` — Leads Quentes
- `Target` — Sniper Mode
- `Camera` — Fachada/Vistoria
- `CheckCircle` — Verificado
- `XCircle` — Vetado
- `AlertTriangle` — Alerta

---

## 🚀 INTEGRAÇÃO GSD

Seguimos o fluxo **Especificação → Plano → Execução**.

- Todos os diagramas devem ser gerados como arquivos HTML auto-contidos com SVG inline, conforme o `backend/src/utils/diagram_templates.py`.
- A estética "Diagram Design" deve estar presente em relatórios PDF e propostas geradas pelo `ClosingAgent`.
- Componentes frontend devem respeitar este design system — revisar contra este documento no code review.

---

*Atualizado em: 19 de Maio de 2026 — Versão 3.2*