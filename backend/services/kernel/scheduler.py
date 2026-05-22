import asyncio
import logging
from enum import IntEnum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

logger = logging.getLogger("AIOS_Scheduler")

class Priority(IntEnum):
    URGENT = 0     # Shadow Sentinel (Execution/Risk)
    HIGH = 1       # Captain (Strategy)
    NORMAL = 2     # General Agents
    BACKGROUND = 3 # Chronicler/Logs

@dataclass(order=True)
class PriorityTask:
    priority: Priority
    payload: Dict[str, Any] = field(compare=False)
    future: asyncio.Future = field(default_factory=lambda: asyncio.Future(), compare=False)

class AIOSScheduler:
    """
    Manages agent request prioritization using an async PriorityQueue.
    Ensures critical trading actions (Sentinel) take precedence over 
    background tasks (Chronicler/Logs).
    """
    
    def __init__(self, max_concurrent: int = 5):
        self.queue = asyncio.PriorityQueue()
        self.max_concurrent = max_concurrent
        self._running_tasks = 0
        self._is_running = False

    async def schedule(self, payload: Dict[str, Any], priority: Priority = Priority.NORMAL) -> Any:
        """
        Adds a message to the queue and returns a future to be resolved when executed.
        """
        task = PriorityTask(priority=priority, payload=payload)
        await self.queue.put(task)
        logger.debug(f"📊 [SCHEDULER] Queued: {payload.get('type')} | Priority: {priority.name}")
        
        if not self._is_running:
            asyncio.create_task(self._process_loop())
            self._is_running = True
            
        return await task.future

    async def _process_loop(self):
        """Internal loop to process the priority queue."""
        while True:
            task: PriorityTask = await self.queue.get()
            
            # Wait for capacity if needed (basic rate limiting)
            while self._running_tasks >= self.max_concurrent:
                await asyncio.sleep(0.01)
            
            self._running_tasks += 1
            asyncio.create_task(self._execute_task(task))
            self.queue.task_done()

    async def _execute_task(self, task: PriorityTask):
        try:
            # We wrap the execution in a way that the Dispatcher can handle
            # The Dispatcher will actually do the call to the agent
            task.future.set_result(task.payload)
        except Exception as e:
            task.future.set_exception(e)
        finally:
            self._running_tasks -= 1

# Singleton instance
scheduler = AIOSScheduler()
