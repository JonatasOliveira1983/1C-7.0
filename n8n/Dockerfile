FROM docker.n8n.io/n8nio/n8n

USER root

# Instala o Nginx
RUN apk add --no-cache nginx

# Cria diretórios necessários para o nginx e dá permissão pro usuário node (que não é root)
RUN mkdir -p /run/nginx /var/lib/nginx /var/log/nginx /tmp/client_temp /tmp/proxy_temp_path /tmp/fastcgi_temp /tmp/uwsgi_temp /tmp/scgi_temp && \
    chown -R node:node /run/nginx /var/lib/nginx /var/log/nginx /etc/nginx /tmp/client_temp /tmp/proxy_temp_path /tmp/fastcgi_temp /tmp/uwsgi_temp /tmp/scgi_temp

# Copia as configurações do Nginx e nosso script de inicialização
COPY nginx.conf /etc/nginx/nginx.conf
COPY start.sh /start.sh

# Dá permissão de execução pro script e transfere o dono pra segurança
RUN chmod +x /start.sh && chown node:node /start.sh

# Volta para o usuário padrão do N8N (segurança)
USER node

# Variáveis do N8N
ENV N8N_HOST=0.0.0.0
ENV WEBHOOK_URL=https://n8n-production-8e2d4.up.railway.app

# Informa ao Railway qual porta o Nginx estará escutando (8080)
EXPOSE 8080

# Inicia usando o nosso script que levanta N8N e Nginx juntos
CMD ["/start.sh"]
