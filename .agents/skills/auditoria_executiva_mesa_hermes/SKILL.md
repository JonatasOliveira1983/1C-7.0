---
name: auditoria_executiva_mesa_hermes
description: Protocolo de auditoria forense autônoma da mesa de trading executado pelo Hermes para gerar o Briefing Executivo diário sem necessidade de prints.
---

# Auditoria Executiva da Mesa e Histórico de Ordens (Hermes Briefing)

### Pra que serve
Auditar a integridade matemática da banca, o risco das ordens vivas em custódia e o histórico recente de trades da Laya, entregando um Briefing Executivo direto ao ponto que atesta se a mesa está segura e prosperando sem necessidade de prints ou intervenção humana.

---

### Quando usar
- Sempre que o operador abrir o chat do Hermes (`/hermes` ou mobile) e solicitar um relatório de status (ex: *"Hermes, como está a mesa?"*, *"Status do sistema"*, *"Relatório diário"*).
- No início da manhã ou na abertura de uma nova sessão de acompanhamento.
- Imediatamente após uma sequência de trades fechados para atestar se o lucro é real e se houve respeito estrito aos stops e quarentenas.

---

### O que precisa
1. **Saldo Realizado e Flutuante**: Endpoint `/api/sandbox/unified-state` (ou `get_sandbox_unified_balance`) e banco local `backend/local_sniper.db`.
2. **Ordens Vivas em Custódia**: Endpoint `/api/slots` e cache de slots ativos (`database_service._last_active_slots_cache`).
3. **Histórico Recente de Trades Fechados**: Tabela de ordens encerradas do SQLite/Postgres com PnL líquido, preços de entrada, saída e motivo de encerramento (`STOP_LOSS`, `TAKE_PROFIT`, `TRAILING_STOP`).
4. **Telemetria de Infraestrutura e Laya**: Endpoint `/api/telemetry/stats` (ping da OKX, vazão de ticks/s, duração do ciclo de varredura dos 507 pares e regime ADX).
5. **Dicionário de Instrumentos OKX**: Especificações de contrato (`ctVal`, `tickSz`, `lotSz`) via `OKXUniverseService`.

---

### Passos da Execução (Na ordem em que o operador confere)

1. **Passo 1: Inspeção da Banca Soberana**
   - Ler o `net_worth_usd` consolidado e decompor em **Saldo Realizado** vs **PnL Flutuante**.
   - Comparar o valor contra o marco de milestone ativo (degraus de $1.000: se entre $10.000 e $10.999, a margem permitida por slot é rigorosamente $100.00).
   - Validar se o lucro acumulado é matematicamente consistente com os trades já encerrados no banco de dados.

2. **Passo 2: Radiografia dos Slots em Custódia Ativa**
   - Mapear cada uma das posições abertas (máximo 8 slots permitidos).
   - Para cada par: conferir se a alavancagem está cravada em 15x (ou 20x conforme especificação), se a margem respeita o teto de $100.00 e qual o PnL flutuante atual ($ e %).
   - Identificar se alguma posição atingiu **-40% ou -50% da margem** e checar onde está o stop de emergência.
   - Auditar o Trailing Stop (*Never Give Back*): verificar se o stop atual (`current_stop`) já subiu para o Break-Even ou para as escadinhas superiores de lucro trancado.

3. **Passo 3: Autópsia Forense dos Últimos Fechamentos**
   - Inspecionar os últimos 3 a 5 trades encerrados.
   - Se o trade fechou no lucro: confirmar se o crédito entrou na banca realizada e se o cálculo respeitou o `ctVal` da OKX (sem distorções de alavancagem).
   - Se o trade fechou no Stop Loss:
     - Conferir se o par entrou imediatamente em **Quarentena Anti-Reincidência de 2 horas** (`7200s`).
     - Investigar o gatilho da entrada: se disparou em direção ao ímã de liquidez dominante (correto) ou contra; e se o rastreio bilateral de Dump/Pump deveria ter abortado o trade precocemente.

4. **Passo 4: Checagem dos Sinais Vitais da Infraestrutura**
   - Aferir o Ping da OKX: se está na zona verde (< 60ms) ou se ativou o Circuit Breaker (> 150ms).
   - Checar se a Laya completou a varredura dos 507 pares dentro do tempo normal (< 90s).

