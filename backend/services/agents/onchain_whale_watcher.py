import logging
import time
import httpx
from typing import Dict, Any, List
from services.agents.aios_adapter import AIOSAgent
from config import settings

logger = logging.getLogger("OnChainWhaleWatcher")

class OnChainWhaleWatcher(AIOSAgent):
    """
    [V56.0] On-Chain Intelligence: Monitors blockchain transactions to predict CEX moves.
    Focuses on Bybit Hot Wallets and large BTC on-chain flows.
    """
    def __init__(self):
        super().__init__(
            agent_id="agent-onchain-whale",
            role="onchain_whale_watcher",
            capabilities=["ethereum_monitoring", "bitcoin_monitoring", "exchange_inflow_analysis"]
        )
        # Bybit Hot Wallets (Ethereum/ERC20)
        self.bybit_eth_wallets = [
            "0xf89d7b9c864f589bbf53a82105107622b35eaa40",
            "0x1Db92e2EeBC8E0c075a02BeA49a2935BcD2dFCF4"
        ]
        self.last_check_ts = 0
        self.whale_alerts = [] # List of recent large transactions

    async def on_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        msg_type = message.get("type")
        
        if msg_type == "GET_WHALE_ALERTS":
            return {"status": "SUCCESS", "data": self.whale_alerts}
            
        if msg_type == "REFRESH_ONCHAIN_DATA":
            alerts = await self.refresh_alerts()
            return {"status": "SUCCESS", "data": alerts}
            
        return {"status": "ERROR", "message": f"Unknown message type: {msg_type}"}

    async def refresh_alerts(self) -> List[Dict[str, Any]]:
        """Polls multiple on-chain sources for whale activity."""
        try:
            eth_alerts = await self._get_etherscan_whale_transfers()
            btc_alerts = await self._get_mempool_whale_transfers()
            
            self.whale_alerts = eth_alerts + btc_alerts
            # Keep only the last 20 alerts
            self.whale_alerts = sorted(self.whale_alerts, key=lambda x: x['timestamp'], reverse=True)[:20]
            
            return self.whale_alerts
        except Exception as e:
            logger.error(f"Error refreshing on-chain alerts: {e}")
            return []

    async def _get_etherscan_whale_transfers(self) -> List[Dict[str, Any]]:
        """Monitors Bybit Hot Wallets via Etherscan API (Free Tier)."""
        alerts = []
        api_key = getattr(settings, "ETHERSCAN_API_KEY", "YourApiKeyToken") # Fallback to default for testing
        
        if api_key == "YourApiKeyToken":
            logger.warning("[V56.0] Etherscan API Key not configured. Using limited mode.")

        async with httpx.AsyncClient() as client:
            for wallet in self.bybit_eth_wallets:
                try:
                    # Monitor USDT (ERC20) Token Transfers to/from Bybit
                    url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={wallet}&startblock=0&endblock=99999999&sort=desc&apikey={api_key}"
                    response = await client.get(url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("status") == "1":
                            transactions = data.get("result", [])
                            for tx in transactions[:5]: # Check last 5 transactions
                                value = float(tx.get("value", 0)) / (10**int(tx.get("tokenDecimal", 18)))
                                symbol = tx.get("tokenSymbol", "UNKNOWN")
                                
                                # Alert threshold: $500,000+
                                if (symbol == "USDT" and value > 500000) or (symbol == "ETH" and value > 200):
                                    is_inflow = tx.get("to").lower() == wallet.lower()
                                    alerts.append({
                                        "source": "ETHERSCAN",
                                        "symbol": symbol,
                                        "value": value,
                                        "type": "INFLOW (Potential Dump)" if is_inflow else "OUTFLOW (Accumulation)",
                                        "timestamp": int(tx.get("timeStamp", time.time())),
                                        "hash": tx.get("hash")
                                    })
                except Exception as e:
                    logger.error(f"Etherscan error for {wallet}: {e}")
        return alerts

    async def _get_mempool_whale_transfers(self) -> List[Dict[str, Any]]:
        """Monitors BTC large transactions via Mempool.space (Public API)."""
        alerts = []
        try:
            async with httpx.AsyncClient() as client:
                # Mempool.space API for large transactions isn't direct, 
                # but we can check the latest block for 'heavy' txs or use their ticker
                url = "https://mempool.space/api/v1/fees/recommended" # Placeholder for health check
                # Note: In a real implementation, we'd use a websocket or a specific whale-focused endpoint
                # For now, let's mock a high-level check or use a known public Whale tracking endpoint
                pass
            return alerts
        except Exception:
            return []

# Instance
on_chain_whale_watcher = OnChainWhaleWatcher()
