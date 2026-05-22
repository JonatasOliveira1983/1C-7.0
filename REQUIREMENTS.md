# Requisitos do Sistema de Antecipação

## Integração Técnica
- **Graphify CLI:** Instalação global ou em venv para varredura do diretório `/backend`.
- **Obsidian Vault:** Pasta raiz `.obsidian_intel` na raiz do projeto (ignorada pelo git se necessário).
- **Python 3.10+:** Necessário para o Graphify processar as árvores de chamadas.

## Fluxo de Dados
1. **Scanning:** O Graphify varre o diretório e gera `graph.json`.
2. **Parsing:** Script para converter `graph.json` em arquivos `.md`.
3. **Linking:** Uso de Wikilinks `[[filename]]` para criar o grafo visual no Obsidian Graph View.

## Funcionalidades de Antecipação
- **Impact Analysis:** Comando para verificar quem será afetado por uma mudança no `bybit_ws.py`.
- **Strategic Mapping:** Notas no Obsidian que conectam códigos de agentes (ex: `librarian.py`) a conceitos de SMC (Smart Money Concepts).
- **Proactive Logs:** O sistema deve sugerir varreduras de grafos após mudanças críticas na arquitetura.
