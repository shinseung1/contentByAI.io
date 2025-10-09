"""Content generation models."""

from typing import Optional, List, Union, Dict, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Text, Integer

from packages.core.database import Base


class GenerationStatus(str, Enum):
    """Content generation status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"


class GenerationRequest(BaseModel):
    """Content generation request model."""
    topic: str = Field(..., min_length=1, max_length=500, description="Content topic")
    provider: Optional[str] = Field(None, max_length=50, description="AI provider (gemini, openai, claude, grok)")
    tone: Optional[str] = Field("professional", max_length=50, description="Content tone")
    word_count: Optional[int] = Field(800, ge=300, le=3000, description="Target word count")
    include_images: bool = Field(True, description="Whether to include images")
    target_language: str = Field("ko", max_length=10, description="Target language code")
    num_options: Optional[int] = Field(1, ge=1, le=5, description="Number of content options to generate")
    balance_word_count: bool = Field(True, description="Whether to balance word count across multiple options")
    workflow_template_id: Optional[int] = Field(None, description="ID of workflow template to use")


class ImageInfo(dict):
    """ImageInfo that inherits from dict to be JSON serializable."""
    def __init__(self, url: str = "", alt: str = "", caption: str = "", **kwargs):
        super().__init__()
        self.update({
            "url": url,
            "alt": alt,
            "caption": caption,
            **kwargs
        })
    
    # Add properties for compatibility
    @property
    def url(self):
        return self.get("url", "")
    
    @property
    def alt(self):
        return self.get("alt", "")
    
    @property
    def caption(self):
        return self.get("caption", "")

# Also create the function for backward compatibility
def create_image_info(url: str = "", alt: str = "", caption: str = "", **kwargs) -> dict:
    """Create image info as ImageInfo object (which is a dict)."""
    return ImageInfo(url=url, alt=alt, caption=caption, **kwargs)


class GeneratedContent(BaseModel):
    """Generated content model."""
    title: str = Field(..., description="Content title")
    content: str = Field(..., description="Main content body (HTML)")
    markdown_content: Optional[str] = Field(None, description="Markdown version of content")
    summary: Optional[str] = Field(None, description="Content summary")
    tags: List[str] = Field(default_factory=list, description="Content tags")
    images: List[Dict[str, Any]] = Field(default_factory=list, description="Related images")
    options: Optional[List['GeneratedContent']] = Field(None, description="Multiple content options")
    word_count_actual: Optional[int] = Field(None, description="Actual word count of the content")
    
    def __init__(self, **data):
        # Convert any ImageInfo objects to ensure they're JSON serializable
        if 'images' in data and data['images']:
            processed_images = []
            for img in data['images']:
                if isinstance(img, dict):
                    processed_images.append(img)
                elif hasattr(img, 'url'):  # ImageInfo-like object
                    processed_images.append({
                        "url": str(img.url) if hasattr(img, 'url') else "",
                        "alt": str(img.alt) if hasattr(img, 'alt') else "",
                        "caption": str(img.caption) if hasattr(img, 'caption') else ""
                    })
            data['images'] = processed_images
        super().__init__(**data)


class GenerationResponse(BaseModel):
    """Content generation response model."""
    job_id: str = Field(..., description="Unique job identifier")
    status: GenerationStatus = Field(..., description="Generation status")
    message: str = Field(..., description="Status message")
    progress: Optional[float] = Field(None, ge=0.0, le=1.0, description="Completion progress (0-1)")
    content: Optional[GeneratedContent] = Field(None, description="Generated content (if completed)")
    error: Optional[str] = Field(None, description="Error message (if failed)")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")
    tone: Optional[str] = Field(None, description="Content tone")
    word_count: Optional[int] = Field(None, description="Target word count")


# Database Models
class GenerationJob(Base):
    """Content generation job database model."""
    __tablename__ = "generation_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String, unique=True, nullable=False, index=True)
    provider = Column(String, nullable=False)
    topic = Column(String, nullable=False, index=True)
    tone = Column(String, nullable=False, default="professional")
    word_count = Column(Integer, nullable=False, default=800)
    include_images = Column(String, nullable=False, default="1")  # SQLite boolean as string
    target_language = Column(String, nullable=False, default="ko")
    num_options = Column(Integer, nullable=False, default=1)
    balance_word_count = Column(String, nullable=False, default="1")  # SQLite boolean as string
    
    status = Column(String, nullable=False, default=GenerationStatus.PENDING)
    progress = Column(Integer, nullable=False, default=0)
    content = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())