5. **Passo 5: Síntese e Emissão do Briefing Executivo**
   - Carregar o modelo `arquivos/modelo-briefing-executivo.md` e aplicar rigorosamente as diretrizes de `arquivos/regras-de-tom-e-formato.md`.
   - Substituir as lacunas entre colchetes pelos dados reais apurados nos Passos 1 a 4.
   - Apenas emitir o veredito *"Mesa 100% segura e prosperando. Zero intervenção necessária"* se todas as conferências da seção **Pronto quando** passarem com nota 10. Se qualquer teste falhar, apontar a discrepância explicitamente.

---

### Decisões (Se X, então Y)

- **Se PnL Flutuante de uma ordem ativa $\le -45\%$**:
  - *Ação*: Alertar com destaque de atenção no Bloco 2, calcular a distância em dólares até o Stop Loss e auditar se a microestrutura do par formou rejeição ou faca caindo.
- **Se um trade foi fechado em Stop Loss há menos de 2 horas**:
  - *Ação*: Verificar na lista de candidatos da Laya se aquele símbolo está estritamente bloqueado. Se o símbolo estiver reincidindo, acionar trava de emergência no `LayaRouterService`.
- **Se o Ping OKX for $> 150$ms**:
  - *Ação*: Indicar no Bloco 4 que o *Circuit Breaker Anti-Slippage* está travando novos disparos a mercado para proteger o capital.
- **Se houver divergência entre Net Worth e Saldo Realizado do Sandbox**:
  - *Ação*: Sinalizar no Bloco 1 que há discrepância de liquidação e expor a diferença em centavos.
- **Se o lucro recente for anômalo (> 20% em um único scalp)**:
  - *Ação*: Auditar se a OKX não reportou preço espúrio e validar a quantização de lotes (`quantize_order_contracts`) antes de computar como lucro real.

---

### Pronto quando (As Provas Factuais do Estado da Arte)

O Hermes só pode assinar *"Mesa 100% segura e prosperando. Zero intervenção necessária"* se **TODAS** as conferências abaixo forem comprovadas contra dados externos (logs e banco de dados):

1. **[PROVA 1] Prova da Banca Realizada**: O Net Worth reportado no briefing bate no centavo com a soma do saldo realizado no SQLite (`local_sniper.db`) com o floating auditado.
2. **[PROVA 2] Prova da Margem por Slot**: Nenhuma ordem aberta possui margem alocada superior ao milestone ativo ($100.00 para banca entre $10k e $11k).
3. **[PROVA 3] Prova do Anti-Hedge**: Não existem ordens simultâneas de BUY e SELL registradas no mesmo par de moedas.
4. **[PROVA 4] Prova do Never Give Back**: Todo trade que superou o primeiro degrau de ativação tem `current_stop` rigorosamente superior ao preço de entrada (Break-Even protegido).
5. **[PROVA 5] Prova da Quarentena de 2 Horas**: Nenhum par estopado nas últimas 2 horas possui ordem aberta ou elegibilidade ativa na Laya.
6. **[PROVA 6] Prova de Latência OKX**: O ping WebSocket da OKX está abaixo de 120ms e o fluxo de ticks por segundo é $> 0$.
7. **[PROVA 7] Prova de Contrato Físico**: O PnL em dólar de cada trade fechado corresponde à fórmula exata: $(\text{preço\_saída} - \text{preço\_entrada}) \times \text{contratos} \times \text{ctVal}$.

---

### Casos que já deram errado (Os Fantasmas do Passado)

1. **O Stop que Recuava**: O Trailing Stop acompanhava a volatilidade para trás, transformando um trade vencedor em prejuízo.
   - *Blindagem*: A regra *Never Give Back* é unidirecional estrita no código (`new_stop = max(current_stop, calculated_stop)`).
2. **O Hedge Cego**: O sistema abriu LONG e SHORT no mesmo ativo em janelas de tempo diferentes, pagando taxa dupla de financiamento e travando margem.
   - *Blindagem*: Invariante Anti-Hedge checa o inventário de posições antes de qualquer validação tática.
3. **A Quarentena Furada**: Um par levava stop loss e, 3 minutos depois, a Laya via outro gatilho no mesmo candle e entrava de novo, tomando dois stops seguidos.
   - *Blindagem*: Tabela de quarentena com timestamp Unix fixo de 7.200 segundos.
4. **O Lucro Fantasma de Alavancagem**: O sistema calculava contratos considerando moeda linear e a OKX operava em SWAP de cotação inversa ou com `ctVal != 1`, inflando o PnL na tela.
   - *Blindagem*: Auditoria obrigatória do `OKXUniverseService` antes de computar o PnL.
