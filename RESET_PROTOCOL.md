# ☢️ PROTOCOLO DE RESET NUCLEAR (ESTADO ZERO)

Este documento define o procedimento para resetar completamente o sistema 10D Sniper Factory para fins de teste ou reinício de banca.

### 🚀 Comando Rápido
Execute o comando abaixo no terminal da raiz do projeto:

```powershell
python 1CRYPTEN_SPACE_V4.0/backend/nuclear_reset.py
```

### 🛠️ O que o Reset faz?
1. **Limpa Slots**: Todos os 4 slots voltam ao estado `LIVRE`.
2. **Reseta Banca**: O saldo total volta para **$100.00**.
3. **Apaga Histórico**: Deleta permanentemente o histórico de trades, Moonbags e registros de Gênese no Postgres.
4. **Limpa Paper Mode**: Zera as posições simuladas no arquivo `paper_storage.json`.
5. **Cancela Ordens**: Tenta cancelar todas as ordens abertas na exchange Bybit.

### ⚠️ Aviso Importante
Este procedimento é **irreversível**. Use-o apenas quando desejar iniciar um novo ciclo de treinamento ou validar correções na lógica de Stop/Emancipação.

---
*Documentação V1.0 - 10D REAL 5.0*
