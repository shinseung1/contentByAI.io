"""Application configuration management."""

import os
from typing import List, Optional
from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_ENV: str = Field("dev", description="Application environment")
    TZ: str = Field("Asia/Seoul", description="Timezone")
    DATABASE_URL: str = Field("sqlite:///./data/aiwriter.db", description="Database URL")
    LOG_LEVEL: str = Field("INFO", description="Log level")
    
    # API Server
    API_HOST: str = Field("0.0.0.0", description="API server host")
    API_PORT: int = Field(8000, description="API server port")
    API_CORS_ORIGINS: List[str] = Field(
        ["http://localhost:3000", "http://127.0.0.1:3000"],
        description="CORS allowed origins"
    )
    
    # WordPress
    WP_BASE_URL: Optional[str] = Field(None, description="WordPress site URL")
    WP_APP_USER: Optional[str] = Field(None, description="WordPress application user")
    WP_APP_PASSWORD: Optional[str] = Field(None, description="WordPress application password")
    
    # Google Blogger
    GOOGLE_CLIENT_ID: Optional[str] = Field(None, description="Google OAuth client ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(None, description="Google OAuth client secret")
    GOOGLE_REFRESH_TOKEN: Optional[str] = Field(None, description="Google refresh token")
    BLOGGER_BLOG_ID: Optional[str] = Field(None, description="Blogger blog ID")
    
    # AI Services
    OPENAI_API_KEY: Optional[str] = Field(None, description="OpenAI API key")
    OPENAI_MODEL: str = Field("gpt-4o", description="OpenAI model")
    CLAUDE_API_KEY: Optional[str] = Field(None, description="Claude API key")
    CLAUDE_MODEL: str = Field("claude-3-sonnet-20240229", description="Claude model")
    GEMINI_API_KEY: Optional[str] = Field(None, description="Gemini API key")
    GEMINI_MODEL: str = Field("gemini-1.5-pro", description="Gemini model")
    GROK_API_KEY: Optional[str] = Field(None, description="Grok API key")
    GROK_MODEL: str = Field("grok-beta", description="Grok model")
    
    # AI Client Settings
    AI_MAX_TOKENS: int = Field(4000, description="Maximum tokens for AI responses")
    AI_TEMPERATURE: float = Field(0.7, description="AI temperature setting")
    AI_TIMEOUT: int = Field(30, description="AI request timeout in seconds")
    PRIMARY_AI_PROVIDER: str = Field("openai", description="Primary AI provider")
    AI_FALLBACK_ENABLED: bool = Field(True, description="Enable AI fallback")
    
    ANTHROPIC_API_KEY: Optional[str] = Field(None, description="Anthropic API key")
    AI_PROVIDER: str = Field("openai", description="AI provider (openai|anthropic)")
    
    # Image Provider
    IMAGE_PROVIDER: str = Field("stock", description="Image provider (stock|gen|custom)")
    UNSPLASH_ACCESS_KEY: Optional[str] = Field(None, description="Unsplash access key")
    
    # S3/CDN
    S3_BUCKET: Optional[str] = Field(None, description="S3 bucket name")
    S3_REGION: str = Field("ap-northeast-2", description="S3 region")
    S3_ACCESS_KEY: Optional[str] = Field(None, description="S3 access key")
    S3_SECRET_KEY: Optional[str] = Field(None, description="S3 secret key")
    S3_PUBLIC_BASE: Optional[str] = Field(None, description="S3 public base URL")

    @validator("API_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        """Parse CORS origins from environment."""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()

    @validator("AI_PROVIDER")
    def validate_ai_provider(cls, v):
        """Validate AI provider."""
        valid_providers = ["openai", "anthropic"]
        if v not in valid_providers:
            raise ValueError(f"AI_PROVIDER must be one of {valid_providers}")
        return v
    
    @validator("PRIMARY_AI_PROVIDER")
    def validate_primary_ai_provider(cls, v):
        """Validate primary AI provider."""
        valid_providers = ["claude", "openai", "gemini", "grok"]
        if v not in valid_providers:
            raise ValueError(f"PRIMARY_AI_PROVIDER must be one of {valid_providers}")
        return v

    @validator("IMAGE_PROVIDER")
    def validate_image_provider(cls, v):
        """Validate image provider."""
        valid_providers = ["stock", "gen", "custom"]
        if v not in valid_providers:
            raise ValueError(f"IMAGE_PROVIDER must be one of {valid_providers}")
        return v

    def validate_wordpress_config(self) -> bool:
        """Validate WordPress configuration."""
        required_fields = [self.WP_BASE_URL, self.WP_APP_USER, self.WP_APP_PASSWORD]
        return all(field for field in required_fields)

    def validate_blogger_config(self) -> bool:
        """Validate Blogger configuration."""
        required_fields = [
            self.GOOGLE_CLIENT_ID,
            self.GOOGLE_CLIENT_SECRET,
            self.GOOGLE_REFRESH_TOKEN,
            self.BLOGGER_BLOG_ID
        ]
        return all(field for field in required_fields)

    def validate_ai_config(self) -> bool:
        """Validate AI service configuration."""
        if self.AI_PROVIDER == "openai":
            return bool(self.OPENAI_API_KEY)
        elif self.AI_PROVIDER == "anthropic":
            return bool(self.ANTHROPIC_API_KEY)
        return False

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()