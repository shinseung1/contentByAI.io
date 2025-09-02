"""AI client factory for creating different AI clients."""

from typing import Dict, Any, Optional
from .models import AIProvider, AIClientConfig
from .base import BaseAIClient
from .claude_client import ClaudeClient
from .openai_client import OpenAIClient
from .gemini_client import GeminiClient
from .grok_client import GrokClient


class AIClientFactory:
    """Factory class for creating AI clients."""
    
    _client_classes = {
        AIProvider.CLAUDE: ClaudeClient,
        AIProvider.OPENAI: OpenAIClient,
        AIProvider.GEMINI: GeminiClient,
        AIProvider.GROK: GrokClient
    }
    
    @classmethod
    def create_client(
        cls, 
        provider: AIProvider, 
        config: AIClientConfig
    ) -> BaseAIClient:
        """Create an AI client for the specified provider."""
        if provider not in cls._client_classes:
            raise ValueError(f"Unsupported AI provider: {provider}")
        
        client_class = cls._client_classes[provider]
        return client_class(config)
    
    @classmethod
    def create_from_settings(
        cls,
        provider: AIProvider,
        api_key: str,
        model: str,
        base_url: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        timeout: int = 30
    ) -> BaseAIClient:
        """Create an AI client from individual settings."""
        config = AIClientConfig(
            api_key=api_key,
            base_url=base_url,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout
        )
        
        return cls.create_client(provider, config)
    
    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """Get list of supported AI providers."""
        return list(cls._client_classes.keys())


class MultiAIClient:
    """Client that can use multiple AI providers with fallback."""
    
    def __init__(self, clients: Dict[AIProvider, BaseAIClient]):
        self.clients = clients
        self.primary_provider: Optional[AIProvider] = None
        if clients:
            self.primary_provider = next(iter(clients.keys()))
    
    def set_primary_provider(self, provider: AIProvider) -> None:
        """Set the primary AI provider."""
        if provider not in self.clients:
            raise ValueError(f"Provider {provider} not configured")
        self.primary_provider = provider
    
    async def generate(
        self, 
        request, 
        provider: Optional[AIProvider] = None,
        fallback: bool = True
    ):
        """Generate response with optional fallback to other providers."""
        target_provider = provider or self.primary_provider
        
        if not target_provider:
            raise ValueError("No provider specified and no primary provider set")
        
        if target_provider not in self.clients:
            raise ValueError(f"Provider {target_provider} not configured")
        
        try:
            async with self.clients[target_provider] as client:
                return await client.generate(request)
        except Exception as e:
            if not fallback or len(self.clients) == 1:
                raise e
            
            for fallback_provider, fallback_client in self.clients.items():
                if fallback_provider != target_provider:
                    try:
                        async with fallback_client as client:
                            return await client.generate(request)
                    except Exception:
                        continue
            
            raise e