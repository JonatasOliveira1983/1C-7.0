---
name: reverse_api_engineer
description: Engenharia reversa autônoma ou manual de websites e plataformas web para geração de clientes API tipados e estruturados em Python, captura de fluxos HAR e mapeamento de endpoints privados.
---

# REVERSE API ENGINEER — PROTOCOLO OPERACIONAL

Este protocolo orienta o agente na captura e dissecação de tráfego de rede (HAR) de plataformas web (como eassets.ai, agregadores de derivativos, exchanges e portais de inteligência cripto) para transformar dados web em clientes Python assíncronos (`httpx`) perfeitamente tipados e integrados ao ecossistema do 1Crypten.

---

## 🏛️ Localização da Ferramenta
- Repositório local: `C:\Users\jonat\Desktop\Sistemas 2026\1 - BASE Technológica\tools\reverse-api-engineer`
- Código-fonte: `src/reverse_api/`

---

## 🛠️ Modos de Operação

### 1. Modo Manual (`manual`)
Recomendado para sites com autenticação, Captcha ou dados restritos a login (ex: eAssets autenticado):
1. O navegador abre a URL alvo.
2. O operador navega, faz login e visualiza os dados/indicadores desejados.
3. Ao fechar a janela, a ferramenta salva o `.har` e o analisador extrai os endpoints e gera o `api_client.py`.

### 2. Modo Agente Autônomo (`agent`)
Recomendado para sites abertos com navegação automática orientada a objetivos:
- O agente utiliza Playwright / CDP para navegar, disparar os filtros e capturar os pacotes JSON.

### 3. Modo Coletor (`collector`)
Extração de dados tabulares diretamente em JSON ou CSV para alimentação de datasets.

---

## 📋 Regras de Integração no 1Crypten
1. **Desacoplamento Assíncrono**: Todo cliente gerado deve rodar de forma não-bloqueante (`async/await` com `httpx.AsyncClient`).
2. **Resiliência a Falhas (Circuit Breaker)**: Se a API externa rate-limitar ou falhar, o serviço deve ter fallback gracioso para não travar o loop de 1s da Laya/Scalping.
3. **Higienização de Chaves e Cookies**: Nenhuma credencial privada ou cookie de sessão deve ser commitado no repositório; use `.env` ou variáveis seguras.
