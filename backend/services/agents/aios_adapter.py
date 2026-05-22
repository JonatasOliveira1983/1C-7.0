import logging
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

logger = logging.getLogger("AIOSAdapter")

class AIOSAgent(ABC):
    """
    Standard Base for AIOS-compatible agents.
    Emulates the manifest-driven architecture of Synkra AIOS.
    """
    
    def __init__(self, agent_id: str, role: str, capabilities: List[str]):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.role = role
        self.capabilities = capabilities
        self.config: Dict[str, Any] = {}
        
    @abstractmethod
    async def on_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handles incoming messages from the Dispatcher (Kernel)."""
        pass

    async def handshake(self) -> Dict[str, Any]:
        """Initial registration data for the Kernel."""
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "capabilities": self.capabilities,
            "status": "READY"
        }

    def log(self, msg: str, level: int = logging.INFO):
        logger.log(level, f"[{self.role}] {msg}")

class AgentMessage:
    """Standardized message format for the Dispatcher."""
    @staticmethod
    def create(sender: str, receiver: str, payload_type: str, data: Dict[str, Any]):
        return {
            "msg_id": str(uuid.uuid4()),
            "sender": sender,
            "receiver": receiver,
            "type": payload_type,
            "data": data,
            "timestamp": uuid.uuid1().time
        }
