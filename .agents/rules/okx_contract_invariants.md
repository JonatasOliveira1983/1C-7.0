# Regra Fundamental: Invariantes de Contratos e Execução OKX SWAP

> **DOCUMENTAÇÃO E MEMÓRIA SISTÊMICA PERMANENTE (RAG / REGRAS DE AGENTE)**  
> **NUNCA IGNORAR OU SOBRESCREVER ESTAS DIRETRIZES DE MERCADO.**

---

## 1. Especificação de Contratos Perpétuos OKX (SWAP Linear USDT)

Na OKX, ordens de futuros perpétuos operam exclusivamente em **número de contratos** (`sz`), e NÃO em quantidade direta de moedas ou dólares.

Cada instrumento possui especificações imutáveis fornecidas pela API pública da OKX (`/api/v5/public/instruments?instType=SWAP`):
- `ctVal` (Contract Value): Quantidade de moedas que 1 contrato representa.
- `lotSz` (Lot Size): Passo mínimo de incremento no número de contratos.
- `minSz` (Minimum Size): Quantidade mínima de contratos por ordem.
- `tickSz` (Tick Size): Variação mínima de preço (casas decimais).

### Tabela Oficial de Referência OKX SWAP
| Instrumento | `ctVal` | O que representa 1 contrato | `lotSz` | `minSz` | `tickSz` |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BTC-USDT-SWAP** | **0.01 BTC** | 1 contrato = 0,01 BTC | 0.01 | 0.01 | **0.1** |
| **ETH-USDT-SWAP** | **0.1 ETH** | 1 contrato = 0,10 ETH | 0.01 | 0.01 | **0.01** |
| **SOL-USDT-SWAP** | **1.0 SOL** | 1 contrato = 1 SOL | 0.01 | 0.01 | **0.01** |
| **NEAR-USDT-SWAP**| **10.0 NEAR**| 1 contrato = 10 NEAR | 0.1 | 0.1 | **0.001** |
| **AVAX-USDT-SWAP**| **1.0 AVAX** | 1 contrato = 1 AVAX | 0.1 | 0.1 | **0.001** |
| **LINK-USDT-SWAP**| **1.0 LINK** | 1 contrato = 1 LINK | 0.1 | 0.1 | **0.001** |
| **DOGE-USDT-SWAP**| **100.0 DOGE**| 1 contrato = 100 DOGE | 1.0 | 1.0 | **0.00001** |
| **PEPE-USDT-SWAP**| **10.000.000**| 1 contrato = 10M PEPE | 1.0 | 1.0 | **0.00000001**|
| **SHIB-USDT-SWAP**| **1.000.000** | 1 contrato = 1M SHIB | 1.0 | 1.0 | **0.00000001**|
| **JTO-USDT-SWAP** | **1.0 JTO**  | 1 contrato = 1 JTO | 1.0 | 1.0 | **0.0001** |
| **DOT-USDT-SWAP** | **1.0 DOT**  | 1 contrato = 1 DOT | 0.1 | 0.1 | **0.001** |

---

## 2. Invariante Matemática de Dimensionamento de Ordens

Para qualquer trade (seja em Paper Trading ou Conta Real), a quantidade de contratos (`sz`) DEVE ser calculada obrigatoriamente por:

$$\text{Nocional (USD)} = \text{Margem} \times \text{Alavancagem}$$
$$\text{Quantidade Bruta} = \frac{\text{Nocional}}{\text{Preço de Entrada} \times \text{ctVal}}$$
$$\text{sz (Contratos)} = \max\left(\text{minSz}, \left\lfloor \frac{\text{Quantidade Bruta}}{\text{lotSz}} \right\rfloor \times \text{lotSz}\right)$$

### Proibições Absolutas:
1. **É PROIBIDO** assumir `ctVal = 1.0` de forma genérica para moedas com contratos agrupados (como NEAR com 10, BTC com 0.01 ou PEPE com 10.000.000).
2. **É PROIBIDO** forçar `tickSize = 0.1` arbitrário em altcoins. O `tickSize` deve ser rigorosamente o do ativo (ex: `0.001` em NEAR, AVAX e LINK).
3. **É PROIBIDO** ignorar a API pública da OKX sob a justificativa de "modo mock" — a consulta de especificações de instrumentos é pública e deve ser realizada mesmo em simulação.

---

## 3. Invariante de Simulação Realista (Paper Trading)

Toda e qualquer simulação de saldo ou PnL no Sandbox DEVE obrigatoriamente deduzir os custos operacionais reais:
1. **Taxa de Entrada (OKX Taker)**: $0,05\%$ sobre o volume nocional.
2. **Taxa de Saída (OKX Taker)**: $0,05\%$ sobre o volume nocional.
3. **Slippage Estimada**: Mínimo de $0,03\%$ sobre o volume nocional no fechamento a mercado.
4. **Alavancagem 15X**: Em 15X, o custo total de taxas + slippage equivale a aproximadamente **$1,95\%$ de ROI da margem** que deve ser deduzido do PnL de cada trade.
