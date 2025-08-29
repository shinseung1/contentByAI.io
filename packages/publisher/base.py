"""Base publisher interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime

from .models import PublishResult, PostMetadata, PublishMode


class BasePublisher(ABC):
    """Base class for all publishers."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize publisher with configuration."""
        self.config = config
        self.platform_name = self.get_platform_name()

    @abstractmethod
    def get_platform_name(self) -> str:
        """Get platform name."""
        pass

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to the platform."""
        pass

    @abstractmethod
    async def publish_draft(
        self,
        title: str,
        content: str,
        metadata: PostMetadata,
        images: Optional[Dict[str, bytes]] = None
    ) -> PublishResult:
        """Publish as draft."""
        pass

    @abstractmethod
    async def publish_immediately(
        self,
        title: str,
        content: str,
        metadata: PostMetadata,
        images: Optional[Dict[str, bytes]] = None
    ) -> PublishResult:
        """Publish immediately."""
        pass

    @abstractmethod
    async def schedule_publish(
        self,
        title: str,
        content: str,
        metadata: PostMetadata,
        scheduled_datetime: datetime,
        images: Optional[Dict[str, bytes]] = None
    ) -> PublishResult:
        """Schedule publication."""
        pass

    async def publish(
        self,
        title: str,
        content: str,
        metadata: PostMetadata,
        mode: PublishMode,
        scheduled_datetime: Optional[datetime] = None,
        images: Optional[Dict[str, bytes]] = None
    ) -> PublishResult:
        """Generic publish method."""
        if mode == PublishMode.DRAFT:
            return await self.publish_draft(title, content, metadata, images)
        elif mode == PublishMode.PUBLISH:
            return await self.publish_immediately(title, content, metadata, images)
        elif mode == PublishMode.SCHEDULE:
            if not scheduled_datetime:
                raise ValueError("scheduled_datetime is required for SCHEDULE mode")
            return await self.schedule_publish(
                title, content, metadata, scheduled_datetime, images
            )
        else:
            raise ValueError(f"Unsupported publish mode: {mode}")

    @abstractmethod
    async def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get post by ID."""
        pass

    @abstractmethod
    async def update_post(
        self,
        post_id: str,
        title: str,
        content: str,
        metadata: PostMetadata
    ) -> PublishResult:
        """Update existing post."""
        pass

    @abstractmethod
    async def delete_post(self, post_id: str) -> bool:
        """Delete post."""
        pass

    def validate_config(self) -> bool:
        """Validate publisher configuration."""
        return True

    def get_required_fields(self) -> list:
        """Get list of required configuration fields."""
        return []

    def sanitize_content(self, content: str) -> str:
        """Sanitize content for the platform."""
        return content

    def format_metadata(self, metadata: PostMetadata) -> Dict[str, Any]:
        """Format metadata for the platform."""
        return metadata.dict()