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
3. **Invariantes Invioláveis de Trading (Regras de Ouro)**:
   - 🛡️ **Stops Só Sobem ("Never Give Back")**: O stop loss de uma posição NUNCA pode ser afastado para trás. Uma vez que atingiu breakeven (GARANTIA_4 em +4% ROI no Scalp ou +12% no Swing), o stop só avança.
   - 🛡️ **Anti-Hedge Rígido**: É terminantemente proibido abrir simultaneamente posições opostas (LONG e SHORT) no mesmo par.
   - 🛡️ **Zero Mock Data em REAL**: Em modo `OKX_EXECUTION_MODE=REAL`, todas as ordens e saldos derivam da API OKX. Em `PAPER`, o Cockpit espelha a Banca Simulada Realizada do Sandbox.
   - 🛡️ **Teto Rígido de Risco**: Margem por trade e limites de slots definidos em `backend/config.py` são soberanos.
4. **Evidência Obrigatória (Verification Before Completion)**:
   - Nenhuma tarefa é declarada concluída sem que o agente execute os testes no terminal (`pytest`, `scripts/run_regression_tests.py` ou chamadas HTTP nos endpoints `/api/health`, `/api/slots`, `/api/sandbox/unified-state`).
5. **Depuração Sistemática em 4 Fases**:
   - Proibido aplicar "remendos ad-hoc" em erros de WebSocket OKX (como 429), race conditions em locks assíncronos ou falhas de PnL. Deve-se reproduzir, rastrear a causa raiz causal, corrigir na origem com defesa em profundidade e validar regressão.
