FROM docker.n8n.io/n8nio/n8n

# CACHEBUST: altere este valor para forçar um rebuild completo no Railway
ARG CACHEBUST=9
RUN echo "[BUILD] Cache bust: $CACHEBUST"

USER node

# Configurações n8n
ENV N8N_PORT=5678
ENV N8N_HOST=0.0.0.0
ENV WEBHOOK_URL=https://n8n-production-8e2d4.up.railway.app

EXPOSE 5678
