"""Provides core functionalities for the registry module."""
from typing import Dict, Optional, List
from app.agents.base import BaseAgent, BaseSupervisor

class DomainRegistry:
    """Dynamic loading registry for Domains (Supervisors) and Worker Agents."""
    def __init__(self):
        """Executes the   init   operation."""
        self.agents: Dict[str, BaseAgent] = {}
        self.supervisors: Dict[str, BaseSupervisor] = {}

    def register_agent(self, agent: BaseAgent):
        """Registers a worker agent to be used by supervisors or direct routing."""
        self.agents[agent.agent_id] = agent

    def register_supervisor(self, supervisor: BaseSupervisor):
        """Registers a domain supervisor."""
        self.supervisors[supervisor.supervisor_id] = supervisor

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Retrieves a specific agent by ID."""
        return self.agents.get(agent_id)

    def get_supervisor(self, supervisor_id: str) -> Optional[BaseSupervisor]:
        """Retrieves a specific supervisor by ID."""
        return self.supervisors.get(supervisor_id)
        
    def list_supervisors(self) -> List[BaseSupervisor]:
        """Lists all registered domain supervisors."""
        return list(self.supervisors.values())
