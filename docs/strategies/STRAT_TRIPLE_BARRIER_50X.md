# STRAT_TRIPLE_BARRIER_50X — ESTRATÉGIA DO MÉTODO DAS TRÊS BARREIRAS (LÓPEZ DE PRADO) 50X

## 1. Identificação Formal
- **ID Canônico**: `STRAT_TRIPLE_BARRIER_50X`
- **Nome**: Triple Barrier Method Volatility & Time Expiry 50X
- **Categoria**: Rotulagem e Gestão Quantitativa de Risco
- **Regime de Mercado**: `TENDENCIA` (ADX $\ge$ 25.0)
- **Alavancagem Fixa Invariante**: 50.0X Isolada (Rigoroso 1Crypten)
- **Embasa Acadêmico**: *Advances in Financial Machine Learning* (Marcos López de Prado, 2018) & *Algorithmic Crypto Trading using Information-Driven Bars* (University of Warsaw, 2024).

---

## 2. Fundamentação Matemática & Arquitetura de Barreiras

Diferente do stop/alvo fixo em pontos ou tempo fixo sem volatilidade, o método das Três Barreiras delimita o espaço de probabilidade em 3 fronteiras dinâmicas:

```
Preço
  ^
  |        [Barreira Superior: TP Dinâmico = Entry + k * ATR]
  |       /
  |------* Entrada (t_0)
  |       \
  |        [Barreira Inferior: Stop Dinâmico Never Give Back]
  +-------------------------------------> Tempo
                                   |
                          [Barreira Temporal: t_0 + N velas]
```

### 2.1 Barreira Superior (Lucro Dinâmico)
Calculada com base na volatilidade realizada via Average True Range (ATR 14 períodos no 15M):

$$\text{TP} = \text{Entry} + k_{\text{ATR}} \times \text{ATR}_{15M}$$

Onde $k_{\text{ATR}} = 2.5$. Com alavancagem 50X, a barreira superior mira expansões de ROI entre $+30\%$ e $+80\%$.

### 2.2 Barreira Inferior (Proteção Never Give Back)
- **Fase Inicial**: Stop estrutural abaixo do suporte (buffer de $0.3\%$ a $0.5\%$, limitando perda máxima inicial).
- **Fase de Escada**: Atingindo limiares de ROI ($+15\%$, $+25\%$, $+40\%$, $+60\%$, $+80\%$), o stop de proteção é recalculado exclusivamente para cima:

$$\text{Stop}_{t+1} = \max(\text{Stop}_t, \text{Escadinha}(\text{ROI}_t))$$

### 2.3 Barreira Temporal (Time Expiry / Anti-Drawdown)
- Se a posição não alcançar nem o TP superior nem for stopada dentro de $N = 16$ barras de 15 minutos (4 horas operacionais), a inércia do trade expirou.
- O algoritmo fecha preventivamente a ordem a mercado para liberar o slot e o colateral, prevenindo cauda longa de risco.
