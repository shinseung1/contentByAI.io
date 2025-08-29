"""Publisher models and schemas."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, DateTime, JSON, Text, Integer
from sqlalchemy.sql import func

from packages.core.database import Base


class PublishMode(str, Enum):
    """Publishing modes."""
    DRAFT = "draft"
    PUBLISH = "publish"
    SCHEDULE = "schedule"


class PublishStatus(str, Enum):
    """Publishing job status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PublishRequest(BaseModel):
    """Publishing request model."""
    bundle_id: str = Field(..., description="Bundle ID to publish")
    platform: str = Field(..., pattern="^(wordpress|blogger)$")
    mode: PublishMode = Field(PublishMode.DRAFT)
    scheduled_datetime: Optional[datetime] = None

    @validator("scheduled_datetime")
    def validate_schedule(cls, v, values):
        """Validate scheduled datetime."""
        if values.get("mode") == PublishMode.SCHEDULE and not v:
            raise ValueError("scheduled_datetime is required for SCHEDULE mode")
        if v and v <= datetime.now():
            raise ValueError("scheduled_datetime must be in the future")
        return v


class PublishResponse(BaseModel):
    """Publishing response model."""
    job_id: str
    status: PublishStatus
    platform: str
    bundle_id: str
    mode: PublishMode
    created_at: datetime
    updated_at: datetime
    scheduled_datetime: Optional[datetime] = None
    published_url: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PostMetadata(BaseModel):
    """Post metadata model."""
    title: str
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    labels: List[str] = Field(default_factory=list)  # For Blogger
    schedule: Dict[str, Any] = Field(default_factory=dict)
    featured_image: Optional[str] = None


class PublishResult(BaseModel):
    """Publishing result model."""
    success: bool
    post_id: Optional[str] = None
    post_url: Optional[str] = None
    published_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# Database Models
class PublishJob(Base):
    """Publishing job database model."""
    __tablename__ = "publish_jobs"

    id = Column(String, primary_key=True)
    bundle_id = Column(String, nullable=False, index=True)
    platform = Column(String, nullable=False)
    mode = Column(String, nullable=False)
    status = Column(String, nullable=False, default=PublishStatus.PENDING)
    
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    scheduled_datetime = Column(DateTime, nullable=True)
    
    published_url = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Publishing details
    post_id = Column(String, nullable=True)  # Platform-specific post ID
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(DateTime, nullable=True)