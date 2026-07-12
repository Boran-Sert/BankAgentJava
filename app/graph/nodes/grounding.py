"""Provides core functionalities for the grounding module."""
from app.graph.state import AgentState
from app.core.logger import logger

def grounding_node(state: AgentState) -> dict:
    """
    Translates raw text parameters into concrete backend identifiers (e.g. UUIDs).
    """
    logger.info("node_execution", node="grounding_node", session_id=state.get("session_id"))
    
    collected = state.get("collected_parameters", {})
    grounded = state.get("grounded_parameters", {})
    
    # In a real app, we would query the database here using state['user_id']
    # For now, we mock the grounding.
    new_grounded = {}
    for key, value in collected.items():
        if key not in grounded:
            # Sadece ID alanları için mock DB dönüşümü (grounding) yapalım.
            # Tutar (amount) gibi sayısal alanlara metin eklersek Pydantic float dönüşümünde hata verir.
            if "id" in key.lower():
                new_grounded[key] = f"grounded_{value}"
            else:
                new_grounded[key] = value
            
    if new_grounded:
        merged = {**grounded, **new_grounded}
        logger.info("parameters_grounded", grounded_count=len(new_grounded))
        return {"grounded_parameters": merged}
        
    return {}
