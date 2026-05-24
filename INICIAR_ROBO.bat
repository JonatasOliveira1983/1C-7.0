@echo off
title Sniper V110.100 - Alpha Revolution
cls
set PYTHONUTF8=1
echo ========================================================
echo   SNIPER INTELLIGENCE LAB - V110.100 ALPHA REVOLUTION
echo ========================================================
echo.
echo 1. Executando PROTOCOLO NUKE (Limpando processos antigos)...
python TERMINAR_TUDO.py
echo.
echo 2. Iniciando Servidor Central (V110.100)...
cd backend
python main.py
pause
