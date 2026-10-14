---
name: writing_plans
description: Converte objetivos e refatorações do 1Crypten em planos de implementação atômicos, com microtarefas de 2 a 5 minutos, caminhos exatos de arquivo e comandos de verificação empírica.
---

# Writing Plans — Decomposição Atômica para 1Crypten

Esta skill é acionada após o término do `brainstorming_blueprint` para planejar alterações no motor de trading, rotas ou interface do Cockpit.

## Estrutura Obrigatória de Cada Tarefa

```markdown
### Tarefa X.Y: [Nome Claro da Ação]
- **Arquivos Afetados**:
  - `backend/services/sandbox_service.py` (Modificação)
  - `tests/test_sandbox.py` (Teste)
- **Objetivo**: O que exatamente esta micro-etapa constrói ou corrige.
- **Passos Concretos**:
  1. Escrever caso de teste para o novo gatilho de break-even.
  2. Implementar a condição na função `_evaluate_trade_stops`.
- **Ciclo TDD**:
  - Comando de falha (RED): `pytest tests/test_sandbox.py -k test_breakeven`
  - Comando de aprovação (GREEN): `pytest tests/test_sandbox.py -k test_breakeven -v`
- **Critério de Aceite**: Status 0, 100% de asserções passando.
```

---

## Regras
1. **Duração**: Tarefas devem ser executáveis em 2 a 5 minutos.
2. **Caminhos Exatos**: Declare o caminho completo (ex: `backend/services/agents/captain.py`).
3. **Verificação Sem Adivinhação**: Cada tarefa exige um comando de terminal para validação.
