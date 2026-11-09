# METODOLOGIA SUPERPOWERS — REGRAS DE ENGENHARIA AGÊNTICA PARA 1CRYPTEN

> **Status**: Regras Canônicas e Inegociáveis para Todos os Agentes de IA que operam no 1Crypten.
> **Fonte de Verdade Técnica**: `MASTER_ARCHITECTURE.md`.

---

## 1. Princípios Fundamentais de Engenharia

1. **Especificação & Planejamento Antes do Código**:
   - Nenhuma alteração estrutural de rotas, motores de sinais ou agentes de risco pode ser feita sem planejamento prévio com tarefas de 2 a 5 minutos (`writing_plans`).
2. **TDD Estrito (Red-Green-Refactor)**:
   - Qualquer ajuste em lógica de stop loss, trailing, cálculo de PnL, margem ou dimensionamento de lote **DEVE** ter um teste automatizado escrito antes em `tests/` ou `backend/tests/`.
   - Se o teste falhar, resolve-se o código mínimo necessário (GREEN) e refatora-se mantendo os testes verdes.
3. **Invariantes Invioláveis de Trading (V205 - Regras de Ouro Escritas em Pedra)**:
   - 🛡️ **Versão Canônica Vencedora V205**: Performance comprovada no Cockpit com expansão de $100.000,00 para $107.550,49 (+7.55% líquido), 0 drawdown e 0 ordens devolvidas.
   - 🛡️ **Margem Cruzada Soberana (Cross Margin 50X - Banca $10k)**: Toda operação opera em Margem Cruzada ($10.000,00 de colateral garantidor). Margem fixa de $1.000 por lote (exposição $50.000). Proibido calcular risco de liquidação isolada. Stops técnicos no 2H/4H ou SMA 21 com respiro livre de 12h a 24h.
   - 🛡️ **Regra de Expansão em Bola de Neve (2 + 2 + 2 + 2)**: Máximo de 2 ordens simultâneas em risco ativo (20% da banca; 80% ou $8.000 livres em colateral). Slots 3 a 8 só abrem conforme ordens anteriores atinjam Breakeven Soberano (+60% ROI / Trava +30% ROI). No ápice de 8 ordens, exatamente 6 ordens estão em risco zero e 2 em risco vivo.
   - 🛡️ **Breakeven Soberano (+60.0% ROI / Trava +30.0%)**: Disparo apenas com +60.0% de ROI (+1.2% de preço a favor), travando pelo menos +30.0% de ROI líquido (+ $300 no bolso), nunca fechando ordens por ruído de $21.
   - 🛡️ **Alvo Chão +300% de ROI (+$3,000.00)**: Alvo mínimo de realização por trade é +300% de ROI (provado por XPL com +365.91% / +$3.659,14), travando +200% de ROI (+ $2.000 fixos) no Degrau 5 e deixando o trailing correr no 4H.
   - 🛡️ **Stops Só Sobem ("Never Give Back")**: O stop loss de uma posição NUNCA pode ser afastado para trás. Stops progressivos em 5 escadinhas.
   - 🛡️ **Veto Soberano Farol BTC 2H (Tolerância Zero)**: Quando o Bitcoin não estiver estritamente em regime BULL (SMA 8 > SMA 21 e viés comprador positivo), compras de qualquer altcoin são sumariamente vetadas sem exceções de estratégia.
   - 🛡️ **Anti-Hedge Rígido**: É terminantemente proibido abrir simultaneamente posições opostas (LONG e SHORT) no mesmo par.
   - 🛡️ **Zero Mock Data em REAL**: Em modo `OKX_EXECUTION_MODE=REAL`, todas as ordens e saldos derivam da API OKX. Em `PAPER`, o Cockpit espelha a Banca Simulada Realizada do Sandbox.
4. **Evidência Obrigatória (Verification Before Completion)**:
   - Nenhuma tarefa é declarada concluída sem que o agente execute os testes no terminal (`pytest`, `scripts/run_regression_tests.py` ou chamadas HTTP nos endpoints `/api/health`, `/api/slots`, `/api/sandbox/unified-state`).
5. **Depuração Sistemática em 4 Fases**:
   - Proibido aplicar "remendos ad-hoc" em erros de WebSocket OKX (como 429), race conditions em locks assíncronos ou falhas de PnL. Deve-se reproduzir, rastrear a causa raiz causal, corrigir na origem com defesa em profundidade e validar regressão.
