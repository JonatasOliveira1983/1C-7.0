"""
[STUB] services.kernel.dispatcher — Reconstructed from .pyc cache
Provides the kernel object expected by main.py and other modules.
"""

import asyncio
import logging

logger = logging.getLogger("kernel.dispatcher")

class KernelDispatcher:
    """Minimal kernel dispatcher — stub reconstruction from original module."""

    def __init__(self):
        self._agents = {}
        self._dispatcher_mode = "direct"

    async def register_agent(self, agent):
        """Register an agent with the kernel."""
        name = getattr(agent, 'name', None) or getattr(agent, '__class__', None)
        if name is None:
            name = f"agent_{id(agent)}"
        elif hasattr(name, '__name__'):
            name = name.__name__
        
        agent_id = str(name).lower().replace(' ', '_')
        self._agents[agent_id] = agent
        logger.info(f"✅ Agent registered: {agent_id}")
        return agent

    async def unregister_agent(self, agent_id):
        """Unregister an agent."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.info(f"✅ Agent unregistered: {agent_id}")

    async def get_agent(self, agent_id):
        """Get a registered agent by ID."""
        return self._agents.get(agent_id)

    async def dispatch(self, event_type, payload=None):
        """Dispatch an event to all agents."""
        results = []
        for agent_id, agent in self._agents.items():
            try:
                if hasattr(agent, 'handle_event') and callable(agent.handle_event):
                    if asyncio.iscoroutinefunction(agent.handle_event):
                        result = await agent.handle_event(event_type, payload)
                    else:
                        result = agent.handle_event(event_type, payload)
                    results.append((agent_id, result))
            except Exception as e:
                logger.warning(f"⚠️ Agent {agent_id} dispatch error: {e}")
        return results

    @property
    def dispatcher(self):
        """Return self as dispatcher (backward compatibility)."""
        return self

    @property
    def agents(self):
        """Return all registered agents."""
        return dict(self._agents)

    def __len__(self):
        return len(self._agents)

    def __contains__(self, agent_id):
        return agent_id in self._agents

    def __iter__(self):
        return iter(self._agents.items())

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


# Singleton instance
kernel = KernelDispatcher()
