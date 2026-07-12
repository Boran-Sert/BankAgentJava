"""Provides core functionalities for the main module."""
from fastapi import FastAPI
from app.api import endpoints
from app.core.contracts import ToolSchema, RiskLevel, ServiceSpec
from app.core.logger import logger, setup_logger

def create_app() -> FastAPI:
    """Executes the Create app operation."""
    # Logger is already setup in app.core.logger, but we can ensure it's initialized
    setup_logger()
    logger.info("application_starting")

    app = FastAPI(
        title="BankAgent LangGraph AI",
        description="Scalable, asynchronous, and contract-driven banking AI microservice using LangGraph.",
        version="2.0.0",
    )

    # Seed the Vector DB with LangChain Tools
    from app.core.vector_db import vdb
    from app.core.tool_registry import tool_registry
    from app.agents.tools import banking_tools
    
    # Auto-discover schemas from LangChain tools
    tool_registry.load_langchain_tools(banking_tools)
    
    # Index generated schemas into VectorDB
    vdb.index_tools(tool_registry.get_all_tools())
    logger.info("vector_db_seeded")

    # Include routers
    app.include_router(endpoints.router, prefix="/api/v1")

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
