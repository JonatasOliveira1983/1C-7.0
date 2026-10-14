# 03 - FLUXO DO APLICATIVO (APP FLOW & USER JOURNEY) - 1CRYPTEN MOBILE

> **Regra de Ouro**: Nenhuma tela, aba ou modal e construida sem que seu gatilho de entrada, comportamento de carregamento, estado vazio, caso de erro e acao de saida estejam detalhados aqui.

---

## 1. Mapa Geral de Navegacao (Mobile Bottom Navigation)

```
[ Acesso /mobile ]
       |
       v
[ Sticky Top Header: Saldo Liquido OKX | PnL do Dia | Status WebSocket ]
       |
       +---> [ ABA 1: HERMES (Home Principal) ] <--- TELA PADRAO INICIAL
       |        |---> Feed Conversacional com Historico SQLite
       |        |---> Chips de Acao Rapida (Banca, Laya, Risco)
       |        |---> Cards Interativos (Atalho para Grafico e Encerramento)
       |        +---> Input de Texto e Comando de Voz
       |
       +---> [ ABA 2: COCKPIT ]
       |        |---> Metricas da Carteira (Equity, Winrate, Margem)
       |        |---> Resumo Compacto dos 4 Slots Operacionais
       |        +---> Telemetria Laya (Regime de Mercado e ADX)
       |
       +---> [ ABA 3: GRAFICO SOLO ]
       |        |---> Seletor Horizontal de Slots [Slot 1] [Slot 2] [Slot 3] [Slot 4]
       |        |---> 1 Canvas TradingView Lightweight Charts Ativo
       |        +---> Linhas de Entrada, Alvo (+5.0%) e Stop (-2.5%)
       |
       +---> [ ABA 4: CUSTODIA & ORDENS ]
       |        |---> Cards Expansiveis de Ordens Abertas na OKX
       |        |---> Detalhes de Entrada, PnL e Alavancagem 15X
       |        +---> Modal de Confirmacao de Encerramento Anti-Erro
       |
       +---> [ ABA 5: RADAR FLASH ]
                |---> Scanner das Altcoins OKX Monitoradas
                +---> Taxas de Financiamento (Funding Rate) e Confluencias
```

---

## 2. Inventario Detalhado por Aba

### Aba 1: HERMES (Home / Pagina Principal)
- **Gatilho de Entrada**: Acesso inicial a `/mobile` ou clique na primeira aba da barra inferior.
- **Objetivo da Tela**: Ser o centro de comando conversacional do operador, onde ele interage com o assistente geral do sistema sobre a banca, diretrizes e atuacao da Laya.
- **Componentes Visiveis**:
  1. Mini-dashboard no topo com Saldo Total e PnL Diario.
  2. Feed de chat scrollavel com mensagens do usuario (alinhadas a direita) e do Hermes (alinhadas a esquerda com badge executivo dourado).
  3. Botoes de acao rapida (*quick prompt pills*):
     - `[Resumo da Banca]` -> Envia pergunta sobre liquidez e exposicao.
     - `[Status da Laya]` -> Consulta acoes taticas da Laya nos 4 slots.
     - `[Auditoria de Risco]` -> Avalia stop loss e margem livre.
  4. Barra de input inferior com campo de digitacao e botao de envio SVG.
- **Comportamento Conversacional**:
  - Quando o operador envia mensagem: adiciona imediatamente o balao do usuario, exibe indicador de digitacao sutil (*shimmer pulse*) e consulta `/api/v1/hermes/chat`.
  - Se a resposta envolver ordens ativas, Hermes retorna tambem um botao de acao rapida inline (ex: *"Ver no Grafico Solo"* ou *"Auditar Posicao"*).

---

### Aba 2: COCKPIT (Visao Geral da Banca)
- **Gatilho de Entrada**: Clique na segunda aba da barra inferior.
- **Objetivo da Tela**: Sintese quantitativa do desempenho operacional.
- **Componentes Visiveis**:
  - Cards de topo: Saldo Liquido, Lucro Total Realizado, Lucro Nao Realizado e Taxa de Acerto.
  - Grade compacta dos 4 slots com cor de destaque:
    - Verde: Ordem em lucro.
    - Vermelho: Ordem em drawdown.
    - Cinza: Slot livre aguardando sinal da Laya.
  - Clique em qualquer card de slot navega diretamente para a **Aba 3 (Grafico Solo)** com aquele par pre-selecionado.

---

### Aba 3: GRAFICO SOLO (Analise Visual Dedicada)
- **Gatilho de Entrada**: Clique na terceira aba ou selecao direta de uma ordem/slot em qualquer outra tela.
- **Objetivo da Tela**: Permitir analise visual de candles sem sobrecarregar a GPU/CPU do celular.
- **Componentes Visiveis**:
  - Seletor horizontal deslizavel no topo: `[Slot 1: DOGE] [Slot 2: PEPE] [Slot 3: SOL] [Slot 4: BTC]`.
  - Area de cabecalho do par: Preco de mercado em tempo real, variacao percentual e preco de entrada.
  - Area grafica com 400px de altura responsiva via Lightweight Charts.
  - Linhas horizontais com tags de preco:
    - Linha Azul: Entrada.
    - Linha Verde/Dourada: Alvo (+5.0% alavancado).
    - Linha Vermelha: Stop Loss (-2.5% alavancado).

---

### Aba 4: CUSTODIA & ORDENS (Manejo Operacional)
- **Gatilho de Entrada**: Clique na quarta aba da barra inferior.
- **Objetivo da Tela**: Supervisao e intervencao direta nas ordens abertas na OKX.
- **Componentes Visiveis**:
  - Lista vertical de cards de ordens ativas.
  - Metricas por ordem: Par, Side (BUY/LONG ou SELL/SHORT), Preco de Entrada, Preco Atual, Lucro Flutuante em Dolar e Percentual.
  - Botao destacado: *"Encerrar Ordem"*.
- **Modal de Confirmacao**:
  - Ao clicar em *"Encerrar Ordem"*, abre modal escuro bloqueador (*overlay*) exibindo:
    - Par e PnL no momento.
    - Alerta: *"Confirma o encerramento imediato a mercado na OKX?"*
    - Botoes: `[Confirmar Encerramento]` (Vermelho) e `[Cancelar]` (Cinza).

---

### Aba 5: RADAR FLASH (Scanner de Altcoins)
- **Gatilho de Entrada**: Clique na quinta aba da barra inferior.
- **Objetivo da Tela**: Monitorar o universo de pares sob analise da Laya.
- **Componentes Visiveis**:
  - Tabela responsiva com as 5 principais altcoins monitoradas (ex: DOGE, PEPE, SOL, BTC, ETH).
  - Colunas: Par, Preco, Variacao 24h, Taxa de Financiamento (*Funding Rate*) e Status da Laya (Monitorando, Confluencia, Em Posicao).

---

## 3. Matriz de Estados e Tratamento de Falhas

| Estado | Comportamento Visual Mobile | Acao Automatica do Sistema |
|---|---|---|
| **Conexao OKX Ativa** | Ponto verde pulsante no topo ("OKX LIVE") | Recebe precos via WebSocket a cada 1s |
| **Queda de Conexao** | Ponto amarelo ("RECONECTANDO...") | Backoff exponencial automatico a cada 3s |
| **Sem Ordens Abertas** | Card de estado vazio: "Nenhum slot ativo no momento. Laya em prontidao no radar." | Mantem radar e escuta de gatilho ativos |
| **Erro na API Hermes** | Toast discreto: "Falha temporaria de comunicacao com Hermes." | Permite reenvio da mensagem sem perder o texto |
