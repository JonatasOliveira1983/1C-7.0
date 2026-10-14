---
name: session_forensics
description: Inspeciona históricos de sessão, transcrições e logs do 1Crypten para diagnosticar alucinações de agentes de IA, loops de chamadas ou quebras de invariantes de trading.
---

# Session Forensics — Diagnóstico Forense de Sessões no 1Crypten

Esta skill audita o comportamento de agentes de IA (Antigravity, Hermes ou subagentes) quando uma sessão apresentar comportamento indesejado ou falha operacional.

## Procedimento
1. Inspecione o arquivo de transcrição (`transcript.jsonl`) em `<appDataDir>\brain\<conversation-id>\.system_generated\logs/`.
2. Identifique desvios críticos:
   - Quebra de regras de `MASTER_ARCHITECTURE.md`.
   - Modificações em múltiplos arquivos sem seguir um plano atômico.
   - Declaração de sucesso sem execução de testes.
3. Produza relatório com evidência linha a linha da falha e as ações corretivas imediatas.
