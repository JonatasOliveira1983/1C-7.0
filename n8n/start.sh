#!/bin/sh

# Inicia o n8n em segundo plano (background)
n8n &

# Dá um tempinho pro n8n iniciar
sleep 3

# Inicia o Nginx em primeiro plano para segurar o processo rodando
nginx -g 'daemon off;'
