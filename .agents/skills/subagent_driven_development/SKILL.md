---
name: subagent_driven_development
description: Orquestra a execução de tarefas complexas no 1Crypten através de subagentes independentes, com revisão obrigatória em dois estágios (Conformidade com a Especificação e Qualidade/Invariantes de Trading).
---

# Subagent-Driven Development — Execução Autônoma no 1Crypten

Esta skill gerencia a delegação de microtarefas do plano para subagentes, evitando que o agente principal sature sua janela de contexto com logs volumosos de trading.

## As Duas Fases de Revisão Obrigatória

### Estágio 1: Auditoria de Conformidade com o Plano
1. O subagente alterou estritamente os arquivos designados na tarefa?
2. O teste automatizado correspondente foi executado e passou?
3. Houve alguma tentativa de modificar arquivos de configuração global sem autorização?

### Estágio 2: Auditoria de Invariantes do 1Crypten
1. **Never Give Back**: A regra de que o stop loss só avança foi preservada?
2. **Anti-Hedge**: Há salvaguarda contra abertura LONG+SHORT no mesmo símbolo?
3. **Mapeamento PAPER/REAL**: A semântica de espelho do Cockpit em PAPER foi respeitada?
4. **Tratamento de Exceções Assíncronas**: Há try/except com logging adequado dentro de tasks assíncronas do asyncio (`captain`, `flash_agent`), garantindo que locks e tocaias sejam sempre limpos no `finally`?
