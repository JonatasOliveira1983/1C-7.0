FROM docker.n8n.io/n8nio/n8n

# CACHEBUST: altere este valor para forçar um rebuild completo no Railway
ARG CACHEBUST=8
RUN echo "[BUILD] Cache bust: $CACHEBUST"

USER root

# Copia o proxy Node.js que remove headers de bloqueio de iframe
COPY proxy.js /usr/local/bin/proxy.js
RUN chmod +x /usr/local/bin/proxy.js

# ==============================================================
# CONFIGURAÇÃO: proxy Node.js + wrapper
#
# Railway tem "Custom Start Command = n8n" (não podemos mudar),
# então substituímos o binário n8n por um wrapper que:
#   1) Inicia proxy.js na porta 8080 (background)
#   2) Executa o n8n REAL na porta 5678
#
# O proxy.js faz proxy de 8080 → 5678, REMOVENDO os headers
# X-Frame-Options, Content-Security-Policy e X-Content-Security-Policy
# que bloqueiam iframe.
#
# Node.js já está disponível na imagem (n8n depende dele).
# Sem nginx, sem apk, sem dependências externas.
# ==============================================================

# Substitui o binário n8n por um wrapper que inicia o proxy antes
RUN mv /usr/local/bin/n8n /usr/local/bin/n8n.real && \
    printf '#!/bin/sh\n\
echo "[WRAPPER] Starting proxy on port 8080..."\n\
node /usr/local/bin/proxy.js &\n\
PROXY_PID=$!\n\
sleep 1\n\
echo "[WRAPPER] Proxy PID: $PROXY_PID. Executing n8n on port 5678..."\n\
exec /usr/local/bin/n8n.real "$@"\n' > /usr/local/bin/n8n && \
    chmod +x /usr/local/bin/n8n

# Limpa artefatos de tentativas anteriores (nginx, start.sh)
RUN rm -f /etc/nginx/conf.d/default.conf /start.sh 2>/dev/null; true

USER node

# Configurações n8n
ENV N8N_PORT=5678
ENV N8N_HOST=0.0.0.0
ENV WEBHOOK_URL=https://n8n-production-8e2d4.up.railway.app

# Porta que o Railway vai expor (proxy escuta aqui)
EXPOSE 8080
