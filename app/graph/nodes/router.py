"""Provides core functionalities for the router module."""
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from app.graph.state import AgentState
from app.core.logger import logger
from app.core.vector_db import vdb
from app.core.config import settings
from app.core.llm_factory import llm_engine

class IntentClassification(BaseModel):
    """Classifies the user's intent."""
    detected_intent: Optional[str] = Field(
        description="If the user wants to start a new transaction, write the exact ID of that transaction. If they are answering questions for the active transaction, write null."
    )
    is_answering: bool = Field(
        description="Is the user answering the active transaction? True if yes."
    )

def router_node(state: AgentState) -> dict:
    """
    Analyzes the user's intent using an LLM Routing Agent. 
    Routes to the appropriate tool or detects context switches dynamically.
    """
    logger.info("node_execution", node="router_node", session_id=state.get("session_id"))
    
    messages = state.get("messages", [])
    if not messages:
        return {}
        
    last_user_message = next((m.content for m in reversed(messages) if isinstance(m, HumanMessage)), None)
    if not last_user_message:
        return {}
        
    active_intent = state.get("active_intent")
    
    # 1. Retrieve Candidate Tools with a very low threshold (0.1) to get top candidates
    found_tools = vdb.find_tools_for_domain(
        domain="BANKING", 
        query=last_user_message, 
        top_k=5,
        threshold=0.1
    )
    
    # 2. Call LLM for Dynamic Classification
    system_prompt = f"""You are a Banking Routing Agent.
Analyze the user's latest message and determine their intent.

Active Intent: {active_intent if active_intent else 'None'}
Candidate Tools (Possible New Intents): {found_tools}
Special Intent: CANCEL_TRANSACTION (Use this ONLY if the user explicitly wants to cancel/abort the Active Intent)

Rules:
1. If the user explicitly requests one of the 'Candidate Tools' (and it is different from the Active Intent), write the exact name of that tool in the detected_intent field.
2. If the user explicitly cancels or aborts the Active Intent (e.g. "vazgeçtim", "iptal et"), write CANCEL_TRANSACTION in the detected_intent field.
3. If the user is answering a question related to the Active Intent (e.g., providing parameters), write null in detected_intent and set is_answering to true.
NEVER MAKE ASSUMPTIONS.
"""
    
    new_intent = None
    try:
        # We use bind_tools to enforce structured output just like extractor_node
        llm_with_tools = llm_engine.bind_tools([IntentClassification])
        response = llm_with_tools.invoke([SystemMessage(content=system_prompt)] + messages)
        
        if hasattr(response, 'tool_calls') and len(response.tool_calls) > 0:
            args = response.tool_calls[0].get("args", {})
            new_intent = args.get("detected_intent")
            logger.info("llm_routing_decision", detected_intent=new_intent, is_answering=args.get("is_answering"))
    except Exception as e:
        logger.error("intent_classification_failed", error=str(e))
        # Fallback to strict VDB if LLM fails
        fallback_tools = vdb.find_tools_for_domain(
            domain="BANKING", 
            query=last_user_message, 
            threshold=0.85
        )
        new_intent = fallback_tools[0] if fallback_tools else None
        
    if new_intent == "CANCEL_TRANSACTION":
        logger.info("transaction_cancelled_by_user", intent=active_intent)
        return {
            "active_intent": None,
            "expected_specs": [],
            "collected_parameters": {},
            "grounded_parameters": {},
            "confirmation_status": "IDLE",
            "messages": [AIMessage(content="İşleminiz iptal edilmiştir. Başka nasıl yardımcı olabilirim?")]
        }
    
    # 3. Handle Interruption / Context Switch
    if active_intent and new_intent and new_intent != active_intent:
        logger.info("task_interrupted", old_intent=active_intent, new_intent=new_intent)
        
        pending_tasks = state.get("pending_tasks", [])
        
        # Check if new_intent is already in the cache (pending_tasks)
        found_idx = None
        for i, task in enumerate(pending_tasks):
            if task.get("active_intent") == new_intent:
                found_idx = i
                break
                
        # Push current active_intent to stack
        pending_tasks.append({
            "active_intent": active_intent,
            "expected_specs": state.get("expected_specs", []),
            "collected_parameters": state.get("collected_parameters", {}),
            "grounded_parameters": state.get("grounded_parameters", {}),
            "confirmation_status": state.get("confirmation_status", "IDLE"),
            "requires_confirmation": state.get("requires_confirmation", False)
        })
        
        if found_idx is not None:
            # Restore the task from cache
            restored_task = pending_tasks.pop(found_idx)
            logger.info("task_restored_from_cache", restored_intent=new_intent)
            
            # Enforce max limit of 5
            if len(pending_tasks) > 5:
                pending_tasks = pending_tasks[-5:]
                
            return {
                "active_intent": restored_task.get("active_intent"),
                "expected_specs": restored_task.get("expected_specs", []),
                "collected_parameters": restored_task.get("collected_parameters", {}),
                "grounded_parameters": restored_task.get("grounded_parameters", {}),
                "pending_tasks": pending_tasks,
                "confirmation_status": restored_task.get("confirmation_status", "IDLE"),
                "requires_confirmation": restored_task.get("requires_confirmation", False)
            }
        else:
            # Fetch specs for the NEW intent from the registry
            from app.core.tool_registry import tool_registry
            new_tool = tool_registry.get_tool(new_intent)
            new_specs = [s.dict() for s in new_tool.specs] if new_tool else []
            requires_conf = (new_tool.risk_level.name == "MUTATING_CRITICAL") if new_tool else False
            
            # Enforce max limit of 5
            if len(pending_tasks) > 5:
                pending_tasks = pending_tasks[-5:]
                
            # Start new intent
            return {
                "active_intent": new_intent,
                "expected_specs": new_specs,
                "collected_parameters": {},
                "grounded_parameters": {},
                "pending_tasks": pending_tasks,
                "confirmation_status": "IDLE",
                "requires_confirmation": requires_conf
            }
        
    # 4. Handle First Task Start
    if not active_intent and new_intent:
        logger.info("new_task_started", intent=new_intent)
        
        # Fetch specs for the NEW intent from the registry
        from app.core.tool_registry import tool_registry
        new_tool = tool_registry.get_tool(new_intent)
        new_specs = [s.dict() for s in new_tool.specs] if new_tool else []
        requires_conf = (new_tool.risk_level.name == "MUTATING_CRITICAL") if new_tool else False
        
        return {
            "active_intent": new_intent,
            "expected_specs": new_specs,
            "collected_parameters": {},
            "grounded_parameters": {},
            "confirmation_status": "IDLE",
            "requires_confirmation": requires_conf
        }
        
    # 5. Handle Chitchat / Unknown
    if not active_intent and not new_intent:
        logger.info("no_intent_found", message=last_user_message)
        return {
            "messages": [AIMessage(content="Size nasıl yardımcı olabilirim? (Örn: Para transferi yapmak istiyorum)")]
        }
        
    # 6. User is answering questions for current intent
    return {}
