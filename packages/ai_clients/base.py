"""Base AI client class."""

from abc import ABC, abstractmethod
from typing import Optional
import httpx
from .models import AIRequest, AIResponse, AIClientConfig


class BaseAIClient(ABC):
    """Base class for AI API clients."""
    
    def __init__(self, config: AIClientConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def _ensure_client(self):
        """Ensure HTTP client is initialized."""
        if not self._client:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout),
                headers=self._get_headers()
            )
    
    @abstractmethod
    def _get_headers(self) -> dict:
        """Get HTTP headers for API requests."""
        pass
    
    @abstractmethod
    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate AI response."""
        pass
    
    @abstractmethod
    def _format_request(self, request: AIRequest) -> dict:
        """Format request for specific API."""
        pass
    
    @abstractmethod
    def _parse_response(self, response_data: dict) -> AIResponse:
        """Parse API response."""
        pass