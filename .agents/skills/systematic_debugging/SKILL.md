---
name: systematic_debugging
description: Protocolo forense em 4 fases para depuração de bugs críticos no motor de trading do 1Crypten (desconexão WebSocket OKX, 429 rate limit, ROI inflado, trailing stops travados e deadlocks assíncronos).
---

# Systematic Debugging — Protocolo Forense para 1Crypten

Esta skill deve ser acionada imediatamente quando um erro de execução, regressão estatística (drawdown anômalo, stops travados) ou exceção assíncrona for detectada.

## As 4 Fases Obrigatórias

### Fase 1: Reprodução Mínima e Isolamento
- Isole a falha em um teste em `tests/` ou script de reprodução pontual.
- Exemplo clássico: simular uma lista de ticks de preço e testar se a função `_evaluate_trade_stops` move o stop corretamente.
- Se a falha envolve WebSocket da OKX, inspecione a fila `OKXCommandQueue` e os logs de rate-limit.

### Fase 2: Rastreamento da Causa Raiz Causal
- Rastreie o caminho dos dados de trás para frente.
- Exemplo real: Se o ROI de um trade disparou para +4066%, rastreie de onde veio o preço de referência (descobriu-se que `_get_peak_price` lia wicks de 120s com dados desatualizados do cache).
- Nunca faça correções superficiais (ex: apenas colocar um cap sem remover a fonte do dado poluído).

### Fase 3: Correção Cirúrgica & Defesa em Profundidade
- Remova o defeito na fonte exata.
- Adicione sanity caps e asserções protetivas (ex: `min(roi, 300.0)` como defesa secundária caso a fonte falhe).
- Adicione limpeza em bloco `finally` para tasks assíncronas no Captain/FlashAgent.

### Fase 4: Verificação de Regressão
- Execute o teste que falhava para comprovar a solução.
- Execute a suíte de testes de invariantes: `pytest tests/test_flash_stop_invariants.py tests/test_sandbox.py`.
