"""Provides core functionalities for the extractor module."""

from typing import Type
from pydantic import BaseModel, create_model, Field
from langchain_core.messages import AIMessage, ChatMessage
from app.graph.state import AgentState
from app.core.logger import logger
from app.core.llm_factory import llm_engine
from langchain_core.messages import ToolMessage


def _create_dynamic_pydantic_model(expected_specs: list) -> Type[BaseModel]:
    """Dynamically creates a Pydantic model based on Java expected specs."""
    fields = {}
    for spec in expected_specs:
        name = spec.get("name", "")
        # Çoğul takısı (s) veya list kelimesi geçiyorsa Liste tipinde kabul et
        if name.endswith("s") or "list" in name.lower():
            field_type = list[str]
        else:
            field_type = str

        fields[name] = (
            field_type,
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

    # Bind tool to LLM alongside sanitized SAFE proxy tools only (Zero-DB Access for LLM)
    from app.agents.tools import get_user_account_options

    utility_tools = [get_user_account_options]

    # We create a dictionary to easily invoke utility tools by name
    utility_tools_map = {tool.name: tool for tool in utility_tools}

    llm_with_tools = llm_engine.bind_tools([schema] + utility_tools)

    messages_to_pass = list(state.get("messages", []))
    system_prompt_content = (
        "You are a professional banking assistant. Your goal is to extract the following missing information "
        f"from the user: {[s.get('name') for s in missing_specs]}.\n\n"
        "RULES:\n"
        "1. You can use the provided safe proxy tools (like get_user_account_options) to query user options and find the missing parameters.\n"
        "2. CRITICAL: If a tool returns multiple options (e.g., multiple accounts) and it is ambiguous which one the user wants, "
        "DO NOT guess. You must ask the user to clarify which one they mean.\n"
        "3. Only use the DynamicExtractionSchema tool when you are absolutely sure of the final values for all missing parameters."
    )

    system_prompt = AIMessage(content=system_prompt_content)

    # Start ReAct Loop
    max_iterations = 5
    current_iteration = 0

    while current_iteration < max_iterations:
        current_iteration += 1

        response = llm_with_tools.invoke(
            [system_prompt, ChatMessage(role="control", content="thinking")]
            + messages_to_pass
        )

        if not response.tool_calls:
            # LLM decided to ask the user a question or respond directly
            logger.info("extractor_asking_user", content=response.content)
            return {"messages": [response]}

        # Check what tools were called
        schema_calls = [
            tc for tc in response.tool_calls if tc["name"] == "DynamicExtractionSchema"
        ]
        utility_calls = [
            tc for tc in response.tool_calls if tc["name"] != "DynamicExtractionSchema"
        ]

        if schema_calls:
            # Parameters extracted!
            new_params = {}
            for tc in schema_calls:
                new_params.update(tc.get("args", {}))

            merged = {**collected_params, **new_params}

            # Check if there are STILL missing specs after this extraction
            still_missing = [s for s in expected_specs if s.get("name") not in merged]

            if still_missing:
                missing_names = [s.get("name") for s in still_missing]
                follow_up_msg = AIMessage(
                    content=f"Lütfen şu bilgileri de giriniz: {', '.join(missing_names)}"
                )
                logger.info("partial_extraction_asking_more", missing=missing_names)
                return {"collected_parameters": merged, "messages": [follow_up_msg]}

            logger.info("extraction_completed_via_schema", params=merged)
            return {"collected_parameters": merged}

        elif utility_calls:
            # The LLM decided to call a utility tool (e.g., get_account_types)

            messages_to_pass.append(
                response
            )  # Append the AIMessage containing the tool_calls

            for tc in utility_calls:
                tool_name = tc["name"]
                if tool_name in utility_tools_map:
                    logger.info(
                        "executing_utility_tool", tool=tool_name, args=tc["args"]
                    )
                    tool_func = utility_tools_map[tool_name]
                    try:
                        tool_result = tool_func.invoke(tc["args"])
                    except Exception as e:
                        tool_result = f"Error executing tool: {e}"

                    messages_to_pass.append(
                        ToolMessage(content=str(tool_result), tool_call_id=tc["id"])
                    )
                else:
                    messages_to_pass.append(
                        ToolMessage(
                            content=f"Tool {tool_name} not found.",
                            tool_call_id=tc["id"],
                        )
                    )
            # Loop continues so the LLM can process the ToolMessage results

    # If we hit max iterations without returning, just ask user as fallback
    logger.warning("extractor_hit_max_iterations")
    fallback_msg = AIMessage(
        content="İşleminize devam edebilmem için biraz daha detaya ihtiyacım var."
    )
    return {"messages": [fallback_msg]}
