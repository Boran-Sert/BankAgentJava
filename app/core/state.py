"""Provides core functionalities for the state module."""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from enum import Enum
from app.core.contracts import ServiceSpec

class TaskStatus(str, Enum):
    """Defines the Taskstatus structure."""
    IDLE = "IDLE"
    IN_PROGRESS = "IN_PROGRESS"
    CONFIRMATION_PENDING = "CONFIRMATION_PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    INTERRUPTED = "INTERRUPTED"

class SessionState(BaseModel):
    """Session State Model object per user/session."""
    session_id: str = Field(..., description="Unique identifier for the user session")
    user_id: str = Field(..., description="Unique identifier for the customer/user")
    active_agent_id: Optional[str] = Field(None, description="The ID of the currently active agent if a task is in progress")
    active_task_status: TaskStatus = Field(TaskStatus.IDLE, description="Status of the current task")
    collected_parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters collected so far across the session")
    mapped_keys_history: Dict[str, str] = Field(default_factory=dict, description="History of Python to Java mapped keys for rejection recovery")
    last_intent: Optional[str] = Field(None, description="The last intent identified by the system")
    expected_specs: List[ServiceSpec] = Field(default_factory=list, description="Dynamic contract expectations received from Java backend")
    last_system_message: Optional[str] = Field(None, description="The last question or message the system asked the user")
    pending_tasks: List[Dict[str, Any]] = Field(default_factory=list, description="Stack of interrupted tasks to resume later")
