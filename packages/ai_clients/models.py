"""AI client models and types."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from enum import Enum


class AIProvider(str, Enum):
    """AI provider types."""
    CLAUDE = "claude"
    OPENAI = "openai"
    GEMINI = "gemini"
    GROK = "grok"


class AIMessage(BaseModel):
    """AI message model."""
    role: str  # "user", "assistant", "system"
    content: str


class AIRequest(BaseModel):
    """AI API request model."""
    messages: List[AIMessage]
    max_tokens: Optional[int] = 4000
    temperature: Optional[float] = 0.7
    model: Optional[str] = None


class AIResponse(BaseModel):
    """AI API response model."""
    content: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    provider: AIProvider
    raw_response: Optional[Dict[str, Any]] = None


class AIClientConfig(BaseModel):
    """AI client configuration."""
    api_key: str
    base_url: Optional[str] = None
    model: str
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 30