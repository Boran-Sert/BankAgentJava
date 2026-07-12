"""Provides core functionalities for the endpoints module."""
import traceback
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from langchain_core.messages import HumanMessage, AIMessage

from app.core.contracts import BaseResponse, ServiceSpec
from app.core.guardrails import SanityFilter
from app.core.logger import logger
from app.graph.workflow import app_graph
import structlog

router = APIRouter()

class JavaRequest(BaseModel):
    """Defines the Javarequest structure."""
    session_id: str
    user_id: str
    message: str
    expected_specs: Optional[List[ServiceSpec]] = []
    requires_confirmation: Optional[bool] = False
    rejected_field: Optional[str] = None
    rejection_reason: Optional[str] = None

@router.post("/process_message", response_model=BaseResponse)
async def process_message(request: JavaRequest):
    """
    Main endpoint called by the Java backend.
    """
    # Bind structlog context variables for the lifetime of this request
    structlog.contextvars.bind_contextvars(
        session_id=request.session_id,
        user_id=request.user_id
    )
    
    logger.info("incoming_request", message=request.message, expected_specs=len(request.expected_specs))

    try:
        # Configuration for LangGraph Checkpointer (persistence)
        config = {"configurable": {"thread_id": request.session_id}}
        
        # We need to initialize state or fetch it to handle rejections
        # LangGraph memory saver handles state persistence automatically via invoke/get_state
        current_state = app_graph.get_state(config)
        state_values = current_state.values if current_state else {}
        
        # Update expected_specs
        if request.expected_specs:
            # We convert ServiceSpec to dict for state
            state_values["expected_specs"] = [s.dict() for s in request.expected_specs]
            
        if request.rejected_field:
            logger.warning("java_rejection", field=request.rejected_field, reason=request.rejection_reason)
            collected = state_values.get("collected_parameters", {})
            if request.rejected_field in collected:
                del collected[request.rejected_field]
            state_values["collected_parameters"] = collected
            state_values["confirmation_status"] = "IDLE"
            
            if not request.message.strip():
                # Fast-fail return to user
                return BaseResponse(
                    agent=state_values.get("active_intent", "System"),
                    intent=state_values.get("active_intent", "UNKNOWN"),
                    status="IN_PROGRESS",
                    parameters=state_values.get("collected_parameters", {}),
                    message_to_user=f"İşleminiz reddedildi: {request.rejection_reason}. Lütfen yeni bir değer giriniz."
                )

        # Append new user message to state
        # In langgraph, if we pass a dict to invoke, it merges with existing state using reducers
        input_state = {
            "messages": [HumanMessage(content=request.message)],
            "session_id": request.session_id,
            "user_id": request.user_id,
        }
        
        # If we modified expected_specs or collected_parameters (due to rejection), we pass them too
        if request.expected_specs or request.rejected_field:
            input_state["expected_specs"] = state_values.get("expected_specs", [])
            input_state["collected_parameters"] = state_values.get("collected_parameters", {})
            input_state["confirmation_status"] = state_values.get("confirmation_status", "IDLE")

        input_state["requires_confirmation"] = request.requires_confirmation

        # Execute Graph
        logger.info("invoking_stategraph")
        final_state = app_graph.invoke(input_state, config=config)
        logger.info("stategraph_execution_completed")

        # Extract outputs from final state
        active_intent = final_state.get("active_intent")
        parameters = final_state.get("collected_parameters", {})
        messages = final_state.get("messages", [])
        
        # We only want AIMessages generated during THIS specific execution run.
        # old_state messages + the new HumanMessage we just added.
        old_msg_count = len(state_values.get("messages", [])) + 1 
        new_messages = messages[old_msg_count:]
        
        ai_messages = [m.content for m in new_messages if isinstance(m, AIMessage)]
        
        if ai_messages:
            message_to_user = "\n\n".join(ai_messages)
        else:
            message_to_user = "İşleminize devam ediyorum..."
            
        status = "IN_PROGRESS"
        if not active_intent:
            status = "COMPLETED"
            
        response = BaseResponse(
            agent=active_intent or "System",
            intent=active_intent or "UNKNOWN",
            status=status,
            parameters=parameters,
            message_to_user=message_to_user
        )

        return SanityFilter.validate_final_response(response)

    except Exception as e:
        logger.exception("critical_system_error", error=str(e), traceback=traceback.format_exc())
        return SanityFilter.get_safe_fallback_response(
            "FastAPI", "Unhandled Exception Caught in LangGraph execution"
        )
