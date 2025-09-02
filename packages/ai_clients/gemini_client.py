"""Google Gemini API client."""

from typing import Dict, Any
import httpx
from .base import BaseAIClient
from .models import AIRequest, AIResponse, AIProvider, AIClientConfig


class GeminiClient(BaseAIClient):
    """Google Gemini API client implementation."""
    
    def __init__(self, config: AIClientConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://generativelanguage.googleapis.com"
    
    def _get_headers(self) -> dict:
        """Get headers for Gemini API."""
        return {
            "Content-Type": "application/json"
        }
    
    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate response using Gemini API."""
        await self._ensure_client()
        
        formatted_request = self._format_request(request)
        model = request.model or self.config.model
        
        url = f"{self.base_url}/v1beta/models/{model}:generateContent"
        params = {"key": self.config.api_key}
        
        response = await self._client.post(
            url,
            json=formatted_request,
            params=params
        )
        response.raise_for_status()
        
        response_data = response.json()
        return self._parse_response(response_data)
    
    def _format_request(self, request: AIRequest) -> dict:
        """Format request for Gemini API."""
        contents = []
        system_instruction = None
        
        for msg in request.messages:
            if msg.role == "system":
                system_instruction = {"parts": [{"text": msg.content}]}
            else:
                role = "user" if msg.role == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.content}]
                })
        
        formatted = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature if request.temperature is not None else self.config.temperature,
                "maxOutputTokens": request.max_tokens or self.config.max_tokens
            }
        }
        
        if system_instruction:
            formatted["systemInstruction"] = system_instruction
            
        return formatted
    
    def _parse_response(self, response_data: dict) -> AIResponse:
        """Parse Gemini API response."""
        content = ""
        if (response_data.get("candidates") and 
            len(response_data["candidates"]) > 0):
            candidate = response_data["candidates"][0]
            if candidate.get("content") and candidate["content"].get("parts"):
                content = candidate["content"]["parts"][0].get("text", "")
        
        usage = response_data.get("usageMetadata", {})
        
        return AIResponse(
            content=content,
            model=self.config.model,
            tokens_used=usage.get("candidatesTokenCount"),
            finish_reason=response_data.get("candidates", [{}])[0].get("finishReason"),
            provider=AIProvider.GEMINI,
            raw_response=response_data
        )