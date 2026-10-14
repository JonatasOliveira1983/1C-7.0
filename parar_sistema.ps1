# ============================================================================
#  1CRYPTEN 7.0 - FINALIZADOR DE PROCESSOS (PowerShell)
#  Libera com seguranca a porta 8085 e encerra processos zumbis.
# ============================================================================
$ErrorActionPreference = "SilentlyContinue"

Write-Host "==============================================================" -ForegroundColor Yellow
Write-Host "  1CRYPTEN 7.0 - PARANDO SERVICOS ATIVOS                      " -ForegroundColor Red
Write-Host "==============================================================" -ForegroundColor Yellow

$ports = @(8085)
foreach ($port in $ports) {
    $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conns) {
        foreach ($c in $conns) {
            $pidToKill = $c.OwningProcess
            if ($pidToKill -gt 0) {
                Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
                Write-Host "[-] Processo PID $pidToKill na porta $port finalizado." -ForegroundColor Green
            }
        }
    } else {
        Write-Host "[*] Porta $port ja esta liberada." -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "[OK] Todos os servicos foram finalizados com sucesso." -ForegroundColor Green
