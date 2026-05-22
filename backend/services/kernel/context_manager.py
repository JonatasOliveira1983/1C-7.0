import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("AIOS_Context")

class AIOSContextManager:
    """
    Handles serialization and persistence of agent states.
    Ensures zero-cost restarts and context continuity.
    """
    
    def __init__(self, storage_dir: str = ".aios/context"):
        self.storage_dir = storage_dir
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

    def save_context(self, agent_id: str, state: Dict[str, Any]):
        """Persists the agent's current mental state to disk."""
        file_path = os.path.join(self.storage_dir, f"{agent_id}.json")
        try:
            with open(file_path, "w") as f:
                json.dump(state, f, indent=2)
            logger.debug(f"💾 [CONTEXT] Saved state for agent: {agent_id}")
        except Exception as e:
            logger.error(f"❌ [CONTEXT] Failed to save state for {agent_id}: {e}")

    def load_context(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Loads a persisted state for an agent."""
        file_path = os.path.join(self.storage_dir, f"{agent_id}.json")
        if not os.path.exists(file_path):
            return None
            
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ [CONTEXT] Failed to load state for {agent_id}: {e}")
            return None

    def clear_context(self, agent_id: str):
        """Removes the stored state for an agent."""
        file_path = os.path.join(self.storage_dir, f"{agent_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)

# Singleton instance
context_manager = AIOSContextManager()
