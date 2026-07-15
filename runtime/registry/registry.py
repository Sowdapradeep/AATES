import logging
from typing import Any
from brain.agent_base import AgentBase

logger = logging.getLogger("runtime_registry")

class RuntimeAgentRegistry:
    """Registry maintaining active AI components and agent lifecycles in the AATES operating platform."""
    
    def __init__(self) -> None:
        self._agents: dict[str, AgentBase] = {}

    def register(self, agent: AgentBase) -> None:
        """Registers a cognitive agent configuration and status details."""
        self._agents[agent.name] = agent
        logger.info(f"Registry: Registered agent '{agent.name}' (v{agent.version})")

    def get_agent(self, name: str) -> AgentBase | None:
        """Retrieves a registered agent instance by its identifier name."""
        return self._agents.get(name)

    def list_agents(self) -> list[dict[str, Any]]:
        """Returns details, lifecycles, and performance metrics parameters of all registered agents."""
        return [
            {
                "name": agent.name,
                "version": agent.version,
                "status": agent.status,
                "metrics": agent.metrics
            }
            for agent in self._agents.values()
        ]

agent_registry = RuntimeAgentRegistry()
