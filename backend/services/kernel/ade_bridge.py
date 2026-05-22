import os
import subprocess
import asyncio
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("AIOS_ADE_Bridge")

class AIOSADEBridge:
    """
    Bridge between the Trading Fleet and the AIOS-Core ADE.
    Allows agents to request codebase modifications, spec generation,
    and QA validation using the npx aios-core CLI.
    """
    
    def __init__(self, core_path: str = "./aios-core"):
        self.core_path = core_path

    async def run_command(self, cmd: List[str]) -> Dict[str, Any]:
        """Executes a command via npx aios-core."""
        full_cmd = ["npx", "aios-core"] + cmd
        try:
            logger.info(f"🛠️ [ADE] Executing: {' '.join(full_cmd)}")
            process = await asyncio.create_subprocess_exec(
                *full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode(),
                "stderr": stderr.decode()
            }
        except Exception as e:
            logger.error(f"❌ [ADE] Command execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def generate_spec(self, feature_description: str) -> Dict[str, Any]:
        """Triggers the ADE Spec Pipeline."""
        return await self.run_command(["pm", "*write-spec", feature_description])

    async def execute_task(self, story_id: str) -> Dict[str, Any]:
        """Triggers the ADE Execution Engine."""
        return await self.run_command(["dev", "*execute-subtask", story_id])

    async def run_qa(self, story_id: str) -> Dict[str, Any]:
        """Triggers the QA Review phase."""
        return await self.run_command(["qa", "*review-build", story_id])

# Singleton instance
ade_bridge = AIOSADEBridge()
