"""Provides core functionalities for the store module."""
import json
import redis.asyncio as redis
from typing import Optional
from app.core.state import SessionState

class StateStore:
    """Async Redis interface to save and load state between requests."""
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """Executes the   init   operation."""
        self.redis = redis.from_url(redis_url, decode_responses=True)

    async def get_session(self, session_id: str) -> SessionState:
        """Retrieve session state from Redis or create a new one."""
        data = await self.redis.get(f"session:{session_id}")
        if data:
            return SessionState.model_validate_json(data)
        # Return a fresh state if not found
        return SessionState(session_id=session_id)

    async def save_session(self, state: SessionState):
        """Save session state to Redis."""
        await self.redis.setex(
            f"session:{state.session_id}", 
            3600, 
            state.model_dump_json()
        )
