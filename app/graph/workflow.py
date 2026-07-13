"""Provides core functionalities for the workflow module."""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from app.graph.state import AgentState
from app.graph.nodes import (
    router_node,
    extractor_node,
    grounding_node,
    confirmation_node,
    execution_node,
)
from app.core.logger import logger


def build_graph():
    """Builds and compiles the LangGraph StateGraph."""
    logger.info("building_stategraph")

    builder = StateGraph(AgentState)

    # Add Nodes
    builder.add_node("router", router_node)
    builder.add_node("extractor", extractor_node)
    builder.add_node("grounding", grounding_node)
    builder.add_node("confirmation", confirmation_node)
    builder.add_node("execution", execution_node)

    # Define routing logic
    def route_from_router(state: AgentState):
        """Executes the Route from router operation."""
        if not state.get("active_intent"):
            return END
        return "extractor"

    def route_from_extractor(state: AgentState):
        """Executes the Route from extractor operation."""
        # If the extractor generated an AIMessage asking a question, it ends here to wait for user
        # This implies if "collected_parameters" didn't cover all "expected_specs", we wait.
        expected = len(state.get("expected_specs", []))
        collected = len(state.get("collected_parameters", {}))

        # We also check if the last message is an AIMessage asking a question
        # If it is, we pause. If all params are collected, we move to grounding.
        if expected > 0 and collected < expected:
            return END
        return "grounding"

    def route_from_grounding(state: AgentState):
        """Executes the Route from grounding operation."""
        # Eğer yukarıda grounding_error fırlattıysak işlemi bitir, cevabı kullanıcıya göster
        if state.get("grounding_error"):
            return END

        # For now, we assume grounding succeeds.
        return "confirmation"

    def route_from_confirmation(state: AgentState):
        """Executes the Route from confirmation operation."""
        status = state.get("confirmation_status", "IDLE")
        if status == "PENDING" or status == "REJECTED":
            return END
        return "execution"

    def route_from_execution(state: AgentState):
        """Executes the Route from execution operation."""
        # If there are pending tasks restored, we need to loop back to extractor
        if state.get("active_intent"):
            return "extractor"
        return END

    # Edges
    builder.add_edge(START, "router")
    builder.add_conditional_edges("router", route_from_router)
    builder.add_conditional_edges("extractor", route_from_extractor)
    builder.add_conditional_edges("grounding", route_from_grounding)
    builder.add_conditional_edges("confirmation", route_from_confirmation)
    builder.add_conditional_edges("execution", route_from_execution)

    # Checkpointer for persistence and race-condition safety
    memory = MemorySaver()

    # Compile
    app_graph = builder.compile(checkpointer=memory)
    logger.info("stategraph_compiled_successfully")
    return app_graph


# Global compiled graph instance
app_graph = build_graph()
