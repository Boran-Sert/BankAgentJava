"""Provides core functionalities for the confirmation module."""
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage, HumanMessage
from app.graph.state import AgentState
from app.core.logger import logger
from app.core.llm_factory import llm_engine

class ConfirmationResponse(BaseModel):
    """Defines the Confirmationresponse structure."""
    is_approved: bool = Field(description="True if the user approved the transaction, False if rejected or ambiguous.")

def confirmation_node(state: AgentState) -> dict:
    """
    Handles user confirmation for MUTATING_CRITICAL transactions using LLM structured output.
    """
    logger.info("node_execution", node="confirmation_node", session_id=state.get("session_id"))
    
    if not state.get("requires_confirmation", False):
        return {"confirmation_status": "APPROVED"}
        
    status = state.get("confirmation_status", "IDLE")
    
    if status == "IDLE":
        # Generate confirmation prompt
        intent = state.get("active_intent")
        grounded = state.get("grounded_parameters", {})
        
        sys_prompt = f"""You are a polite banking assistant.
The user is about to execute the following transaction: {intent}
With these parameters: {grounded}

Write a natural, single-sentence confirmation prompt in Turkish asking if they approve.
Remove any technical prefixes like 'grounded_' from the values.
Example: 'Son 4 hanesi 9012 olan kartınızdan 2500 TL ödeme yapılacaktır. Onaylıyor musunuz?'
Do not add any additional greetings or text, just the prompt sentence.
"""
        from langchain_core.messages import SystemMessage
        try:
            response = llm_engine.invoke([SystemMessage(content=sys_prompt)])
            prompt = response.content.strip()
        except Exception as e:
            logger.error("prompt_generation_failed", error=str(e))
            summary = ", ".join(f"{k}: {str(v).replace('grounded_', '')}" for k, v in grounded.items())
            prompt = f"İşleminiz şu şekilde gerçekleşecektir: {summary}. Onaylıyor musunuz?"
        
        logger.info("confirmation_requested", intent=state.get("active_intent"))
        return {
            "confirmation_status": "PENDING",
            "messages": [AIMessage(content=prompt)]
        }
        
    elif status == "PENDING":
        # Analyze user's response using LLM
        messages = state.get("messages", [])
        last_user_msg = next((m.content for m in reversed(messages) if isinstance(m, HumanMessage)), None)
        
        if not last_user_msg:
            return {}
            
        # Use LLM to classify yes/no instead of simple substring matching
        structured_llm = llm_engine.with_structured_output(ConfirmationResponse)
        try:
            prompt = f"""Analyze the user's following response: '{last_user_msg}'
Is this an approval (yes) message?

CRITICAL INSTRUCTIONS:
1. You MUST output your response strictly as a JSON object matching the provided schema.
2. Do NOT output any conversational text, markdown formatting (like ```json), or explanations.
3. Output ONLY the raw JSON object. Example: {{"is_approved": true}}
"""
            result = structured_llm.invoke(prompt)
            if result.is_approved:
                logger.info("transaction_approved", intent=state.get("active_intent"))
                return {"confirmation_status": "APPROVED"}
            else:
                logger.info("transaction_rejected", intent=state.get("active_intent"))
                return {
                    "confirmation_status": "REJECTED",
                    "active_intent": None,
                    "expected_specs": [],
                    "collected_parameters": {},
                    "grounded_parameters": {},
                    "messages": [AIMessage(content="İşleminiz iptal edilmiştir.")]
                }
        except Exception as e:
            logger.error("confirmation_analysis_failed", error=str(e))
            # Fallback to asking again
            return {"messages": [AIMessage(content="Lütfen net bir şekilde evet veya hayır olarak yanıtlayın.")]}
            
    return {}
