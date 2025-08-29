"""Content generation models."""

from typing import Optional, List
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, JSON, Text, Integer, Float
from sqlalchemy.sql import func

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
    tone: Optional[str] = Field("professional", max_length=50, description="Content tone")
    word_count: Optional[int] = Field(800, ge=300, le=3000, description="Target word count")
    include_images: bool = Field(True, description="Whether to include images")
    target_language: str = Field("ko", max_length=10, description="Target language code")


class GeneratedContent(BaseModel):
    """Generated content model."""
    title: str = Field(..., description="Content title")
    content: str = Field(..., description="Main content body")
    summary: Optional[str] = Field(None, description="Content summary")
    tags: List[str] = Field(default_factory=list, description="Content tags")
    images: List[str] = Field(default_factory=list, description="Image URLs or paths")


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


# Database Models
class GenerationJob(Base):
    """Content generation job database model."""
    __tablename__ = "generation_jobs"

    id = Column(String, primary_key=True)
    topic = Column(String, nullable=False, index=True)
    tone = Column(String, nullable=True)
    word_count = Column(Integer, nullable=True)
    include_images = Column(String, nullable=True)  # Store as string for boolean
    target_language = Column(String, nullable=False, default="ko")
    
    status = Column(String, nullable=False, default=GenerationStatus.PENDING)
    progress = Column(Float, nullable=True)
    message = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # Generated content
    generated_title = Column(String, nullable=True)
    generated_content = Column(Text, nullable=True)
    generated_summary = Column(Text, nullable=True)
    generated_tags = Column(JSON, nullable=True)
    generated_images = Column(JSON, nullable=True)
    
    job_metadata = Column(JSON, nullable=True)