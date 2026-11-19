---
name: crypto_market_breadth
description: Protocolo de quantificacao de amplitude de mercado e regime macro para contratos perpetuos na OKX. Mede a porcentagem do universo acima da SMA 21 no 2H, pressao de fluxo comprador/vendedor, aquecimento de funding rates e contracao de volatilidade para governar as permissoes direcionais do Titan Radar e Farol BTC.
---

# Crypto Market Breadth — Protocolo de Amplitude e Regime Macro Cripto

## Proposito

Quantificar com rigor matematico a saude e a amplitude do mercado de derivativos da OKX antes de autorizar qualquer entrada individual em altcoins. Esse protocolo impede a armadilha classica de operar altcoins na contramao da mare macro institucional.

## Os 5 Componentes de Amplitude Institucional

| Componente | Peso | Metrica Calculada | Pergunta Respondida |
|---|---|---|---|
| 1. Altcoin Breadth (SMA 21 de 2H) | 30% | % dos 30 Titas com preco > SMA 21 de 2H | As altcoins estao acompanhando a tendencia ou apenas o BTC se move? |
| 2. Estrutura Macro do BTC (Farol BTC) | 25% | SMA 8 vs SMA 21 no 2H + ADX + Pearson | A maré mestra do mercado e compradora, vendedora ou lateral? |
| 3. Ratio Long/Short & Order Flow | 15% | % do universo com LSR < 1.00 (sem sardinhas na compra) | O varejo esta excessivamente comprado gerando risco de cascata? |
| 4. Regime de Funding Rate | 15% | Media ponderada de taxas de funding dos 20 maiores pares | O mercado de perpetuos esta sobreaquecido ou com desconto? |
| 5. Indice de Compressao (1C-EXP) | 15% | Media do 1C-EXP dos 30 Titas (Bandas de Bollinger e ATR) | Estamos em fase de acumulação estreita ou em expansao violenta? |

## Zonas de Regime e Postura Operacional do Titan Engine

### Zona 1: BEAR_DOMINANT (Score 0 a 35)
- **Diagnostico**: Menos de 30% dos ativos acima da SMA 21 no 2H. Bitcoin em regime de baixa ou testando suportes. Funding rates caindo ou negativos.
- **Diretriz Tática**:
  - Autorizacao plena para abertura de ordens em **SHORT** no Titan Engine (Grau 1 e Grau 2).
  - Veto absoluto e irrevogavel a compras (`VETO_FAROL_BTC` e `VETO_MACRO_TENDENCIA_BAIXA`).
  - Alvos expandidos para captura de Degraus 3 a 5 (+100% a +300% de ROI).

### Zona 2: CHOP_CONSOLIDATION (Score 36 a 65)
- **Diagnostico**: 35% a 65% dos ativos orbitando em torno da SMA 21 de 2H. Mercado lateral com baixa direcionalidade.
- **Diretriz Tática**:
  - Ativacao obrigatoria da tatica **Consolidation Ceiling Sniper** (`range_pos_2h >= 62%`).
  - Proibido vender no meio ou fundo do caixote (`VETO_MEIO_DE_ACUMULACAO_2H`).
  - Exigencia de sweep de liquidez na SMA 21 com pavio de rejeicao >= 25% (Grau 2).

### Zona 3: BULL_EXPANSION (Score 66 a 100)
- **Diagnostico**: Mais de 70% dos ativos acima da SMA 21 de 2H. Bitcoin com SMA 8 > SMA 21 em rompimento confirmado de resistencia institucional.
- **Diretriz Tática**:
  - Autorizacao para compras estruturadas de altcoins alinhadas no Slot 1 a 8.
  - Veto sumario a operacoes de venda contra a tendencia de alta acelerada.

## Como Executar a Analise no Sistema

A amplitude e calculada nativamente pelo `MarketIntelEngine` e exposta via endpoints de telemetria:

```bash
# 1. Consultar metricas consolidadas de amplitude
curl -s http://localhost:8085/api/v1/market/breadth | jq .

# 2. Consultar integracao com o Titan Radar
curl -s http://localhost:8085/api/cockpit/telemetry | jq .market_breadth
```
