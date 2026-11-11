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
3. **Invariantes Rígidas e Vencedoras de Risco e Trading (V212 - ESCRITAS EM PEDRA)**:
   - **Versão Canônica Vencedora V212 (Dual Breakeven 35/60 & Gap Elástico 50%)**:
     - *Degrau 1 (Breakeven Protetivo Taxas OKX)*: Dispara em **+35.0% de ROI** (+0.70% de preço a favor), travando o stop em **+7.0% de ROI** (+0.14% de preço a favor), cobrindo integralmente taxas da OKX e slippage (Zero a Zero Real) e impedindo que trades positivos sofram reversão para stop loss cheio (-100%).
     - *Degrau 2 (Breakeven Soberano Consolidado)*: Dispara em **+60.0% de ROI** (+1.20% de preço a favor), travando o stop em **+30.0% de ROI** líquido (+$300 fixos no cofre) e liberando novos slots de expansão na frota.
   - **Estratégia Soberana Swing 2H & Pullback Hunter 30M (`LAYA_PULLBACK_HUNTER_2H_30M`)**: Subordinação hierárquica estrita. O filtro direcional macro opera na tendência de 2H (SMA 8 x SMA 21). O gatilho de entrada confluencia o candle de confirmação no 30M. O Stop Loss é técnico e estrutural ancorado estritamente no 2H (topo/fundo estrutural ou além da SMA 21 de 2H).
   - **Trailing Dinâmico com Gap Elástico de 50% de ROI (1.0% de Preço a 50X)**: Ativado a partir de +100% de ROI (`trail_stop_roi = max(50.0, max_roi - 50.0)`), garantindo 1.0% de respiro livre para o ativo buscar o Alvo Chão de +300% de ROI sem estrangulamento precoce. Acima de +300% de ROI, trava no mínimo +200% de ROI fixos ($2.000 garantidos) e mantém 70% de folga até 500% no 4H.
   - **Extirpação Total de Micro-Defesas Legadas de Scalping**: As antigas travas de scalping (`lock_in_active` a 5% e `equity_defense` L1-L3 a 3%) foram permanentemente desativadas do motor unificado, impedindo qualquer sufocamento de posições por ruído de 0.06% a 0.10% de preço.
   - **Tríade Soberana de Cognição e Memória**: **Laya** (Inteligência Tática, Radar Universal de 507 pares e Farol BTC), **Hermes** (Orquestrador Soberano e Auditoria Executiva) e **OpenViking** (`viking://` Context Engine L0/L1/L2 com síntese auto-evolutiva de casos no Obsidian Vault e MCP 2.x Bridge com 16 ferramentas).
   - **Linha Visual de Risco Zero no Gráfico (+35% ROI)**: Exibição nativa em todos os gráficos da linha tracejada em Azul Ciano Neon (`#00F0FF`) marcando a cotação exata (+0.70% de deslocamento em 50X) onde o Breakeven Protetivo de Taxas é acionado.
   - **Painel de Custódia Geral com Intenção Tática Exclusiva da Laya**: O cabeçalho da custódia exibe em linha única compacta a composição da frota (`[3/8]` `[3 RISCO ZERO]` `[0/2 RISCO]` `[2 VAGOS]` e `[FLATTEN ALL]`), integrado à sub-faixa tática `LAYA RADAR` indicando o status de expansão e as moedas no alvo. O Top Banner superior permanece 100% limpo com telemetria macro global.
   - **Margem Cruzada Soberana (Cross Margin 50X)**: Toda e qualquer operação do 1Crypten opera estritamente sob Margem Cruzada. A banca de $10.000,00 é o colateral garantidor soberano; é terminantemente proibido calcular limites de stop loss ou alegar risco de liquidação baseado em fórmulas de margem isolada (1.8%). Margem fixa de $1.000,00 por lote (exposição nocional de $50.000,00). Stops pertencem à estrutura técnica (topo/fundo no 2H/4H ou SMA 21) com respiro livre de 12h a 24h.
   - **Regra de Expansão em Bola de Neve (2 + 2 + 2 + 2)**:
     - *Risco Inicial*: Máximo de 2 ordens abertas simultâneas em risco não protegido ($2.000 de margem comprometida = 20% da banca; 80% ou $8.000 livres como colateral garantidor em 50X Cruzada).
     - *Expansão Autofinanciada*: A 3ª, 4ª, 5ª, 6ª, 7ª e 8ª ordem só podem ser abertas conforme ordens anteriores atinjam Breakeven Soberano (+60% ROI / +1.2% de preço a favor com lucro travado de +30% ROI / +$300 fixos).
     - *Ápice da Frota (8 Slots Cheios)*: Exatamente 6 ordens com Risco Zero (lucro travado) e no máximo 2 ordens em risco ativo.
   - **Breakeven Soberano (+60.0% ROI / Trava +30.0%)**: O Breakeven nunca dispara por ruído de mercado (eliminado disparo legado de +25%). Disparo calibrado em +60.0% de ROI (+1.2% de preço a favor), com trava obrigatória de pelo menos +25.0% a +35.0% de ROI líquido (+30.0% padrão / +$300 fixos no cofre), nunca fechando trades prematuramente.
   - **Alvo Chão +300% de ROI (+$3,000.00)**: O alvo mínimo de realização por trade é +300% de ROI (superado por XPL com +365.91% / +$3.659,14), garantindo pelo menos +200% de lucro travado no Degrau 5 (+$2.000.00 fixos), deixando o trailing correr solto até a exaustão da tendência no gráfico de 4H.
   - **Never Give Back**: Stops progressivos (5 escadinhas) só sobem, nunca recuam.
   - **Veto Soberano Farol BTC 2H (Tolerância Zero)**: Quando o Bitcoin não estiver estritamente em regime BULL (SMA 8 > SMA 21 e viés comprador positivo), compras de qualquer altcoin são sumariamente VETADAS (`VETO_FAROL_BTC`). Sem exceções para Liquidity Hunt ou reversões 15M. A frota opera exclusivamente em SHORT a favor da maré macro ou mantém capital em HOLD.
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
