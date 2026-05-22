# 🛠️ GSD — Get Shit Done (Prospect-On Edition)

Este protocolo define como as melhorias e novas funcionalidades devem ser implementadas para garantir a estabilidade do sistema, evitar o "Vibecoding" e **impedir a perda de memória (Context Rot)** através do uso da pasta `.gsd/`.

---

## 🔄 O FLUXO GSD

### 1. `/gsd-new` (Contexto & Alinhamento)
**Objetivo:** Carregar a memória do projeto e definir o "PORQUÊ" e o "O QUÊ".
- A IA **deve** obrigatoriamente ler todos os arquivos da pasta `.gsd/` (`PROJECT.md`, `REQUIREMENTS.md`, `STATE.md`, `ROADMAP.md`, `CONTEXT.md`) antes de sugerir qualquer coisa.
- Nenhuma linha de código é escrita aqui.
- Analisamos a documentação e mapeamos o impacto.

### 2. `/gsd-plan` (Planejamento Técnico)
**Objetivo:** Definir o "COMO".
- Criação de um `implementation_plan.md`.
- Listagem exata de arquivos a serem modificados.
- Definição de critérios de aceitação e testes.
- **Sinal Verde:** Só avançamos para o código após a sua aprovação explícita.

### 3. `/gsd-exec` (Execução Rigorosa)
**Objetivo:** Codificar com precisão.
- Seguimos o plano à risca.
- Pequenos commits.
- O `CONTEXT.md` deve ser atualizado se decisões táticas menores precisarem ser anotadas.

### 4. `/gsd-verify` (QA & Testes)
**Objetivo:** Validar o que foi construído.
- A IA revisa o código contra os critérios de aceitação.
- Testes práticos no Frontend/Backend para garantir a estabilidade.
- Correção de bugs.

### 5. `/gsd-ship` (Conclusão e Reset)
**Objetivo:** Finalizar e atualizar a memória global.
- Atualizamos o `STATE.md` com o que foi concluído.
- Zeramos ou consolidamos o `CONTEXT.md` para a próxima rodada.

---

## 📜 REGRAS DE OURO
- **Sem Spec, Sem Code:** Se não está no plano, não entra no código.
- **Bunker Mode:** Sempre proteja a integridade dos dados existentes e leia o `REQUIREMENTS.md`.
- **Zero Crash:** Use optional chaining e fallbacks em tudo no Frontend.

---

## 🧰 FERRAMENTAS INTEGRADAS
- **Memória:** Arquivos base na pasta `.gsd/`.
- **GSD Core:** Ferramentas em `tools/gsd/`.
- **Diagram Design:** Templates visuais em `tools/diagram-design/`.
