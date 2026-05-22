
import asyncio
import os
import sys

# Adiciona o caminho do projeto ao sys.path
sys.path.append(os.path.join(os.getcwd(), "1CRYPTEN_SPACE_V4.0", "backend"))

from services.vault_service import vault_service

async def check_vault():
    allowed, reason = await vault_service.is_trading_allowed()
    print(f"Trading Allowed: {allowed}")
    print(f"Reason: {reason}")
    
    # Check balance
    from services.bankroll import bankroll_manager
    balance = await bankroll_manager._get_operating_balance()
    print(f"Operating Balance: ${balance}")

if __name__ == "__main__":
    asyncio.run(check_vault())
