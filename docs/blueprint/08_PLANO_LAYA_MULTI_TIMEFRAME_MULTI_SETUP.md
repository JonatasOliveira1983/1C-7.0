# 08 — PLANO DE ARQUITETURA & IMPLEMENTAÇÃO: LAYA MULTI-TIMEFRAME & MULTI-SETUP ENGINE

> **Status**: Pronto para Execução  
> **Versão**: 1.0  
> **Data**: 12/10/2026  
> **Módulo Central**: `backend/app/services/laya_router_service.py`  
> **Escopo**: Multi-Timeframe (H1, 15M, 5M) + 3 Setups Concorrentes (Smart Money Breakout, Momento Mola e DVWAP Reversion)

---

## 1. Diagnóstico do Problema Atual

Atualmente, o método `run_autonomous_scan` da Laya afunila todos os ativos exclusivamente no setup de **Saída de Acumulação H1** (`evaluate_h1_breakout`).
- Como o mercado passa 85% do tempo dentro da consolidação de 1H, a Laya emite `HOLD` contínuo para quase 100% dos ativos.
- O trader/sistema fica de braços cruzados enquanto o preço oscila no miolo.
- As estratégias de **DVWAP** (retorno à média ponderada por volume no 5M) e **Momento Mola** (compressão de volatilidade no 15M) ficam inativas e silenciadas.

---

## 2. A Nova Arquitetura Hierárquica Multi-Timeframe

```
[CAMADA 1: 1H (H1) - MAPA DO TERRENO & BREAKOUT DE TENDÊNCIA]
  ├── Preço rompeu suporte ou resistência de 1H com força e OI?
  │     ├── SIM ➔ PRIORIDADE 1: LAYA_SMART_MONEY_H1 (Score 90-95)
  │     │       • Stop Loss colado na borda de saída da consolidação
  │     │       • Alvo de tendência longa (+3.5% a +6.0%)
  │     │
  │     └── NÃO ➔ O preço está DENTRO da consolidação de 1H!
  │               (Avança para os setups táticos intradiários)
  │
[CAMADA 2: 15M (M15) - RADAR DE COMPRESSÃO & DISPARO ELÁSTICO]
  ├── Volatilidade comprimiu no 15M (BB Width < 1.6%) no extremo do canal?
  │     ├── SIM ➔ PRIORIDADE 2: LAYA_MOMENTO_MOLA (Score 86-90)
  │     │       • Rejeição de extremo com volume secando
  │     │       • Stop no fundo/topo da mola, alvo no canal oposto
  │     │
  │     └── NÃO ➔ Avança para o radar de esticamento elástico
  │
[CAMADA 3: 5M/1M - RADAR DE DESVIO DA VWAP INTRA-RANGE]
  └── Preço esticou >= 1.2% longe da VWAP intradiária com LSR descompassado?
        ├── SIM ➔ PRIORIDADE 3: LAYA_DVWAP_REVERSION (Score 84-88)
        │       • Long se esticado abaixo da VWAP (desconto)
        │       • Short se esticado acima da VWAP (exaustão)
        │       • Alvo no centro da linha VWAP (retorno à média)
        │
        └── NÃO ➔ Telemetria completa no Thought Stream:
                  "Dentro da acumulação H1. DVWAP neutro. Mola relaxada. Aguardando."
```

---

## 3. Componentes Técnicos a Modificar

1. **`backend/app/services/laya_router_service.py`**:
   - `calculate_vwap_and_deviation`: Cálculo de VWAP em tempo real a partir dos candles intradiários.
   - `evaluate_dvwap_reversion`: Detector de desvio e reversão à média para operações intra-range.
   - `evaluate_momento_mola`: Detector de Squeeze / Compressão no 15M (Bollinger Width mínimo com rejeição).
   - `evaluate_multi_setup_opportunity`: Orquestrador hierárquico unificado que avalia as 3 camadas e seleciona o melhor setup por par.
   - Atualização em `run_autonomous_scan`: Chamar `evaluate_multi_setup_opportunity` e alimentar o Thought Stream com telemetria rica.
2. **`backend/services/order_projection_service.py`**:
   - Roteamento das novas classes de estratégia (`LAYA_DVWAP_REVERSION` e `LAYA_MOMENTO_MOLA`) para as escadinhas correspondentes com trailing stop.
3. **`tests/test_laya_multi_setup.py`**:
   - Testes unitários cobrindo os 3 setups e a invariante de hierarquia de prioridade.

---

## 4. Roteiro de Microetapas de Execução (TDD)

- [ ] **Etapa 1**: Criar suíte de testes `tests/test_laya_multi_setup.py` com casos de teste para Breakout H1, DVWAP 5M e Momento Mola 15M.
- [ ] **Etapa 2**: Implementar `calculate_vwap_and_deviation` e `evaluate_dvwap_reversion` em `laya_router_service.py`.
- [ ] **Etapa 3**: Implementar `evaluate_momento_mola` em `laya_router_service.py`.
- [ ] **Etapa 4**: Implementar o orquestrador `evaluate_multi_setup_opportunity` integrando a hierarquia.
- [ ] **Etapa 5**: Atualizar o loop `run_autonomous_scan` para disparar os setups e enriquecer o Thought Stream da UI.
- [ ] **Etapa 6**: Atualizar `order_projection_service.py` e validar via `pytest` (100% passed).
- [ ] **Etapa 7**: Validação empírica no terminal com o backend ativo.
