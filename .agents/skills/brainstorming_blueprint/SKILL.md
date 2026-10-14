---
name: brainstorming_blueprint
description: Refina ideias brutas em especificações técnicas blindadas através de perguntas socráticas, integrando a documentação e blueprints de docs/blueprint/ antes de alterar qualquer código no 1Crypten.
---

# Brainstorming & Blueprint de Especificação — 1Crypten

Esta skill é ativada antes da criação de novas estratégias, novos endpoints, novos módulos visuais (Cockpit/Mobile) ou refatorações estruturais.

## Objetivo
Impedir adivinhações e suposições da IA, conduzindo uma entrevista socrática de baixo atrito para gerar especificações blindadas integradas ao ecossistema 1Crypten (`docs/blueprint/`).

---

## 1. Princípios Operacionais

1. **Perguntas Focadas**: Faça no máximo 1 ou 2 perguntas por turno, fornecendo opções com recomendação técnica explícita.
2. **Respeito aos Contratos e Invariantes**:
   - Timeframes e Alavancagem: 50x (padrão), VWAP Sniper em M1/M5, Swing Lab em 2H (120m).
   - Roteamento de Stops: 5 escadas de stop (`order_projection_service.py`).
   - Regime de Mercado: ADX < 25 (LATERAL), >= 25 (TENDENCIA).
   - Visual: Binance Dark & Gold, Lamborghini HUD, zero emojis no código de produção.
3. **Seções Claras e Digestíveis**: Entregue especificações modulares que possam ser lidas e validadas em menos de 2 minutos.
