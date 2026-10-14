# 06 - PLANO DE IMPLEMENTACAO & CRITERIOS DE ACEITE - 1CRYPTEN MOBILE

> **Regra de Ouro**: A implementacao segue fases lineares e estritas com testes intermediarios obrigatorios. Nao se avanca para a proxima fase enquanto a atual nao estiver com 100% de aceite formalizado.

---

## 1. Cronograma de Fases e Portões de Qualidade (Quality Gates)

```
[ Fase 1: Rota /mobile & Shell Base ] ---> [ Quality Gate 1: Shell Mobile & 5 Abas Operacionais ]
               | (Aprovado)
               v
[ Fase 2: Hermes Chat (Home Page) ]  ---> [ Quality Gate 2: Dialogo RAG/MCP com Historico SQLite ]
               | (Aprovado)
               v
[ Fase 3: Cockpit Resumo & Custodia ]---> [ Quality Gate 3: Metricas da Banca & Modal de Ordem ]
               | (Aprovado)
               v
[ Fase 4: Grafico Solo OKX (15X) ]   ---> [ Quality Gate 4: Canvas Solo com Linhas Alvo/Stop ]
               | (Aprovado)
               v
[ Fase 5: Radar Flash & MCP Tools ]  ---> [ Quality Gate 5: Scanner OKX & Ferramentas Ativas ]
               | (Aprovado)
               v
[ Fase 6: Homologacao & Validacao ]  ---> [ Quality Gate 6: Auditoria Visual E2E a 415x942 px ]
```

---

## 2. Detalhamento das Fases de Construcao

### Fase 1: Rota `/mobile` e Shell Base de Navegacao
- **Escopo**:
  - Registro da rota `GET /mobile` no `main.py` apontando para `backend/app/static/mobile_app.html`.
  - Estrutura base HTML5 com viewport mobile, Safe-Area para iOS, CSS Binance Dark e icones SVG vetoriais.
  - Sticky Top Header com Saldo da Banca e status da conexao OKX.
  - Bottom Tab Bar fixa com as 5 abas (`[HERMES]`, `[COCKPIT]`, `[GRAFICO]`, `[CUSTODIA]`, `[RADAR]`) e alternancia instantanea no DOM.
- **Criterio de Aceite (Quality Gate 1)**:
  - `GET /mobile` responde com status 200.
  - A aplicacao renderiza sem barra de rolagem horizontal indesejada em 415px de largura.
  - O toque em cada uma das 5 abas alterna o container de visualizacao correspondente sem recarregar a pagina.

---

### Fase 2: Hermes Chat (Home Page do Mobile)
- **Escopo**:
  - Implementacao do feed conversacional do Hermes na Aba 1 (Home).
  - Conexao com `/api/v1/hermes/chat` e historico via `/api/v1/hermes/history`.
  - Integracao de *quick prompt pills* (`[Resumo da Banca]`, `[Status da Laya]`, `[Auditoria de Risco]`).
  - Renderizacao de cards de acao dentro das respostas do Hermes.
- **Criterio de Aceite (Quality Gate 2)**:
  - Envio de mensagem pelo celular exibe resposta em menos de 1.5s.
  - Perguntas sobre a banca ou Laya retornam dados reais auditados do banco.
  - Historico de conversa permanece disponivel ao reabrir o app.

---

### Fase 3: Cockpit Resumo & Aba de Custodia de Ordens
- **Escopo**:
  - Endpoint de agregacao `/api/v1/mobile/overview` retornando equity, PnL e status dos 4 slots.
  - Cards de metricas na Aba 2 (Cockpit).
  - Cards detalhados das ordens abertas na Aba 4 (Custodia).
  - Modal de confirmacao em 2 passos para encerramento manual de ordens.
- **Criterio de Aceite (Quality Gate 3)**:
  - Preco atual e PnL dos 4 slots atualizados em sincronia com o banco local.
  - Clique em encerrar ordem abre modal de confirmacao e nao executa nada sem o segundo clique explícito.

---

### Fase 4: Grafico Solo Responsivo com Seletor de Slots
- **Escopo**:
  - Integracao do TradingView Lightweight Charts adaptado para tela vertical de celular (380px a 450px de altura).
  - Seletor de slots no topo `[Slot 1] [Slot 2] [Slot 3] [Slot 4]`.
  - Renderizacao nativa das 3 linhas de operacao: Entrada (Azul), Alvo +5.0% (Verde/Dourado) e Stop -2.5% (Vermelho).
  - Carregamento de candles de 15m da OKX via API.
- **Criterio de Aceite (Quality Gate 4)**:
  - O grafico ocupa 100% da largura da tela sem scroll horizontal.
  - A troca de slot via seletor atualiza os candles e posiciona as 3 linhas em menos de 400ms.

---

### Fase 5: Radar Flash e Acoplamento de Ferramentas MCP
- **Escopo**:
  - Aba 5 (Radar) listando as altcoins monitoradas da OKX, volume 24h e taxas de financiamento (*funding rate*).
  - Conexao das ferramentas do MCP Bridge ao orquestrador Hermes para que ele execute comandos de auditoria e intervencao quando solicitado no chat.
- **Criterio de Aceite (Quality Gate 5)**:
  - Radar exibe dados reais de mercado da OKX.
  - Hermes aciona ferramentas MCP e reporta resultado no chat.

---

### Fase 6: Homologacao Visual e Testes E2E Mobile
- **Escopo**:
  - Validacao visual no emulador DevTools (415x942 px) com captura de telas de cada uma das 5 abas.
  - Auditoria de conformidade: verificacao de zero emojis em todo o codigo e dados.
  - Teste de reconexao de rede.
- **Criterio de Aceite Final**:
  - Todas as 5 abas validadas visualmente e funcionais.
  - Sistema pronto para operacao mobile de bolso.
