# DOCUMENTO DE REQUISITOS DO PRODUTO (PRD) - 1CRYPTEN MOBILE

> **Objetivo**: Definir com clareza a experiencia mobile de bolso do ecossistema 1CRYPTEN, estabelecendo o agente Hermes como orquestrador central na tela principal (Home), acompanhamento de banca, gestao das acoes da Laya, visualizacao solo de graficos e ferramentas de acao rapida.

---

## 1. Identificacao Basica
- **Nome do Produto**: 1CRYPTEN Mobile Cockpit & Hermes Assistant
- **Ideia em uma Frase**: Terminal mobile-first de alta performance para monitoramento de banca, gestao de ordens perpétuas da OKX SWAP 15X e comando conversacional direto com o orquestrador Hermes.
- **Publico e Usuarios-Alvo**: Jonatas (Operador Soberano e Gestor de Carteira). O operador necessita acompanhar o crescimento da banca, avaliar a saude das ordens executadas pela Laya e intervir operacionalmente atraves do smartphone sem depender do desktop ultrawide.

---

## 2. O Problema e a Situacao Atual
- **A Dor Real do Usuario**: 
  - A interface web atual do Cockpit foi desenhada para resolucoes ultrawide (2560x1080).
  - Em telas de smartphone (ex: 415x942 px), os cards, tabelas e 4 graficos simultaneos colapsam em uma coluna vertical infinita, tornando a navegacao pesada, lenta e inacessivel para operacao com uma mao.
  - Para saber o estado da banca ou o que a Laya esta fazendo, o operador precisa buscar informacoes espalhadas na tela em vez de obter respostas diretas e resumidas.
- **A Solucao Improvisada Atual**:
  - O usuario precisa inspecionar e rolar manualmente pelo celular o cockpit desktop pesado, correndo risco de toques acidentais ou perda de agilidade em momentos criticos de volatilidade da OKX.

---

## 3. Objetivo e Metricas de Sucesso
- **Resultado Esperado**:
  - Uma aplicacao web progressiva (PWA / Mobile Web) com carregamento instantaneo (< 1.5s no 4G/5G).
  - Hermes posicionado na tela inicial (Home) com status da banca visivel no topo, dialogo natural alimentado por RAG e ferramentas MCP.
  - 5 abas inferiores ergonômicas para navegacao com o polegar.
  - 1 grafico solo dedicado e responsivo, eliminando o peso de 4 graficos simultaneos no celular.
- **Metrica / Sinal Mensuravel**:
  - Latencia de resposta do Hermes em consultas taticas < 800ms.
  - Consumo de memoria mobile reduzido em mais de 70% comparado ao carregamento do desktop no smartphone.
  - Tempo de encerramento manual de uma posicao via mobile < 2 segundos.
  - 100% de integridade factual com a base de dados SQLite local e OKX API.

---

## 4. Funcionalidades Principais (Escopo da Versao 1)

1. **Funcionalidade 1: Home Conversacional Hermes & Barra de Banca Superior**
   - **Beneficio**: Ao abrir o app no celular, o operador ve imediatamente o saldo liquido da banca, o PnL do dia e conversa diretamente com Hermes sobre risco, objetivos e o trabalho da Laya.
   - **Recursos**: Feed de chat, chips de atalhos rapidos (*quick pills*), status de conexao WebSocket e input ergonomico com suporte a microfone/voz.
   - **Prioridade**: Critica.

2. **Funcionalidade 2: Aba Cockpit (Resumo Executivo Mobile)**
   - **Beneficio**: Visao geral compacta da banca, percentual de acerto (winrate), exposicao financeira e resumo do estado dos 4 slots operacionais.
   - **Prioridade**: Alta.

3. **Funcionalidade 3: Aba Grafico Solo Dedicado (OKX 15X)**
   - **Beneficio**: Visualizacao clara e de alto contraste de 1 unico par por vez com linhas de Preco de Entrada, Alvo (+5.0%) e Stop (-2.5%), alem de seletor horizontal rapido entre slots (`[Slot 1] [Slot 2] [Slot 3] [Slot 4]`).
   - **Prioridade**: Critica.

