---
name: test_driven_development
description: Executa o ciclo rigoroso de Red-Green-Refactor (TDD) para o 1Crypten, cobrindo rotas FastAPI, motores de stop loss, cálculo de PnL e simulação Sandbox antes de escrever código de produção.
---

# Test-Driven Development (TDD) — 1Crypten Trading Engine

Esta skill governa toda e qualquer alteração de código nos motores operacionais (`captain.py`, `flash_agent.py`, `sandbox_service.py`, `sandbox_swing_service.py`, `bankroll.py`, etc.).

## Filosofia
Em um sistema de alta frequência e alavancagem 50x, um bug de cálculo de ROI ou trailing stop pode causar liquidação ou drawdown severo da banca. O TDD garante que cada regra matemática e de risco seja provada por teste automatizado antes de entrar em execução.

---

## 1. O Ciclo Inegociável

1. 🔴 **RED**: Crie ou atualize o teste em `tests/` ou `backend/tests/`. Execute `pytest tests/test_seu_arquivo.py` e verifique a falha exata.
2. 🟢 **GREEN**: Escreva a menor quantidade de código possível para fazer o teste passar. Re-execute o teste e comprove `PASSED`.
3. 🔵 **REFACTOR**: Otimize o código, garanta tipagens e verifique que toda a suíte de testes adjacente continua verde.

---

## 2. Invariantes a Serem Testadas em Qualquer Mudança de Trading

- **Cálculo de ROI**: Sempre testar com preço real e alavancagem de 50x (`roi = ((current - entry)/entry) * leverage * (1 if side == 'LONG' else -1)`).
- **Stops Progressivos**: Testar se o stop loss sobe quando o preço sobe e se NUNCA recua quando o preço retrai.
- **Margem Dinâmica**: Testar se o PnL em dólares deriva de `(contract_meta or {}).get('margin', 200.0)` e nunca de valores fixos hardcoded.
- **Race Conditions**: Testar concorrência de abertura de slots com `asyncio.Lock()` para impedir abertura de mais de 5 slots simultâneos.
