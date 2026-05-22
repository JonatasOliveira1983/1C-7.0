import asyncio
import logging
from typing import Dict, Any, Optional, Set

logger = logging.getLogger("AIOS_ToolManager")

class AIOSToolManager:
    """
    Manages access to sensitive tools and APIs (e.g., Bybit Client).
    Prevents multiple agents from performing conflicting operations
    on the same resources using async locks.
    """
    
    def __init__(self):
        self.locks: Dict[str, asyncio.Lock] = {}
        self.registered_tools: Set[str] = set()

    def register_tool(self, tool_name: str):
        """Registers a tool name that requires locking."""
        if tool_name not in self.locks:
            self.locks[tool_name] = asyncio.Lock()
            self.registered_tools.add(tool_name)
            logger.info(f"🛠️ [TOOL] Registered restricted tool: {tool_name}")

    async def acquire(self, tool_name: str, agent_id: str):
        """Acquires a lock for a specific tool."""
        if tool_name not in self.locks:
            self.register_tool(tool_name)
        
        logger.debug(f"🔒 [TOOL] Agent {agent_id} requesting lock for {tool_name}")
        await self.locks[tool_name].acquire()
        logger.debug(f"✅ [TOOL] Agent {agent_id} ACQUIRED lock for {tool_name}")

    def release(self, tool_name: str, agent_id: str):
        """Releases a lock for a specific tool."""
        if tool_name in self.locks and self.locks[tool_name].locked():
            self.locks[tool_name].release()
            logger.debug(f"🔓 [TOOL] Agent {agent_id} RELEASED lock for {tool_name}")

    def is_locked(self, tool_name: str) -> bool:
        return self.locks.get(tool_name, None).locked() if tool_name in self.locks else False

# Singleton instance
tool_manager = AIOSToolManager()
