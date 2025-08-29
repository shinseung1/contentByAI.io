"""Grok API client."""

from typing import Dict, Any
import httpx
from .base import BaseAIClient
from .models import AIRequest, AIResponse, AIProvider, AIClientConfig


class GrokClient(BaseAIClient):
    """Grok API client implementation."""
    
    def __init__(self, config: AIClientConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://api.x.ai"
    
    def _get_headers(self) -> dict:
        """Get headers for Grok API."""
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate response using Grok API."""
        await self._ensure_client()
        
        formatted_request = self._format_request(request)
        
        response = await self._client.post(
            f"{self.base_url}/v1/chat/completions",
            json=formatted_request
        )
        response.raise_for_status()
        
        response_data = response.json()
        return self._parse_response(response_data)
    
    def _format_request(self, request: AIRequest) -> dict:
        """Format request for Grok API."""
        messages = []
        
        for msg in request.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return {
            "model": request.model or self.config.model,
            "messages": messages,
            "max_tokens": request.max_tokens or self.config.max_tokens,
            "temperature": request.temperature if request.temperature is not None else self.config.temperature,
            "stream": False
        }
    
    def _parse_response(self, response_data: dict) -> AIResponse:
        """Parse Grok API response."""
        content = ""
        if (response_data.get("choices") and 
            len(response_data["choices"]) > 0 and 
            response_data["choices"][0].get("message")):
            content = response_data["choices"][0]["message"].get("content", "")
        
        usage = response_data.get("usage", {})
        
        return AIResponse(
            content=content,
            model=response_data.get("model", ""),
            tokens_used=usage.get("completion_tokens"),
            finish_reason=response_data.get("choices", [{}])[0].get("finish_reason"),
            provider=AIProvider.GROK,
            raw_response=response_data
        )