import os
import subprocess
import sys
import time

def nuke_zombies():
    print(">>> INICIANDO PROTOCOLO DE EXTERMINIO DE PROCESSOS ZUMBIS <<<")
    print("-" * 50)
    
    # Lista de processos para encerrar
    targets = ["python.exe", "uvicorn.exe"]
    
    for target in targets:
        print(f" tentando encerrar {target}...")
        try:
            # /F = Force, /T = Tree (child processes), /IM = Image Name
            # Redirecionamos stderr para devnull para evitar mensagens feias se o processo não existir
            subprocess.run(["taskkill", "/F", "/T", "/IM", target], capture_output=True)
            print(f" OK: Comando enviado para {target}")
        except Exception as e:
            print(f" ERRO ao tentar encerrar {target}: {e}")

    print("-" * 50)
    print("LIMPANDO CACHE E PORTAS...")
    
    # Tentativa extra de liberar a porta 8085 especificamente
    try:
        # Comando para encontrar PID na porta 8085 e matar
        cmd = 'for /f "tokens=5" %a in (\'netstat -aon ^| findstr :8085\') do taskkill /f /pid %a'
        subprocess.run(cmd, shell=True, capture_output=True)
        print(" OK: Tentativa de limpeza da porta 8085 concluida.")
    except:
        pass

    print("Processo concluido com sucesso.")
    print("-" * 50)
    print("\nAGORA VOCE PODE ABRIR O ROBO NOVO:")
    print("Use o arquivo INICIAR_ROBO.bat na pasta raiz.")
    print("-" * 50)

if __name__ == "__main__":
    nuke_zombies()
    time.sleep(2)
