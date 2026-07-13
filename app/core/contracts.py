"""Provides core functionalities for the contracts module."""
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
from enum import Enum

class RiskLevel(str, Enum):
    """Defines the risk level of a tool to dictate confirmation requirements."""
    READ_ONLY = "READ_ONLY"
    MUTATING_LOW = "MUTATING_LOW"
    MUTATING_CRITICAL = "MUTATING_CRITICAL"

class ServiceSpec(BaseModel):
    """Metadata defining Java-side variable names and types."""
    name: str = Field(..., description="Name of the service parameter expected by Java")
    type: str = Field(..., description="Data type of the parameter (e.g., String, Integer, UUID)")
    description: Optional[str] = Field(None, description="Description of the parameter to help LLM extraction")

class ToolSchema(BaseModel):
    """
    [PHASE 2] Tool Registry Schema
    Represents a full banking tool (e.g., 'MakePayment', 'GetBalance') dynamically loaded from a registry.
    """
    tool_id: str = Field(..., description="Unique identifier for the tool")
    domain: str = Field(..., description="The Domain this tool belongs to (e.g., 'CARD_DOMAIN')")
    risk_level: RiskLevel = Field(default=RiskLevel.READ_ONLY, description="Risk level dictating confirmation rules")
    specs: List[ServiceSpec] = Field(default_factory=list, description="Parameters required by this tool")
    example_utterances: List[str] = Field(default_factory=list, description="Examples of what a user might say to trigger this tool")

class BaseResponse(BaseModel):
    """Fixed schema for Java responses."""
    agent: str = Field(..., description="The name or ID of the agent returning the response")
    intent: str = Field(..., description="The intent identified by the agent")
    status: str = Field(..., description="Task status: e.g., IN_PROGRESS, COMPLETED, FAILED")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Extracted parameters mapping to ServiceSpecs")
    message_to_user: str = Field(..., description="Message to be displayed to the end user")
    thinking: Optional[str] = Field(None, description="The internal reasoning or inner monologue of the AI")
