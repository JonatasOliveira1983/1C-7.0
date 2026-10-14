# 04 - BRIEFING DE UI/UX & SISTEMA DE DESIGN MOBILE - 1CRYPTEN

> **Regra de Ouro**: A interface mobile deve ser rapida, ergonomica para o polegar, de alto contraste e estritamente profissional. E proibido o uso de templates genericos ou icones emoji. Todo elemento visual deve refletir precisao quantitativa no padrao Binance Dark & Gold.

---

## 1. Identidade Visual e Filosofia de Design Mobile
- **Estilo Base**: Binance Dark Executive & Palantir Mobile HUD.
- **Ambiente**: Escuro profundo (`#0B0E11`), cards em grafite escuro (`#181A20`), realces em ouro executivo (`#F0B90B`), lucros em verde institucional (`#0ECB81`) e drawdowns em vermelho cirurgico (`#F6465D`).
- **Regra Fundamental de Icones**: **100% Livre de Emojis**. Toda a iconografia (setas, microfone, graficos, carteira, chat) utiliza exclusivamente vetores SVG inline.
- **Ergonomia para Uma Mao (Thumb Zone)**: Os controles de navegacao e acoes criticas estao situados na parte inferior da tela, ao alcance natural do polegar.

---

## 2. Tokens de Cores Mobile (Design Tokens)

```css
:root {
  /* Superficies e Fundos */
  --bg-mobile-base: #0B0E11;        /* Fundo principal do app */
  --bg-mobile-card: #181A20;        /* Superficie de cards e balões */
  --bg-mobile-header: #12151A;      /* Cabecalho fixo superior */
  --bg-mobile-bottombar: #12151A;    /* Barra inferior fixa de navegacao */
  --bg-mobile-input: #1E2329;       /* Caixa de texto e inputs */
  
  /* Bordas e Divisores */
  --border-subtle: #23272E;         /* Bordas neutras de baixa enfase */
  --border-active: #F0B90B;         /* Destaque dourado da aba ativa */
  
  /* Cores Semanticas de Mercado (OKX Nativo) */
  --gold-primary: #F0B90B;          /* Hermes e acoes principais */
  --green-profit: #0ECB81;          /* Lucro / Comprado / OKX Live */
  --red-loss: #F6465D;              /* Prejuizo / Vendido / Stop */
  --blue-entry: #3888FF;            /* Preco de entrada da ordem */
  
  /* Tipografia */
  --text-bright: #F5F7FA;           /* Precos e titulos */
  --text-normal: #CFD3D8;           /* Mensagens e textos corridos */
  --text-dim: #707A8A;              /* Rótulos e metadados */
}
```

---

## 3. Tipografia e Escalas de Texto
- **Fonte Geral**: `'Inter'`, system-ui, -apple-system, sans-serif.
- **Fonte Numerica (Precos, PnL, Saldos)**: `'JetBrains Mono'`, `'Fira Code'`, monospace.
- **Tamanhos e Pesos**:
  - Saldo de Topo: `18px` | Peso `700` | Família Mono
  - Titulos de Secao: `15px` | Peso `600`
  - Mensagens de Chat: `13.5px` | Peso `400` | Line-height `1.45`
  - Badges e Pills: `11px` | Peso `600` | Letras maiúsculas
  - Metadados e Horarios: `10px` | Família Mono | Cor `--text-dim`

---

## 4. Componentes Chave da Interface Mobile

### 4.1. Barra de Navegacao Inferior (Bottom Tab Bar)
- **Posicao**: Fixa no rodape (`fixed bottom-0 left-0 right-0 z-50`).
- **Altura**: `60px` (+ `env(safe-area-inset-bottom)` para suporte nativo a iPhone).
- **Fundo**: `--bg-mobile-bottombar` com borda superior `1px solid var(--border-subtle)`.
- **5 Botoes de Aba**:
  - Cada botao possui `48x48px` de area de toque minima.
  - Icone SVG (20x20px) centralizado com rotulo de texto `10px` logo abaixo.
  - Aba Ativa: Icone e texto em `--gold-primary` com traco indicador superior dourado de 2px.
  - Abas Inativas: Icone e texto em `--text-dim`.

### 4.2. Cabecalho Superior Fixo (Sticky Header)
- **Posicao**: Fixa no topo (`sticky top-0 z-40`).
- **Altura**: `54px`.
- **Conteudo**:
  - Esquerda: Logo 1CRYPTEN com badge de status WebSocket (ponto verde `animate-pulse`).
  - Direita: Card compacto de Saldo Total da Banca e PnL Flutuante do dia em fonte monospace.

