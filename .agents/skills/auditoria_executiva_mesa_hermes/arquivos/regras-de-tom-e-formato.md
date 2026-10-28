# Regras de Tom, Estilo e Precisão — Auditoria Hermes

1. **Zero Emojis**:
   - É terminantemente proibido o uso de emojis no relatório ou nos logs. Utilize caixas altas, números exatos, sinais de porcentagem e barras limpas.

2. **Factualidade Cirúrgica**:
   - Nunca use palavras vagas como *"o mercado oscilou com volatilidade"* ou *"o trade foi bom"*.
   - Use dados auditados: preço de entrada, preço de saída, ID de contrato, PnL em dólares e milissegundos.

3. **Inviolabilidade do Veredito "Zero Intervenção"**:
   - O Hermes só pode afirmar que *"nenhuma intervenção é necessária"* se todas as 7 provas da seção `Pronto quando` do `SKILL.md` tiverem passado com 100% de sucesso.
   - Se uma única ordem estiver sem stop ou o ping estiver acima de 150ms, o veredito DEVE obrigatoriamente apontar a anomalia e a ação corretiva imediata.

4. **Vocabulário Proibido**:
   - Proibido usar adjetivos vazios: *"espetacular"*, *"incrível"*, *"promissor"*, *"arriscado mas normal"*.
   - Use termos técnicos canônicos: `Never Give Back`, `Quarentena 2h`, `Milestone Composto`, `Anti-Hedge`, `Circuit Breaker`.
