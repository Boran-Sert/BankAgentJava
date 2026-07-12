"""Provides core functionalities for the tool_registry module."""
import logging
from typing import Dict, List, Optional, Callable, Any
from langchain_core.tools import BaseTool
from app.core.contracts import ToolSchema, ServiceSpec, RiskLevel

logger = logging.getLogger(__name__)

class ToolRegistryLoader:
    """Defines the Toolregistryloader structure."""
    def __init__(self):
        """Executes the   init   operation."""
        self._tools: Dict[str, ToolSchema] = {}
        self._domain_index: Dict[str, List[ToolSchema]] = {}
        self._executors: Dict[str, Callable] = {}

    def load_langchain_tools(self, tools: List[BaseTool], domain: str = "BANKING", risk_levels: Dict[str, RiskLevel] = None):
        """
        Automatically parses LangChain native BaseTools into BankAgent ToolSchemas.
        """
        if risk_levels is None:
            risk_levels = {}
            
        schemas = []
        for tool in tools:
            tool_id = tool.name.upper()
            
            # Store the execution function
            self._executors[tool_id] = tool.invoke
            
            # Parse parameters via Pydantic schema
            specs = []
            if tool.args_schema:
                schema_dict = tool.args_schema.schema()
                for prop_name, prop_info in schema_dict.get("properties", {}).items():
                    if prop_name in ["user_id", "kwargs"]:
                        continue
                        
                    t = "String"
                    if prop_info.get("type") == "number": t = "Decimal"
                    elif prop_info.get("type") == "integer": t = "Integer"
                    elif prop_info.get("type") == "boolean": t = "Boolean"
                    
                    specs.append(ServiceSpec(
                        name=prop_name,
                        type=t,
                        description=prop_info.get("description", prop_name)
                    ))
            
            # Apply default risk levels if not explicitly provided
            risk = risk_levels.get(tool_id, RiskLevel.READ_ONLY if tool_id.startswith("GET_") else RiskLevel.MUTATING_CRITICAL)
            
            schemas.append(ToolSchema(
                tool_id=tool_id,
                domain=domain,
                risk_level=risk,
                specs=specs,
                example_utterances=[tool.description]
            ))
            
        self.load_tools(schemas)

    def load_tools(self, tools: List[ToolSchema]):
        """Executes the Load tools operation."""
        for tool in tools:
            self._tools[tool.tool_id] = tool
            if tool.domain not in self._domain_index:
                self._domain_index[tool.domain] = []
            self._domain_index[tool.domain].append(tool)
        logger.info(f"Loaded {len(tools)} tools across {len(self._domain_index)} domains.")

    def get_tool(self, tool_id: str) -> Optional[ToolSchema]:
        """Executes the Get tool operation."""
        return self._tools.get(tool_id)

    def get_all_tools(self) -> List[ToolSchema]:
        """Executes the Get all tools operation."""
        return list(self._tools.values())
        
    def execute(self, tool_id: str, **kwargs) -> Any:
        """Executes the mapped LangChain tool."""
        executor = self._executors.get(tool_id)
        if not executor:
            logger.warning(f"No execution function registered for intent: {tool_id}")
            return None
        try:
            return executor(kwargs)
        except Exception as e:
            logger.exception(f"Error executing action for {tool_id}", extra={"error": str(e)})
            return {"error": str(e)}

tool_registry = ToolRegistryLoader()
