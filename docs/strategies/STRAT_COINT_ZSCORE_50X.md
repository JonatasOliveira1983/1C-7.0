# STRAT_COINT_ZSCORE_50X — ESTRATÉGIA DE PAIRS TRADING, COINTEGRAÇÃO E Z-SCORE 50X

## 1. Identificação Formal
- **ID Canônico**: `STRAT_COINT_ZSCORE_50X`
- **Nome**: Statistical Arbitrage Cointegration & Z-Score Mean Reversion 50X
- **Categoria**: Arbitragem Estatística / Reversão à Média
- **Regime de Mercado**: `LATERAL` (ADX < 25.0)
- **Alavancagem Fixa Invariante**: 50.0X Isolada (Rigoroso 1Crypten)
- **Embasa Acadêmico**: *Crypto Trading Strategies* (Stanford University MS&E 448, 2021) & *Algorithmic Trading & DMA* (Barry Johnson, 2010).

---

## 2. Fundamentação Matemática & Teórica

### 2.1 Cointegração de Clusters Cripto
Diferente da mera correlação móvel (que é instável e vulnerável a spúrios), duas séries temporais $P_A(t)$ e $P_B(t)$ de ativos do mesmo setor (ex: SOL/NEAR, DOT/ADA, LTC/XLM) são cointegradas de ordem $CI(1,1)$ se existir um coeficiente linear $\beta$ tal que os resíduos do spread sejam estacionários:

$$\text{Spread}(t) = P_A(t) - \beta P_B(t)$$

O teste de estacionariedade de Engle-Granger / Augmented Dickey-Fuller (ADF) deve satisfazer:
$$p\text{-value} < 0.05$$

### 2.2 Normalização via Z-Score Dinâmico
O spread normalizado é calculado comparando a média móvel curta (6 horas) com a média e desvio padrão de referência longa (72 horas):

$$Z(t) = \frac{\mu_{6h}(\text{Ratio}) - \mu_{72h}(\text{Ratio})}{\sigma_{72h}(\text{Ratio})}$$

Onde $\text{Ratio}(t) = \frac{P_A(t)}{P_B(t)}$.

---

## 3. Regras Operacionais Estritas (50X Isolada)

### 3.1 Gatilhos de Entrada
1. **Divergência Superior ($Z \ge +2.0$)**:
   - Ativo $A$ está sobrecomprado relativo a $B$; ativo $B$ está sobrevendido relativo a $A$.
   - **Ação 1Crypten Anti-Hedge**: A Laya seleciona o ativo com maior assimetria e liquidez e executa ordem direcional individual (evitando ordens opostas no mesmo par). Para ativo sobrecomprado em topo de canal: executa **SHORT 50X**.
2. **Divergência Inferior ($Z \le -2.0$)**:
   - Ativo $A$ está severamente descontado relativo a $B$.
   - **Ação 1Crypten**: Executa **LONG 50X** na absorção de suporte.

### 3.2 Regras de Saída & Proteção de Capital
1. **Take Profit (Retorno à Média)**:
   - Saída primária quando $Z(t)$ cruza $0.0$ (reversão completa à média histórica).
2. **Stop Loss Estatístico (Corte de Rompimento)**:
   - Se $|Z(t)| \ge 3.2$, a hipótese de cointegração é invalidada (quebra estrutural de correlação). Fechamento imediato a mercado.
3. **Never Give Back (Trailing 5 Escadinhas)**:
   - Assim que o ROI atinge +15%, ativa o primeiro degrau (+5% garantido). O stop só sobe e nunca recua.
