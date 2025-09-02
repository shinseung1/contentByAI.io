"""Claude API client."""

from typing import Dict, Any
import httpx
from .base import BaseAIClient
from .models import AIRequest, AIResponse, AIProvider, AIClientConfig


class ClaudeClient(BaseAIClient):
    """Claude API client implementation."""
    
    def __init__(self, config: AIClientConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://api.anthropic.com"
    
    def _get_headers(self) -> dict:
        """Get headers for Claude API."""
        return {
            "x-api-key": self.config.api_key,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }
    
    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate response using Claude API."""
        await self._ensure_client()
        
        formatted_request = self._format_request(request)
        
        response = await self._client.post(
            f"{self.base_url}/v1/messages",
            json=formatted_request
        )
        response.raise_for_status()
        
        response_data = response.json()
        return self._parse_response(response_data)
    
    def _format_request(self, request: AIRequest) -> dict:
        """Format request for Claude API."""
        messages = []
        system_message = None
        
        for msg in request.messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        formatted = {
            "model": request.model or self.config.model,
            "max_tokens": request.max_tokens or self.config.max_tokens,
            "temperature": request.temperature if request.temperature is not None else self.config.temperature,
            "messages": messages
        }
        
        if system_message:
            formatted["system"] = system_message
            
        return formatted
    
    def _parse_response(self, response_data: dict) -> AIResponse:
        """Parse Claude API response."""
        content = ""
        if response_data.get("content") and len(response_data["content"]) > 0:
            content = response_data["content"][0].get("text", "")
        
        return AIResponse(
            content=content,
            model=response_data.get("model", ""),
            tokens_used=response_data.get("usage", {}).get("output_tokens"),
            finish_reason=response_data.get("stop_reason"),
            provider=AIProvider.CLAUDE,
            raw_response=response_data
        )