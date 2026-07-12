"""Provides core functionalities for the base module."""
from abc import ABC, abstractmethod
from typing import Dict, Any
from app.core.contracts import BaseResponse
from app.core.state import SessionState

class BaseAgent(ABC):
    """Async Base Class for Worker Agents."""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    @abstractmethod
    async def process_message(self, message: str, state: SessionState) -> BaseResponse:
        """Process the user message and update state."""
        pass

    async def read_state(self, state: SessionState) -> Dict[str, Any]:
        """Helper to read agent-specific parameters from state."""
        return state.collected_parameters

    async def write_state(self, state: SessionState, new_parameters: Dict[str, Any], status: str):
        """Helper to write extracted parameters back to state."""
        state.collected_parameters.update(new_parameters)
        state.active_task_status = status
        if status == "IN_PROGRESS":
            state.active_agent_id = self.agent_id
        elif status in ["COMPLETED", "FAILED"]:
            state.active_agent_id = None

class BaseSupervisor(ABC):
    """Async Base Class for Supervisor Agents."""
    def __init__(self, supervisor_id: str):
        self.supervisor_id = supervisor_id

    @abstractmethod
    async def route(self, message: str, state: SessionState) -> BaseAgent:
        """Determine which Worker Agent should handle the message."""
        pass
