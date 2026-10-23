# BLUEPRINT 09 — MOTOR DE PRECISÃO DE CONTRATOS & QUANTIZAÇÃO OKX (507 PARES)

> **Status**: Ativo & Sincronizado  
> **Versão**: 1.0.0 (V164-CANONICAL)  
> **Escopo**: Laya Soberana, Hermes Compliance Agent, OKXUniverseService, OKXRestService, Cockpit UI.

---

## 1. Visão Geral e Motivação

O **1Crypten** monitora mais de 500 pares de contratos derivativos perpétuos (`USDT-SWAP`) na OKX em busca de ignição de robôs institucionais (`1C-EXP` >= 70).

No entanto, no mercado de derivativos futuros da OKX, **cada ativo possui regras de contrato rigidamente distintas**:
1. **Ativos de Micro-Cotação** (ex.: `PEPE-USDT-SWAP`, `SHIB-USDT-SWAP`, `BONK-USDT-SWAP`):
   - Preços cotados em 8 casas decimais (`0.00000951`).
   - Um arredondamento fixo clássico de 4 casas decimais (`round(p, 4)`) resulta em `0.0000` ou `0.0001`, destruindo completamente os cálculos de Stop Loss e Take Profit.
2. **Ativos de Grande Capitalização** (ex.: `BTC-USDT-SWAP`):
   - Preço cotado em 1 casa decimal (`tickSz = 0.1`).
   - O envio de ordens com mais casas decimais acarreta em rejeição imediata pela OKX com código de erro `51001: Order price does not meet the minimum tick size`.
3. **Multiplicador de Contrato (`ctVal`)**:
   - As ordens perpétuas da OKX são enviadas em **contratos (`sz`)**, e não em valor bruto de USDT.
   - 1 contrato de `PEPE-USDT-SWAP` = `10.000.000 PEPE`.
   - 1 contrato de `BTC-USDT-SWAP` = `0.01 BTC`.
   - 1 contrato de `DOGE-USDT-SWAP` = `100 DOGE`.
   - 1 contrato de `LINK-USDT-SWAP` = `1 LINK`.

---

## 2. Fórmulas Canônicas de Engenharia

### 2.1. Precision Engine de Preço (`format_price_by_tick`)

Dado um preço $P$ e o passo de tick oficial do contrato $T$ (`tickSize`):

$$\text{Steps} = \text{round}\left(\frac{P}{T}\right)$$
$$P_{\text{normalizado}} = \text{round}\left(\text{Steps} \times T, \, D\right)$$

Onde $D$ é a quantidade de casas decimais inferida pelo expoente de base 10 de $T$:

$$D = \max\left(0, \, -\lfloor \log_{10}(T) \rfloor\right)$$

### 2.2. Quantizador de Contratos (`quantize_order_contracts`)

Dado o capital de margem alocado $M$ (ex.: $100.00 USD), a alavancagem permitida $L$ (ex.: 15x), o preço do ativo $P$, o multiplicador do contrato $C_{\text{val}}$, o tamanho do lote $L_{\text{sz}}$ e o tamanho mínimo $S_{\text{min}}$:

1. **Notional Alvo em USD**:
   $$N_{\text{target}} = M \times L$$

2. **Custo Nocional de 1 Contrato**:
   $$K_{\text{contract}} = P \times C_{\text{val}}$$

3. **Contratos Brutos**:
   $$Q_{\text{raw}} = \frac{N_{\text{target}}}{K_{\text{contract}}}$$

4. **Quantização de Lote**:
   $$Q_{\text{quantized}} = \text{round}\left(\frac{Q_{\text{raw}}}{L_{\text{sz}}}\right) \times L_{\text{sz}}$$

5. **Notional Efetivo e Margem Real**:
   $$N_{\text{efetivo}} = Q_{\text{quantized}} \times K_{\text{contract}}$$
   $$M_{\text{efetiva}} = \frac{N_{\text{efetivo}}}{L}$$

6. **Critérios de Validação / Sanity Gate**:
   - $Q_{\text{quantized}} \ge S_{\text{min}}$ (respeita ordem mínima da exchange).
   - $M_{\text{efetiva}} \le M \times 1.50$ (impede que o arredondamento aumente o risco acima de 50%).

---

## 3. Matriz de Amostragem dos Contratos OKX

| Par | Multiplicador (`ctVal`) | Moeda do Contrato | Passo de Preço (`tickSz`) | Lote Mínimo (`lotSz`) | Casas Decimais |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PEPE-USDT-SWAP** | 10.000.000,0 | PEPE | `0.00000001` | 1,0 contrato | 8 casas |
| **SHIB-USDT-SWAP** | 1.000.000,0 | SHIB | `0.00000001` | 1,0 contrato | 8 casas |
| **DOGE-USDT-SWAP** | 100,0 | DOGE | `0.00001` | 1,0 contrato | 5 casas |
| **BTC-USDT-SWAP** | 0,01 | BTC | `0.1` | 0,01 / 1,0 contrato | 1 casa |
| **ETH-USDT-SWAP** | 0,10 | ETH | `0.01` | 0,01 / 1,0 contrato | 2 casas |
| **LINK-USDT-SWAP** | 1,0 | LINK | `0.001` | 0,1 / 1,0 contrato | 3 casas |
| **ARB-USDT-SWAP** | 10,0 | ARB | `0.0001` | 1,0 contrato | 4 casas |
| **INJ-USDT-SWAP** | 0,1 | INJ | `0.001` | 1,0 contrato | 3 casas |

---

## 4. Integração Operacional com os Agentes

### 4.1. Laya Soberana (`LayaRouterService`)
- **Stops e Alvos Dinâmicos**: Em vez de `round(..., 4)`, a Laya invoca `okx_universe_service.format_price_by_tick(symbol, price)`.
- **Sanity Gate de Margem**: Antes de emitir qualquer ordem, a Laya valida se `quantize_order_contracts` retornou `is_valid == True`. Se a banca for insuficiente para comprar 1 contrato mínimo (ex.: em pares muito pesados), a ordem é vetada preventivamente com tag `[VETO CONTRATO OKX]` sem abrir ordens deformadas.

### 4.2. Hermes Agent (`HermesAgent`)
- O agente Hermes atua como Auditor de Compliance em tempo real.
- Suporta perguntas de auditoria no chat:
  - `"qual o tick size do pepe?"`
  - `"auditar contrato doge"`
  - `"precisao do contrato btc"`
- Responde com a ficha técnica canônica (ctVal, lotSize, minSz, tickSize e notional efetivo).

---

## 5. Invariantes Rígidas de Trading

1. **Zero Emojis**: Toda a saída de logs e telemetria utiliza exclusivamente notação técnica e ícones SVG na UI.
2. **Never Give Back**: O stop nunca recua e o Breakeven é ancorado no preço exato normalizado pelo tick.
3. **Anti-Hedge**: Uma única posição direcional por ativo em todos os 507 pares.
