"""Provides core functionalities for the execution module."""
from langchain_core.messages import AIMessage, SystemMessage
from app.graph.state import AgentState
from app.core.logger import logger
from app.core.tool_registry import tool_registry
from app.core.llm_factory import llm_engine
import json

import app.agents.tools 

def execution_node(state: AgentState) -> dict:
    """
    Executes the actual transaction dynamically and handles restoring interrupted tasks.
    """
    logger.info("node_execution", node="execution_node", session_id=state.get("session_id"))

    intent = state.get("active_intent")
    grounded = state.get("grounded_parameters", {})
    user_id = state.get("user_id", "test_user_1")

    logger.info("executing_transaction", intent=intent, payload=grounded)

    # 1. Execute the mapped LangChain tool dynamically
    action_result = tool_registry.execute(intent, user_id=user_id, **grounded)
    
    # 2. Use LLM to generate a natural language success message based on the result
    sys_prompt = f"""You are a professional banking AI assistant.
Your task is to inform the user about the result of their latest action: '{intent}'.

Here is the raw JSON output returned by the system for this action:
---
{json.dumps(action_result, ensure_ascii=False, indent=2) if action_result else 'Success'}
---

CRITICAL INSTRUCTIONS:
1. You MUST read the raw JSON output above and extract ALL the important data points (e.g., amounts, balances, card numbers, IDs, statuses).
2. You MUST present these extracted data points to the user clearly. Do NOT hide or omit the actual numbers, values, or records.
3. If the JSON contains a list of items (e.g., multiple credit cards, transactions), list them out clearly using bullet points.
4. Write in a polite, professional, and natural conversational tone in TURKISH.
5. DO NOT use raw JSON syntax (like {{}}, [], "key": "value") in your response. Convert the data into natural language sentences or clean markdown lists.
6. Do NOT mention that you received JSON data, a system tool, or technical terms. Just answer the user directly.

OUTPUT FORMAT:
Provide the final response directly. Make it clear, data-rich, and easy to read.
"""
    try:
        response = llm_engine.invoke([SystemMessage(content=sys_prompt)])
        success_message = response.content.strip()
    except Exception as e:
        logger.error("nlg_generation_failed", error=str(e))
        success_message = f"{intent} işleminiz başarıyla tamamlandı."

    # Check if there are pending tasks in the stack
    pending_tasks = state.get("pending_tasks", [])

    if pending_tasks:
        # Pop the last interrupted task
        restored_task = pending_tasks.pop()
        restored_intent = restored_task.get("active_intent")

        logger.info("task_resumed", restored_intent=restored_intent)
        resume_message = f"{success_message}\n\nŞimdi yarım kalan {restored_intent} işleminize geri dönüyorum."

        return {
            "messages": [AIMessage(content=resume_message)],
            "active_intent": restored_intent,
            "expected_specs": restored_task.get("expected_specs", []),
            "collected_parameters": restored_task.get("collected_parameters", {}),
            "grounded_parameters": restored_task.get("grounded_parameters", {}),
            "confirmation_status": "IDLE",
            "requires_confirmation": restored_task.get("requires_confirmation", False),
            "pending_tasks": pending_tasks,
        }

    # If no pending tasks, we are completely done
    return {
        "messages": [AIMessage(content=success_message)],
        "active_intent": None,
        "expected_specs": [],
        "collected_parameters": {},
        "grounded_parameters": {},
        "confirmation_status": "IDLE",
    }