4. **Funcionalidade 4: Aba Custodia & Ordens (Manejo Operacional)**
   - **Beneficio**: Cards compactos de posicoes abertas com ROI em tempo real, informacoes de margem e botao de encerramento de ordem com modal de confirmacao anti-erro.
   - **Prioridade**: Alta.

5. **Funcionalidade 5: Aba Radar Flash & Oportunidades**
   - **Beneficio**: Lista de monitoramento das altcoins OKX Perpetual SWAP, taxas de financiamento (funding rate) e sinais de confluencia gerados pelo fluxo institucional.
   - **Prioridade**: Media.

6. **Funcionalidade 6: Integracao RAG & Ferramentas MCP no Hermes**
   - **Beneficio**: Hermes responde duvidas sobre o playbook de operacoes (RAG BM25) e executa acoes autorizadas (consulta de saldo e fechamento de ordens via FastMCP).
   - **Prioridade**: Alta.

---

## 5. FORA DA VERSAO 1 (O que NAO construir agora)
> **Aviso ao Agente de IA**: Os itens abaixo estao explicitamente fora do MVP Mobile para assegurar foco, velocidade e estabilidade.

- Treinamento ou ajuste de pesos de modelos neurais pelo celular (fica no terminal/desktop).
- Configuracao avancada de chaves de API ou edicao direta de codigos Python pelo smartphone.
- Exibicao simultanea de 4 graficos em tela dividida no mobile (no mobile sera estritamente 1 grafico por vez).
- Criacao de novos pares de robos customizados via interface mobile.

---

## 6. Historias de Usuario Canonicas

1. **Historia 1**: Como operador, eu quero abrir o app no celular e ver de imediato na Home o Hermes me informando a saude da banca e dos 4 slots, para que eu tenha compreensao total da situacao em segundos.
2. **Historia 2**: Como operador, eu quero perguntar ao Hermes no chat *"Hermes, como estao as ordens da Laya?"* e receber um resumo preciso das entradas e do PnL atual, para nao precisar garimpar informacoes.
3. **Historia 3**: Como operador, eu quero alternar para a aba Grafico Solo e trocar rapidamente entre os slots com um toque, para analisar os candles e as linhas de stop e alvo com precisao grafica.
4. **Historia 4**: Como operador, eu quero clicar em *"Encerrar Posicao"* na aba Custodia e ter confirmacao segura, para liquidar uma ordem em caso de evento de risco extremo.

---

## 7. Criterios de Aceite (Formato BDD)

1. **Criterio 1 - Carregamento da Home**:
   - **Dado** que o operador acessa `/mobile` em dispositivo movel,
   - **Quando** a pagina carrega,
   - **Entao** o cabecalho superior exibe o saldo liquido da OKX e o PnL do dia atualizados via WebSocket, e a aba principal ativa e a Home do Hermes com historico recente de conversa.

2. **Criterio 2 - Grafico Solo Responsivo**:
   - **Dado** que o operador esta na aba Grafico Solo,
   - **Quando** clica no botao `[Slot 2 - PEPE]`,
   - **Entao** o grafico renderiza imediatamente os candles daquele par com a linha de entrada, alvo e stop, redimensionando perfeitamente a largura da tela do aparelho.

3. **Criterio 3 - Confirmacao de Seguranca de Ordem**:
   - **Dado** que o operador decide fechar uma posicao na aba Custodia ou via chat com Hermes,
   - **Quando** o comando de encerramento e disparado,
   - **Entao** o sistema exibe modal de confirmacao detalhando o par, preco e PnL antes de efetivar a transacao na OKX via MCP.

---

## 8. Perguntas e Decisoes em Aberto
- Nenhuma duvida impeditiva de escopo em aberto. O modelo segue rigorosamente a arquitetura da Base Tecnologica e o direcionamento aprovado pelo operador.
