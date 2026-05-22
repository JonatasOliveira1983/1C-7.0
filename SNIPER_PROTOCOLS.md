# 1CRYPTEN_SPACE_V4.0 - PROTOCOLO DE SOBERANIA (V110.668)

## 🎯 Arquitetura da Escadinha (Trailing Stop Progressivo)

O sistema opera sob o conceito de **Single Source of Truth (SSOT)** centralizado no `ProtocolRegistry`.

### 1. Gatilhos de ROI e Proteção
| Fase | Gatilho (ROI %) | Proteção SL (ROI %) | Status UI |
| :--- | :--- | :--- | :--- |
| **T1: Break-Even** | 30% | 0% | `BREAKEVEN` |
| **T2: Profit Bridge**| 50% | 20% | `PROFIT_BRIDGE`|
| **T3: Risk-Zero** | 70% | 5% | `RISK_ZERO` |
| **T4: Profit-Lock** | 110% | 70% | `PROFIT_LOCK` |
| **T5: Emancipação** | 150% | 110% | `EMANCIPATED` |

### 2. Simetria Operacional (Long vs Short)
O sistema é 100% simétrico.
- **LONG (Buy)**: O Stop Loss é movido para **CIMA** conforme o preço sobe.
- **SHORT (Sell)**: O Stop Loss é movido para **BAIXO** conforme o preço desce.
- **ROI**: Calculado de forma absoluta. `+150%` em Short significa que o preço caiu o suficiente para atingir o alvo alavancado.

### 3. Performance de Monitoramento
- **Frequência**: O loop de monitoramento (`SlotOperatorAgent`) roda a cada **0.2 segundos**.
- **Garantia**: Alta reatividade para capturar "pavilhões" (wicks) rápidos e disparar a emancipação.

### 4. Protocolo de Reset Nuclear
Para limpar o sistema e iniciar um novo ciclo de testes:
```powershell
python 1CRYPTEN_SPACE_V4.0/backend/nuclear_reset.py
```
*Ação: Cancela ordens, limpa slots, reseta banca para $100 e apaga histórico.*

---
**Status: ESTÁVEL | Versão: V110.668**
