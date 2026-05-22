import os
import json
import logging
from pathlib import Path
from typing import Any, Optional, Dict

logger = logging.getLogger("AIOSAdapter")

class AIOSAdapter:
    """
    Bridge between 1CRYPTEN (Python) and Synkra AIOS (.aios/ storage).
    Provides persistent local storage for fleet intelligence and system state.
    """
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.aios_dir = self.project_root / ".aios"
        self.memory_dir = self.aios_dir / "fleet-intelligence"
        
        # Ensure directories exist
        self.aios_dir.mkdir(exist_ok=True)
        self.memory_dir.mkdir(exist_ok=True)
        
        # Files mapping
        self.state_file = self.aios_dir / "fleet_state.json"
        self.ticker_file = self.memory_dir / "tickers.json"

    def save_state(self, key: str, value: Any):
        """Persists a key-value pair in the AIOS state file."""
        try:
            state = self._load_json(self.state_file)
            state[key] = value
            self._save_json(self.state_file, state)
        except Exception as e:
            logger.error(f"AIOS Save State Error: {e}")

    def get_state(self, key: str, default: Any = None) -> Any:
        try:
            state = self._load_json(self.state_file)
            return state.get(key, default)
        except Exception:
            return default

    def save_memory(self, category: str, data: Dict[str, Any]):
        """Saves intelligence data (Whale, Sentiment, Macro) to specialized files."""
        try:
            file_path = self.memory_dir / f"{category}.json"
            current_data = self._load_json(file_path)
            current_data.update(data)
            self._save_json(file_path, current_data)
        except Exception as e:
            logger.error(f"AIOS Save Memory Error: {e}")

    def load_memory(self, category: str) -> Dict[str, Any]:
        file_path = self.memory_dir / f"{category}.json"
        return self._load_json(file_path)

    def _load_json(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_json(self, path: Path, data: Dict[str, Any]):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"AIOS JSON Save Error: {e}")

# Usage:
# adapter = AIOSAdapter("c:\\Users\\spcom\\Desktop\\10D-Bybit1.0")
# adapter.save_state("last_macro_risk", 7.5)
