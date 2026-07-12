"""Provides core functionalities for the extractor module."""
from typing import Type
from pydantic import BaseModel, create_model, Field
from langchain_core.messages import AIMessage, HumanMessage
from app.graph.state import AgentState
from app.core.logger import logger
from app.core.llm_factory import llm_engine


def _create_dynamic_pydantic_model(expected_specs: list) -> Type[BaseModel]:
    """Dynamically creates a Pydantic model based on Java expected specs."""
    fields = {}
    for spec in expected_specs:
        # Simplification: Assume all missing fields are strings for LLM extraction
        fields[spec.get("name")] = (
            str,
            Field(..., description=spec.get("description")),
        )
    return create_model("DynamicExtractionSchema", **fields)


def extractor_node(state: AgentState) -> dict:
    """
    Uses LLM tool calling to extract missing parameters based on expected_specs.
    """
    logger.info(
        "node_execution", node="extractor_node", session_id=state.get("session_id")
    )

    active_intent = state.get("active_intent")
    if not active_intent:
        return {}

    expected_specs = state.get("expected_specs", [])
    collected_params = state.get("collected_parameters", {})

    # Find which specs are still missing
    missing_specs = [s for s in expected_specs if s.get("name") not in collected_params]

    if not missing_specs:
        logger.info("all_parameters_collected", intent=active_intent)
        return {}  # Move to grounding

    # Create dynamic schema
    schema = _create_dynamic_pydantic_model(missing_specs)

    # Bind tool to LLM
    llm_with_tools = llm_engine.bind_tools([schema])

    # Ask LLM to extract from conversation history
    messages = state.get("messages", [])
    system_prompt = AIMessage(
        content=f"You are a banking assistant. You must extract the following information from the user's messages. If there is missing information, ask the user: {[s.get('name') for s in missing_specs]} NEVER MAKE ASSUMPTIONS."
    )

    response = llm_with_tools.invoke([system_prompt] + messages)

    new_params = {}
    if response.tool_calls:
        logger.info("tool_calls_extracted", calls=len(response.tool_calls))
        for tc in response.tool_calls:
            # Add extracted args
            new_params.update(tc.get("args", {}))

    if new_params:
        # Merge with existing
        merged = {**collected_params, **new_params}
        
        # Check if there are STILL missing specs after this extraction
        still_missing = [s for s in expected_specs if s.get("name") not in merged]
        
        if still_missing:
            missing_names = [s.get("name") for s in still_missing]
            follow_up_msg = AIMessage(content=f"Lütfen şu bilgileri de giriniz: {', '.join(missing_names)}")
            logger.info("partial_extraction_asking_more", missing=missing_names)
            return {"collected_parameters": merged, "messages": [follow_up_msg]}
            
        return {"collected_parameters": merged}

    # If no tool calls and still missing, return the LLM's text response asking the user
    return {"messages": [response]}
