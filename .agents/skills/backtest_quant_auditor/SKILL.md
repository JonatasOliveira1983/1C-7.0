---
name: backtest_quant_auditor
description: Protocolo de auditoria e validacao quantitativa de estrategias de trading para o 1Crypten sob 50X Margem Cruzada na OKX. Evita overfitting, aplica testes de estresse com friccao real (slippage e taxas taker), exige analise walk-forward e checa sensibilidade de parametros antes de qualquer alteracao no motor de producao.
---

# Backtest Quant Auditor — Protocolo de Validacao Anti-Overfitting

## Proposito

Auditar e validar qualquer hipotese ou refinamento de estrategia no 1Crypten antes de sua aplicacao em producao. O objetivo nao e encontrar a estrategia que "lucra mais no papel" com parametros superotimizados (curva ajustada), mas sim a estrategia que **menos quebra** sob condicoes adversas de mercado.

## Filosofia Inegociavel

1. **Adicionar Friccao Real**: O backtest deve sempre incluir taxas taker reais da OKX (0.10% ida e volta = $1.000 em lote de $500.000 nocional), slippage de livro (0.025% a 0.10%) e debito/credito de funding rates a cada 8 horas.
2. **Respeitar o Teto Rigido 50X (V226)**: Nenhuma hipotese e valida se exigir stop loss superior a 0.70% de preco (max -35.0% de ROI no lote de $10.000).
3. **Platos vs Picos Estreitos**: Rejeitar conjuntos de parametros que funcionam apenas em valores exatos (ex: stop de 0.62% funciona mas 0.60% quebra). Buscar sempre platos estaveis de rentabilidade.

## Quando Usar Esta Skill

- Antes de alterar qualquer regra de gatilho, stop loss ou trailing em `laya_router_service.py` ou `sandbox_service.py`.
- Quando um novo padrao de repique, rompimento ou reversao for proposto para a Laya ou o Titan Engine.
- Apos uma sequencia de perdas para diagnosticar se a falha decorreu de variancia normal ou de quebra estrutural de edge.
- Na avaliacao de novos pares para inclusao na lista dos 30 Titas.

## Fluxo Operacional em 5 Fases

### Fase 1: Declaracao Formal da Hipotese
Definir a vantagem estatistica (edge) em uma unica frase sem ambiguidade.
Exemplo:
"Em regime macro de baixa (BTC abaixo da SMA 21 no 2H), altcoins com score >= 85 que repicam na SMA 8 ou SMA 21 de 30M com pavio de rejeicao >= 25% oferecem expectativa matematica positiva de SHORT com alvo minimo de +60% a +300% de ROI."

### Fase 2: Codificacao Deterministica sem Julgamento Subjetivo
Mapear exatamente:
- **Gatilho de Entrada**: Preco, candle de 30M, confluencias tecnicas minimas (>= 3).
- **Stop Loss Inicial**: Ancorado na microestrutura do repique (SMA 21 + 0.25%), estritamente travado em <= 0.70% de distancia (`max_stop_dist = 0.0070`).
- **Escadinha de Protecao**: Degrau 1 (+45% ROI -> trava +18%), Degrau 2 (+60% ROI -> trava +30%), Trailing dinamico a partir de +100% ROI com gap elastico de 50%.
- **Alocacao**: Lote fixo de $10.000 de margem cruzada ($500.000 nocional) na banca de $100.000 (regra 2+2+2+2).

### Fase 3: Simulacao com Friccao Institucional
Rodar o backtest historico cobrindo:
- **Amostra Minima**: Pelo menos 50 trades em dados historicos da OKX (ou 30 dias de klines de 30M/2H).
- **Multiplos Regimes**: Mercado em tendencia de alta, mercado em tendencia de baixa e consolidacao lateral.
- **Deducao Obrigatoria de Custos**:
  - Taxa Taker OKX: 0.05% na abertura + 0.05% no fechamento (0.10% total = $500 / 5.0% de ROI).
  - Slippage de Livro: Tier 1 (0.025%), Tier 2 (0.05%), Tier 3 (0.10%).
  - Taxa de Financiamento (Funding Rate): Media historica de 0.01% por ciclo de 8h.

### Fase 4: Teste de Sensibilidade de Parametros (Stress Testing)
Variar sistematicamente os parametros para testar a robustez:
- Stop Loss: Testar a 0.50%, 0.60%, 0.70%. Se o resultado desabar com pequenas variacoes, a estrategia e fragil (curve-fitted).
- Gatilho de Pavio: Testar variacoes de 15%, 20%, 25%, 30%.
- Horarios de Execucao: Avaliar desempenho em sessoes distintas (Asia, Londres, Nova York).

### Fase 5: Validacao Walk-Forward e Out-of-Sample
Dividir a base historica em:
1. **In-Sample (Treinamento)**: 70% dos dados para calibracao de limiares.
2. **Out-of-Sample (Validacao Cega)**: 30% dos dados subsequentes sem reajuste de parametros.

**Criterios de Aprovacao**:
- Rentabilidade Out-of-Sample deve ser de pelo menos 60% do resultado In-Sample.
- Max Drawdown da banca nao pode exceder $15.000 (-15.0% da banca de $100k).
- Expectativa Matematica Liquida (Expectancy) por trade deve ser >= +$350.00 (positivo apos taxas).
- Profit Factor liquido >= 1.50.

## Metricas Obrigatorias no Relatorio

- **MAE (Maximum Adverse Excursion)**: Mediana do drawdown flutuante das ordens vencedoras (se for > 0.40% de preco, o timing de entrada esta atrasado).
- **MFE (Maximum Favorable Excursion)**: Mediana do pico de lucro alcancado antes do fechamento (avalia se os stops de trailing estao asfixiando os ganhadores).
- **Taxa de Acerto Real (Win Rate)**: Porcentagem de trades fechados em lucro liquido apos taxas.
- **Relação Ganho Medio / Perda Media**: Deve ser estritamente superior a 1.5:1.
