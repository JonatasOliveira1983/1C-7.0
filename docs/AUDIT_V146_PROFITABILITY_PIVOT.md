# AUDITORIA E REGISTRO DE TRANSIÇÃO: V146 - PIVOT DE RENTABILIDADE E RISCO/RETORNO (R:R > 2:1)

Data: 2026-10-05  
Autor: Equipe de Engenharia / Antigravity Agent  
Status: APLICADO E REGISTRADO  

---

## 1. Diagnóstico Forense Pré-Intervenção (Baseline Empírico)

Auditoria realizada diretamente sobre o banco SQLite de produção local (`local_sniper.db`) e telemetria do Cockpit em 2026-10-05.

### 1.1 Métricas de Scalping (`sandbox_trades`) — 68 Trades Fechados
- **Total de Trades**: 68
- **Taxa de Acerto (Win Rate Real)**: 48.5% (33 vitórias / 35 derrotas)
- **PnL Total Realizado**: -$366.87
- **Ganho Médio por Vitória**: +4.57% (+$9.13)
- **Perda Média por Derrota**: -9.55% (-$19.09)
- **Payoff Ratio (Ganho Médio / Perda Média)**: 1 : 2.09 **INVERSO** (Perda média é 2.09x maior que o ganho médio)
- **Win Rate Mínimo Matemático para Breakeven**: **67.6%**
- **Viés Direcional**: 80.9% SHORT (55 vendas vs 13 compras)
- **Peak Drawdown Intra-Trade Médio**: 9.64% de ROI devolvidos antes do fechamento.

### 1.2 Métricas de Swing (`sandbox_swing_trades`) — 7 Trades Fechados
- **Total de Trades**: 7
- **Taxa de Acerto**: 28.6% (2 vitórias / 5 derrotas)
- **PnL Total Realizado**: -$92.42
- **Ganho Médio por Vitória**: +5.72% (+$6.72)
- **Perda Média por Derrota**: -12.55% (-$21.17)
- **Pior Perda**: -22.46% (-$26.39) no FETUSDT
- **Desperdício de Lucro**: Média de 28.91% de ROI devolvidos a partir da máxima (ex: THETA bateu +32.11% e fechou no 0.00%; XRP bateu +31.41% e fechou em -0.10%).

### 1.3 As Causas Raízes Comprovadas
1. **Assimetria R:R Invertida**: As derrotas custam o dobro das vitórias. Um stop de -10% destrói duas vitórias de +5%.
2. **Asfixia de Lucro**: O trailing stop subia prematuramente para +1.5% ao atingir +6% de ROI, sendo expulso pelo ruído de mercado (spread).
3. **Short-Bias Artificial**: Regra fixa `if lsr >= 1.35: SHORT` forçou 81% de vendas em contratendência.
4. **Níveis S/R Estáticos**: Valores hardcoded defasados em `laya_router_service.py`.
5. **Stop Loss Inicial Excessivo**: Stops iniciais permitiam perdas de até -12% no Scalp e -22% no Swing.

---

## 2. Mudanças Estruturais Aplicadas (V146)

### 2.1 Re-calibração do Risk/Reward em `backend/services/order_projection_service.py`
- **Escadinha Laya Reversion**:
  - Nível 1: Disparo em +10.0% ROI -> Stop travado em +2.0% (cobre taxas e spread, não asfixia em +6%).
  - Nível 2: Disparo em +18.0% ROI -> Stop travado em +8.0% (garante vitória real de 8%).
  - Nível 3: Disparo em +28.0% ROI -> Stop travado em +18.0%.
  - Nível 4: Disparo em +42.0% ROI -> Stop travado em +30.0%.
  - Nível 5 (Trailing): Disparo em +60.0% ROI -> Stop travado em +45.0%.
- **Escadinha Swing Lab**:
  - Nível 1: Disparo em +15.0% ROI -> Stop travado em +2.0%.
  - Nível 2: Disparo em +25.0% ROI -> Stop travado em +12.0% (impossibilita devoluções de trades de +30% para zero).
  - Nível 3: Disparo em +40.0% ROI -> Stop travado em +25.0%.
  - Nível 4: Disparo em +65.0% ROI -> Stop travado em +45.0%.
  - Nível 5 (Trailing): Disparo em +90.0% ROI -> Stop travado em +70.0%.

### 2.2 Redução Drástica dos Stops Iniciais
- **Scalping Lab (`backend/services/sandbox_service.py`)**:
  - `fallback_roi` reduzido de -12.0% para -6.5%.
  - `limit_roi` reduzido de -12.0% para -7.0% (teto rígido inviolável).
  - Limite ATR ajustado para a faixa [-7.0%, -5.0%].
- **Swing Lab (`backend/services/sandbox_swing_service.py`)**:
  - `stop_roi_target` reduzido de 20.0% para 10.0%.

### 2.3 Dinamização dos Canais e Fim do Short-Bias Cego (`backend/app/services/laya_router_service.py`)
- Remoção dos suportes e resistências estáticos hardcoded (`base_sr`).
- Cálculo dinâmico do canal de consolidação a partir das cotações reais `high24h`, `low24h` e `last`.
- O LSR agora é confluenciado com a posição do preço no canal: só abre SHORT se o preço estiver no topo do canal (`price >= mid_ref`). Se estiver na mínima do canal, prioriza LONG mesmo com LSR de sardinha elevado.

---

## 3. Metas Quantitativas para Validação Pós-Mudança

Nos próximos 30 a 50 trades a serem executados a partir desta versão:
- [ ] **Ganho Médio por Vitória**: $\ge +8.0\%$ ROI
- [ ] **Perda Média por Derrota**: $\le -7.0\%$ ROI
- [ ] **Payoff Ratio**: $\ge 1.2 : 1$ a favor do sistema
- [ ] **Trades Vencedores Devolvidos no Zero**: Redução para $< 10\%$
- [ ] **Curva de Patrimônio**: Reversão da inclinação para viés positivo.
