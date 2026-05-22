@echo off
echo [ELITE 30M SNIPER] Iniciando sistema...
set PYTHONUTF8=1
set "PYTHON_EXE=c:\Users\spcom\Desktop\10D-3.0 - Qwen\venv_elite\Scripts\python.exe"
set "BACKEND_DIR=c:\Users\spcom\Desktop\10D-3.0 - Qwen\1CRYPTEN_SPACE_V4.0\backend"

cd /d "%BACKEND_DIR%"
"%PYTHON_EXE%" main.py
pause
