# ============================================================================
#  1CRYPTEN 7.0 - INICIALIZADOR OFICIAL (PowerShell)
#  Inicia o Backend FastAPI (:8085) e exibe os portais de acesso.
# ============================================================================
$ErrorActionPreference = "Continue"

$Base = $PSScriptRoot
$BackendDir = Join-Path $Base "backend"

Write-Host "==============================================================" -ForegroundColor Yellow
Write-Host "  1CRYPTEN 7.0 - ELITE TRADING SYSTEM & BASE TECNOLOGICA     " -ForegroundColor Green
Write-Host "  FastAPI :8085 + OKX SWAP + Hermes + Kronos + Sandbox Labs   " -ForegroundColor Cyan
Write-Host "==============================================================" -ForegroundColor Yellow
Write-Host ""

# 1. Checa porta 8085
$portInUse = Get-NetTCPConnection -LocalPort 8085 -State Listen -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "[!] Porta 8085 ja esta em uso por outro processo (PID $($portInUse[0].OwningProcess))." -ForegroundColor Yellow
    Write-Host "    Para reiniciar, execute '.\parar_sistema.ps1'." -ForegroundColor Gray
} else {
    Write-Host "[*] Iniciando Servidor 1Crypten na porta 8085..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$Base\run_backend.ps1`"" -WorkingDirectory $Base
}

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "==============================================================" -ForegroundColor Yellow
Write-Host "  PORTAIS DE ACESSO ATIVOS:" -ForegroundColor Green
Write-Host "  - Cockpit Lamborghini:         http://localhost:8085/" -ForegroundColor White
Write-Host "  - Sandbox Forward-Testing:     http://localhost:8085/sandbox" -ForegroundColor White
Write-Host "  - Terminal Hermes e Chat:      http://localhost:8085/hermes" -ForegroundColor White
Write-Host "  - Radar Tatico e Mercado:      http://localhost:8085/mercado" -ForegroundColor White
Write-Host "  - Documentacao OpenAPI:        http://localhost:8085/docs" -ForegroundColor White
Write-Host "==============================================================" -ForegroundColor Yellow
Write-Host "Para finalizar o sistema com seguranca, execute: .\parar_sistema.ps1" -ForegroundColor Gray
