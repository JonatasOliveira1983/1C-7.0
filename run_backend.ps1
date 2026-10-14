# ============================================================================
#  1CRYPTEN 7.0 — INICIALIZADOR DO BACKEND (PowerShell)
# ============================================================================
$ErrorActionPreference = "Stop"
$Base = $PSScriptRoot

Set-Location "$Base\backend"

Write-Host "[*] Subindo 1Crypten FastAPI Engine (:8085)..." -ForegroundColor Cyan
python -m uvicorn main:app --host 0.0.0.0 --port 8085 --workers 1
