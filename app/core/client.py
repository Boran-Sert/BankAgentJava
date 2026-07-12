"""Provides core functionalities for the client module."""
import httpx
import logging
import asyncio
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class AsyncHTTPClient:
    """
    Fintech-grade asynchronous HTTP client with connection pooling,
    timeouts, and automatic retries with exponential backoff for external service calls (e.g., LLM APIs).
    """
    def __init__(self, timeout_seconds: int = 10, max_retries: int = 3):
        """Executes the   init   operation."""
        self.timeout = httpx.Timeout(timeout_seconds)
        self.max_retries = max_retries
        # Connection pooling is handled automatically by AsyncClient
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def post(self, url: str, json_data: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        for attempt in range(1, self.max_retries + 1):
            try:
                response = await self.client.post(url, json=json_data, headers=headers)
                response.raise_for_status()
                return response
            except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError) as e:
                logger.warning(f"HTTP POST {url} failed on attempt {attempt}/{self.max_retries}: {e}")
                if attempt == self.max_retries:
                    logger.error(f"Max retries reached for {url}")
                    raise
                # Exponential backoff: 2s, 4s, 8s
                await asyncio.sleep(2 ** attempt)
        
    async def close(self):
        """Closes the underlying HTTPX client. Call this on app shutdown."""
        await self.client.aclose()

# Singleton instance to be used across the app
http_client = AsyncHTTPClient()
