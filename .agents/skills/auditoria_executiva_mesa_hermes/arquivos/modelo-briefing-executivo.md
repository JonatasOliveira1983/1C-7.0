# Modelo de Briefing Executivo Hermes (Template Parametrizado)

### Quando usar
Usar obrigatoriamente toda vez que o operador solicitar o status da mesa de trading ou auditoria de operações.

### Quando NÃO usar
Não usar para debugar código ou quando o operador fizer uma pergunta teórica ou conceitual que não envolva o estado real da banca e ordens.

---

```text
================================================================================
BRIEFING EXECUTIVO DA MESA — [DATA_HORA_UTC]
================================================================================

1. BANCA & PATRIMÔNIO SOBERANO
- Saldo Consolidado: $[NET_WORTH_USD] USD (Milestone Ativo: $[MILESTONE_ATUAL] / Teto: $[TETO_RISCO_8PCT])
- Saldo Realizado (Cofre): $[SALDO_REALIZADO_USD] USD
- PnL Flutuante (Custódia): [SINAL_PNL]$[PNL_FLUTUANTE_USD] USD ([SINAL_PNL][PNL_FLUTUANTE_PCT]%)
- Status da Banca: [STATUS_BANCA_SAUDAVEL_OU_ALERTA]

2. RADIOGRAFIA DA CUSTÓDIA VIVA ([QTD_SLOTS_ATIVOS]/8 SLOTS)
[LISTA_DE_SLOTS_ATIVOS:
- [SYMBOL] ([SIDE] [LEVERAGE]X): Entrada $[ENTRY_PRICE] | Atual $[CURRENT_PRICE] | Stop $[CURRENT_STOP] | PnL: [SINAL]$[SLOT_PNL_USD] ([SINAL][SLOT_PNL_PCT]%) | Defesa: [STATUS_DEFESA_TRAIL]
]
- Risco Total Alocado: [RISCO_TOTAL_PCT]% de 8.0% máximo permitido.
- Alerta de Drawdown: [NENHUM_SLOT_CRITICO_OU_ALERTA_PAR_X]

3. HISTÓRICO RECENTE & PROVA FORENSE (ÚLTIMOS [QTD_FECHADOS] TRADES)
[LISTA_DE_FECHAMENTOS:
- [SYMBOL] ([SIDE]): Fechamento em $[EXIT_PRICE] | Resultado: [SINAL]$[TRADE_PNL_USD] ([SINAL][TRADE_PNL_PCT]%) | Motivo: [MOTIVO_ENCERRAMENTO] | Quarentena: [STATUS_QUARENTENA_2H]
]
- Taxa de Acerto Recente: [WIN_RATE_RECENTE]% ([QTD_WINS] W / [QTD_LOSSES] L)

4. INFRAESTRUTURA & REFLEXO LAYA
- Latência WebSocket OKX: [PING_OKX_MS] ms ([STATUS_CIRCUIT_BREAKER])
- Fluxo de Mercado: [THROUGHPUT_TICKS_SEC] ticks/s contínuos
- Varredura Laya Soberana: [TEMPO_VARREDURA_SEC]s (507 pares) | Regime: [REGIME_ADX_LAYA]

5. VEREDITO DO ESTADO DA ARTE
[VEREDITO_FINAL: "MESA 100% ESTÁVEL E PROSPERANDO. ZERO INTERVENÇÃO NECESSÁRIA." OU AÇÃO CIRÚRGICA REQUERIDA]
================================================================================
```

---

### Exemplo Preenchido de Referência (Golden Sample)

```text
================================================================================
BRIEFING EXECUTIVO DA MESA — 2026-10-28 18:50:00 UTC
================================================================================

1. BANCA & PATRIMÔNIO SOBERANO
- Saldo Consolidado: $10,969.78 USD (Milestone Ativo: $10,000.00 / Teto: $800.00)
- Saldo Realizado (Cofre): $10,969.78 USD
- PnL Flutuante (Custódia): -$12.40 USD (-0.11%)
- Status da Banca: SAUDÁVEL E LUCRATIVA (+9.70% acumulado)

2. RADIOGRAFIA DA CUSTÓDIA VIVA (3/8 SLOTS)
- POL-USDT-SWAP (SHORT 15X): Entrada $0.8920 | Atual $0.8928 | Stop $0.9044 | PnL: -$0.90 (-0.90%) | Defesa: STOP ESTRUTURAL ATIVO
- SOL-USDT-SWAP (SHORT 15X): Entrada $182.34 | Atual $182.50 | Stop $184.81 | PnL: -$1.50 (-1.50%) | Defesa: STOP ESTRUTURAL ATIVO
- UNI-USDT-SWAP (SHORT 15X): Entrada $7.2130 | Atual $7.3180 | Stop $7.5110 | PnL: -$10.00 (-10.00%) | Defesa: STOP ESTRUTURAL ATIVO
- Risco Total Alocado: 3.0% de 8.0% máximo permitido ($300.00 em jogo).
- Alerta de Drawdown: NENHUM SLOT CRÍTICO (Todos distantes de -50%).

3. HISTÓRICO RECENTE & PROVA FORENSE (ÚLTIMOS 3 TRADES)
- ZK-USDT-SWAP (LONG 20X): Fechamento $0.1450 | Resultado: +$19.92 (+19.92%) | Motivo: TRAILING_STOP | Quarentena: DISPENSADA (LUCRO)
- APE-USDT-SWAP (SHORT 15X): Fechamento $1.1120 | Resultado: -$11.13 (-11.13%) | Motivo: STOP_LOSS | Quarentena: ATIVA (Restam 48 min)
- PYTH-USDT-SWAP (SHORT 15X): Fechamento $0.3840 | Resultado: -$9.04 (-9.04%) | Motivo: STOP_LOSS | Quarentena: ATIVA (Restam 1h 12 min)
- Taxa de Acerto Recente: 33.3% Win Rate com R/R positivo.

4. INFRAESTRUTURA & REFLEXO LAYA
- Latência WebSocket OKX: 24.2 ms (ANTI-SLIPPAGE OK)
- Fluxo de Mercado: 363 ticks/s contínuos
- Varredura Laya Soberana: 69.2s (507 pares) | Regime: MEAN_REVERSION (ADX 14.5)

5. VEREDITO DO ESTADO DA ARTE
MESA 100% ESTÁVEL E PROSPERANDO. ZERO INTERVENÇÃO NECESSÁRIA.
================================================================================
```
