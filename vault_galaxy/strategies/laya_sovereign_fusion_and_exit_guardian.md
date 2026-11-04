# LAYA SOVEREIGN FUSION & COGNITIVE EXIT GUARDIAN (v0.4.22)

**Classificação**: Estratégia Institucional Soberana de Ciclo Fechado  
**Modelos Residentes**: ModernBERT 149M (Multilingual PyTorch) + Hermes Multi-Agent Orchestrator  
**Status**: 100% Operacional em Produção (V188)  

---

## 1. Visão Geral e Filosofia Operacional

A **Laya Soberana v0.4.22** atua em ciclo fechado (End-to-End), eliminando a assimetria entre a abertura de ordens e a gestão dinâmica de risco. O arsenal completo opera sobre três frentes cognitivas:

1. **Frente 1: Exit Guardian Ativo**: Cada posição aberta é avaliada continuamente em todas as iterações do loop.
   - **Garantia de Breakeven (+10% ROI)**: Ao atingir o gatilho de +10.0% de pico de ROI, o stop é reposicionado para cobrir 100% das taxas da OKX e slippage, garantindo lucro líquido positivo (Net PnL > 0).
   - **Trailing Escadinha Progressivo**: Trava lucros crescentes (+18%, +30%, +45% de ROI) conforme a tendência se expande, sem asfixiar o movimento.
   - **Panic Cut Preventivo**: Identifica reversão microestrutural anômala na vela 5M e aborta preventivamente antes do stop loss cheio.
2. **Frente 2: Consenso Neural Laya ⇄ Hermes**: Arbitragem para candidatos limítrofes (score entre 75% e 84%) com confluência macro institucional.
3. **Frente 3: Trade Reflex (Memória Episódica)**: Aplicação de bônus (+6 pts) para pares com histórico vencedor no ciclo e penalidades (-10 a -20 pts) para pares com stop recente.

---

## 2. Invariantes de Entrada (Fusão Águia-Encryptos)

- **Retração 2H**:
  - SHORT: Vela atual testa a SMA 8 abaixo da SMA 21 com alinhamento baixista (`ALIGNED_BEAR`).
  - LONG: Vela atual testa a SMA 8 acima da SMA 21 com alinhamento altista (`ALIGNED_BULL`).
- **Rejeição Microestrutural 5M**: Pavio de rejeição >= 25% na direção oposta ao movimento contra a tendência.
- **Robôs Institucionais**: 1C-EXP 30 (expansão algorítmica de volatilidade) ativado.
- **Trava Anti-Squeeze (LSR)**:
  - Veto a SHORT se LSR < 0.80 (risco de short squeeze institucional).
  - Veto a LONG se LSR > 1.35 (sardinhas amontoadas na compra).
- **Limite Direcional de Cluster**: Máximo de 2 posições abertas na mesma direção.

---

## 3. Telemetria Visual no Cockpit

- **Linha de Stop Dinâmica no Flash Map**: Acompanha o `current_stop` real em tempo real.
  - Muda para **Ciano Neon (`#00F0FF`)** e legenda `PROTEÇÃO BREAKEVEN - RISCO ZERO` quando o capital é blindado.
  - Muda para **Verde Neon (`#00E676`)** e legenda `TRAILING STOP PROTEGIDO` quando o lucro é travado.
  - Mantém linha fantasma pontilhada fina do `STOP INICIAL (SUPERADO)` como prova visual do avanço.
- **Painel de Custódia Geral**: Exibe badges SVG com ícone de escudo `[BREAKEVEN]` e `[TRAILING STOP]`.
- **Balão Cognitivo da Laya**: Modal `#laya-thought-modal` que expõe o racional, convicção e status do Exit Guardian sob demanda.
