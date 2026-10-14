---
name: verification_before_completion
description: Portão de saída obrigatório que impede o agente de declarar qualquer alteração no 1Crypten como concluída sem antes apresentar evidência empírica no terminal e validação dos endpoints da API.
---

# Verification Before Completion — Evidência sobre Alegações no 1Crypten

Nenhum agente tem permissão para responder *"Pronto, o código foi corrigido"* sem antes apresentar as provas concretas de execução.

## Checklist Obrigatório do 1Crypten

Antes de encerrar o turno:
- [ ] **1. Testes Automatizados**: Rodar `pytest tests/test_flash_stop_invariants.py` ou a suíte afetada com saída `PASSED` comprovada.
- [ ] **2. Endpoints Críticos**: Se o servidor estiver ativo, verificar status de:
  - `GET /api/health` ➔ `status: "healthy"` ou `200 OK`
  - `GET /api/slots` ➔ Estrutura de slots íntegra
  - `GET /api/sandbox/unified-state` ➔ Banca consolidada e PnL coerente
- [ ] **3. Logs do Backend**: Garantir que `backend.log` não registrou `Traceback`, loops ou erros 500 decorrentes da mudança.
- [ ] **4. Sincronia de Arquitetura**: Se rotas, regras de stop ou parâmetros de configuração mudaram, atualizar `MASTER_ARCHITECTURE.md` e `README.md`.
