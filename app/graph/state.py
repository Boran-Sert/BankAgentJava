"""Provides core functionalities for the state module."""
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    Central state object for the LangGraph agent.
    This object is passed between nodes and persisted by the checkpointer.
    """
    # Conversation history automatically managed by LangGraph
    messages: Annotated[list[BaseMessage], add_messages]
    
    # Session and Identity context
    session_id: str
    user_id: str
    
    # Active task context
    active_intent: Optional[str]
    expected_specs: List[dict]
    collected_parameters: Dict[str, Any]
    grounded_parameters: Dict[str, Any]
    
    # Interruption and Stack management
    pending_tasks: List[Dict[str, Any]]
    
    # Confirmation Management for MUTATING_CRITICAL tools
    requires_confirmation: bool
    confirmation_status: str # IDLE, PENDING, APPROVED, REJECTED
