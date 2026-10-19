# 🛡️ Estratégia Canônica: Tríade de Blindagem Institucional, Descorrelação de Carteira e Veto por Dominância do BTC (V162)

> **Status:** Ativo / Fonte Canônica de Verdade no Segundo Cérebro (RAG)
> **Data:** 19 de Outubro de 2026
> **Responsável:** Laya Sovereign Brain / 1Crypten 7.0

---

## 1. Visão Geral e Princípio de Preservação de Capital

A evolução V162 resolve os pontos de vulnerabilidade identificados na operação contínua de 24h da Laya Soberana (+2.52% de ganho líquido acumulado). O objetivo é garantir **expectativa matemática positiva contínua**, impedindo drawdowns gerados por falsos rompimentos, armadilhas de venda contra o rali do BTC e clusters de ativos correlacionados.

---

## 2. A Matriz de Clima por Dominância do BTC (BTC.D)

O Bitcoin atua como bússola inter-mercado. A Laya cruza em tempo real a variação de preço do BTC com a Dominância (`BTC.D`):

1. **`BTC_DRAINAGE` (Bitcoin como Buraco Negro de Liquidez)**:
   - **Condição**: BTC positivo (`>= +0.3%` ou `btc_trend_bias >= +0.3%`) com Dominância alta (`>= 59.0%` ou subindo `RISING`).
   - **Comportamento**: **VETO ABSOLUTO DE SHORTS EM ALTCOINS**. Proibido abrir ordens de venda a descoberto enquanto o BTC drena capital para cima.
2. **`ALTCOIN_EXPANSION` (Altseason / Transbordamento de Liquidez)**:
   - **Condição**: Dominância em queda (`< 56.5%` ou `FALLING`) com BTC estável ou positivo.
   - **Comportamento**: Compras (LONG) em 15x totalmente liberadas para capturar assimetrias de +40% a +75%. SHORTs vetados.
3. **`ALTCOIN_BLOODBATH` (Sangria Institucional de Altcoins)**:
   - **Condição**: BTC em queda (`< -1.0%`) com Dominância em alta (`>= 58.5%` ou `RISING`).
   - **Comportamento**: **VETO TOTAL DE COMPRAS (LONG)**. Proibido pegar faca caindo. Apenas vendas (SHORT) autorizadas a favor do fluxo.
4. **`CONSOLIDATION_CHOP` (Mercado Lateral Neutro)**:
   - **Condição**: Mercado sem tendência forte.
   - **Proteção Assimétrica**: Se `BTC.D >= 58.0%` e o BTC estiver verde (`> +0.2%`), SHORTs em altcoins também são preventivamente bloqueados.

---

## 3. Os 3 Pilares da Tríade de Blindagem

### Pilar 1: Circuit Breaker Global Anti-Tilt
- **Mecanismo**: Rastreador temporal em janela rolante de 90 minutos (5.400s).
- **Gatilho**: Ocorrência de **3 stops quaisquer no intervalo**.
- **Ação**: Congelamento de **100% de novas aberturas por 45 minutos (2.700s)**, permitindo o resfriamento da banca e a passagem de choques exógenos de mercado.

### Pilar 2: Descorrelação Setorial entre os 4 Slots
- **Mapeamento de 5 Clusters Setoriais**:
  - `L1_BLUECHIP`: `ETH`, `SOL`, `NEAR`, `SUI`, `AVAX`, `ADA`, `DOT`, `ATOM`, `LTC`, `BCH`, `XRP`, `TRX`
  - `L2_ROLLUPS`: `ARB`, `OP`, `ZK`, `POL`, `STRK`, `XPL`
  - `DEFI_ORACLE`: `UNI`, `AAVE`, `MKR`, `PYTH`, `PENDLE`, `ONDO`, `INJ`, `CRV`, `DYDX`, `GMX`
  - `AI_DEPIN`: `RENDER`, `FET`, `TIA`, `AR`, `TAO`, `ICP`
  - `MEME_SPEC`: `DOGE`, `PEPE`, `WIF`, `BONK`, `GALA`, `AXS`, `SAND`, `CHZ`
- **Teto Inegociável**: Máximo de **2 posições simultâneas do mesmo cluster**. Impede que 4 ativos caiam e estopem sincronizados sob um mesmo choque de setor.

### Pilar 3: Confirmação de Agressão de Volume / CVD nas Bordas H1
- **Gatilho no Suporte H1 (LONG)**: Se o candle recente apresentar agressão vendedora desbalanceada (`taker_sell_ratio >= 1.40x`), o sinal é vetado por *Faca Caindo*.
- **Gatilho na Resistência H1 (SHORT)**: Se o topo apresentar agressão compradora acelerada (`taker_buy_ratio >= 1.40x`), o sinal é vetado por *Pressão Compradora Ativa*.