### 4.3. Baloes de Conversa do Hermes
- **Balao do Operador**:
  - Alinhado a direita.
  - Fundo: `#1E2329` com borda sutil `#2B313A`.
  - Texto: `--text-bright` em `13.5px`.
- **Balao do Hermes**:
  - Alinhado a esquerda.
  - Avatar: Circulo preto com borda dourada e letra "H" vetorizada.
  - Fundo: `#181A20` com borda suave dourada `rgba(240, 185, 11, 0.25)`.
  - Nome do assistente em destaque: "HERMES" em dourado `11px` font-bold.
  - Suporte a formatacao markdown clara (negrito, listas e blocos de codigo).

### 4.4. Chips de Acao Rapida (*Quick Prompt Pills*)
- Botoes em formato de capsula horizontal acima da barra de digitacao com rolagem horizontal livre.
- Fundo: `#1E2329`, borda `#2B313A`, texto `--text-normal` em `11px`.
- Efeito ao toque: Destaca instantaneamente com feedback de clique e envia o comando direto ao Hermes.

### 4.5. Seletor de Slot no Grafico Solo
- Barra horizontal logo acima do canvas do grafico.
- Abas tocaveis: `[Slot 1: DOGE]` `[Slot 2: PEPE]` `[Slot 3: SOL]` `[Slot 4: BTC]`.
- Cada aba indica o par e uma pequena bolinha colorida (verde para lucro, vermelha para prejuizo).

### 4.6. Modal de Encerramento de Ordem
- Fundo com efeito de vidro fosco escuro (`bg-black/80 backdrop-blur-sm`).
- Caixa centralizada com largura de 90%, borda vermelha suave `#F6465D/40`.
- Botoes de acao grandes (minimo 48px de altura) com confirmacao explicita.


---

## 5. Padrao Gemini Mobile para Chat de Agentes Autonomos (Hermes Mobile)

> Inspirado no Gemini Mobile oficial e adaptado para o ecossistema 1CRYPTEN (Binance Dark & Gold).

### 5.1. Top Header Minimalista
- Esquerda: Botao Hamburger (SVG) para acionar o Drawer Lateral deslizante.
- Centro: Seletor de Modelo/Agente em dropdown embutido (Hermes Orchestrator, Laya Sniper 15X).
- Direita: Botao de Nova Conversa (lapis SVG) e Avatar circular do Operador com foto real.

### 5.2. Hero State (Estado Inicial Limpo)
- Quando nenhuma mensagem foi enviada ou apos clicar em Nova conversa:
  - Emblema central estilizado do Hermes em ouro e neon suave.
  - Saudacao em tipografia destacada: Ola, Jonatas! No que voce esta pensando?.
  - Oculta-se automaticamente no envio da primeira mensagem para dar lugar ao stream de baloes.

### 5.3. Rodape Flutuante (Capsula de Input Estilo Gemini)
- Estrutura em pilula flutuante (rounded-full) sobre o fundo escuro com elevacao e sombra:
  - Botao + (Abre menu de ferramentas operacionais, RAG e playbooks).
  - Campo de entrada com placeholder contextual (Peca ao Hermes...).
  - Botao de Microfone (ditado de comandos de voz via Web Speech API).
  - Botao circular de Live Audio Waveform (conversa continua por audio).

### 5.4. Drawer Lateral Deslizante (Menu Gemini)
- Desliza da esquerda para a direita cobrindo 84% da tela sobre backdrop com blur:
  - Cabecalho: 1CRYPTEN com botao de fechar.
  - Acao Principal: Botao pilula Nova conversa.
  - Pesquisa: Campo Pesquisar conversas.
  - Atalhos Rapidos: Modulos do ecossistema (Cockpit, Graficos Solo, Custodia, Radar, Base RAG).
  - Secao Recentes: Historico de sessoes conversacionais carregado dinamicamente do SQLite.
  - Rodape Fixo: Perfil do operador (foto do Jonatas Oliveira, nome, selo PRO e icone de configuracoes).

### 5.5. Ausência de Tabbar Inferior (Foco Conversacional Puro)
- Diferente de apps corporativos convencionais que exibem abas fixas no rodapé (Home, Gráficos, Ordens), a experiência Gemini Mobile elimina completamente barras de abas inferiores.
- O rodapé é dedicado com exclusividade à cápsula de entrada flutuante (+, input, mic, áudio live).
- Toda a navegação por módulos (Cockpit Executivo, Gráfico Solo 15X, Custódia & Ordens, Radar de Altcoins) é centralizada no Drawer Lateral (ícone hambúrguer ☰), garantindo 100% de imersão conversacional e fidelidade ao design do Gemini.
