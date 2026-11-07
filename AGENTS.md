# AGENTS.md — PROTOCOLO OPERACIONAL PARA CODING AGENTS (1CRYPTEN)

> Este arquivo é lido automaticamente por agentes de IA (Antigravity, Claude Code, Cursor, Codex, Devin, Hermes, OpenCode) ao entrarem no repositório do 1Crypten.

---

## 🏛️ Diretrizes Inegociáveis do 1Crypten

1. **Fonte Única de Verdade Arquitetural**:
   - Toda a verdade técnica do sistema está em [`MASTER_ARCHITECTURE.md`](file:///c:/Users/jonat/Desktop/1C-SET26/MASTER_ARCHITECTURE.md).
   - O entry point único é `backend.main:app` (porta `8085`). Não existe `main.py` na raiz.
2. **Metodologia Superpowers Obrigatória**:
   - Todas as regras canônicas de engenharia estão formalizadas em [`.agents/rules/superpowers_methodology.md`](file:///c:/Users/jonat/Desktop/1C-SET26/.agents/rules/superpowers_methodology.md).
   - O ciclo **Red-Green-Refactor (TDD)** é obrigatório para qualquer mudança em motores de trading, stops ou PnL.
   - Nenhuma tarefa é finalizada sem evidência empírica no terminal ([`verification_before_completion`](file:///c:/Users/jonat/Desktop/1C-SET26/.agents/skills/verification_before_completion/SKILL.md)).
3. **Invariantes Rígidas de Risco e Trading**:
   - **Margem Cruzada Soberana (Cross Margin 50X)**: Toda e qualquer operação do 1Crypten opera estritamente sob Margem Cruzada. A banca inteira ($100.000) é o colateral garantidor; é terminantemente proibido calcular limites de stop loss ou alegar risco de liquidação baseado em fórmulas de margem isolada (1.8%). Stops pertencem à estrutura técnica (topo/fundo no 2H/4H ou SMA 21) com respiro livre de 12h a 24h.
   - **Regra dos Lotes 4 + 4**:
     - *Lote 1 (Em Risco)*: Máximo de 4 ordens abertas simultâneas em risco não protegido ($1.000 de margem fixa por ordem, alavancagem 50X Cruzada).
     - *Lote 2 (Expansão)*: A 5ª, 6ª, 7ª e 8ª ordem só podem ser abertas conforme ordens anteriores atinjam Breakeven (Risco Zero) ou Trailing Stop no Degrau 1 (+50% ROI / +1.0% de preço a favor). Limite absoluto da frota: 8 ordens.
   - **Alvo Chão +300% de ROI (+$3,000.00)**: O alvo mínimo de realização por trade é +300% de ROI, garantindo pelo menos +200% de lucro travado no Degrau 5 (+$2.000.00 fixos), deixando o trailing correr solto até a exaustão da tendência no gráfico de 4H.
   - **Never Give Back**: Stops progressivos (5 escadinhas) só sobem, nunca recuam.
   - **Veto Soberano Farol BTC 2H**: Quando o Bitcoin estiver em regime BEAR (SMA 8 < SMA 21 ou viés vendedor), compras de altcoin são expressamente vetadas (`VETO_FAROL_BTC`). Apenas vendas a favor do canal ou rompimento com robôs de alta extrema (`alt_pump_ignition`) são permitidos.
   - **Anti-Hedge**: Nunca abrir posições opostas simultâneas no mesmo par.
   - **Semântica PAPER vs REAL**: Em PAPER, o Cockpit espelha a Banca Simulada Realizada do Sandbox (`get_sandbox_unified_balance`); em REAL, a OKX recebe as ordens e o Cockpit reflete o saldo real.
4. **Padrão Visual Lamborghini / Binance Dark**:
   - **Zero Emojis**: Utilize ícones vetoriais SVG de precisão no código, na UI e nos dados.

---

## 🛠️ Skills Disponíveis em `.agents/skills/`

- **`brainstorming_blueprint`**: Refina requisitos socraticamente integrando com `docs/blueprint/`.
- **`writing_plans`**: Decompõe tarefas em microetapas de 2 a 5 minutos com comandos de teste exatos.
- **`subagent_driven_development`**: Despacha subagentes com revisão em dois estágios (Conformidade e Invariantes).
- **`test_driven_development`**: Ciclo TDD estrito para motores de trading e rotas FastAPI.
- **`systematic_debugging`**: Depuração forense em 4 fases para WebSocket, 429, deadlocks e cálculo de ROI.
- **`verification_before_completion`**: Validação empírica obrigatória antes de concluir qualquer turno.
- **`session_forensics`**: Auditoria pós-sessão de transcrições e logs de IA.
- **`update_architecture`**: Atualização do diagrama Mermaid em `MASTER_ARCHITECTURE.md`.
