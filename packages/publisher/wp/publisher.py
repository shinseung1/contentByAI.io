"""WordPress publisher implementation."""

from datetime import datetime
from typing import Any, Dict, Optional
import re

from ..base import BasePublisher
from ..models import PublishResult, PostMetadata, PublishMode
from .client import WordPressClient
from packages.core.exceptions import PublishingError, ConfigurationError
from packages.core.logging import get_logger

logger = get_logger("wordpress.publisher")


class WordPressPublisher(BasePublisher):
    """WordPress publisher implementation."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize WordPress publisher."""
        super().__init__(config)
        
        if not self.validate_config():
            raise ConfigurationError("Invalid WordPress configuration")
        
        self.client = None

    def get_platform_name(self) -> str:
        """Get platform name."""
        return "wordpress"

    def validate_config(self) -> bool:
        """Validate WordPress configuration."""
        required_fields = ["base_url", "username", "password"]
        return all(self.config.get(field) for field in required_fields)

    def get_required_fields(self) -> list:
        """Get required configuration fields."""
        return ["base_url", "username", "password"]

    async def _get_client(self) -> WordPressClient:
        """Get WordPress client instance."""
        if not self.client:
            self.client = WordPressClient(
                self.config["base_url"],
                self.config["username"],
                self.config["password"]
            )
        return self.client

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to WordPress."""
        client = await self._get_client()
        async with client:
            return await client.test_connection()

    def sanitize_content(self, content: str) -> str:
        """Sanitize content for WordPress."""
        # WordPress handles HTML well, minimal sanitization needed
        # Remove any script tags for security
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        return content

    def format_metadata(self, metadata: PostMetadata) -> Dict[str, Any]:
        """Format metadata for WordPress."""
        return {
            "slug": metadata.slug,
            "excerpt": metadata.excerpt,
            "categories": metadata.categories,
            "tags": metadata.tags,
            "featured_image": metadata.featured_image,
            "schedule": metadata.schedule
        }

    async def _upload_images(
        self, 
        client: WordPressClient, 
        images: Optional[Dict[str, bytes]]
    ) -> Dict[str, Any]:
        """Upload images and return media information."""
        media_info = {}
        
        if not images:
            return media_info
            
        for filename, file_data in images.items():
            try:
                media_data = await client.upload_media(file_data, filename)
                media_info[filename] = {
                    "id": media_data["id"],
                    "url": media_data["source_url"],
                    "alt": media_data.get("alt_text", ""),
                }
                logger.info(f"Uploaded image: {filename} (ID: {media_data['id']})")
            except Exception as e:
                logger.error(f"Failed to upload image {filename}: {e}")
                raise PublishingError(f"Image upload failed: {filename}", platform="wordpress")
        
        return media_info

    async def _replace_image_urls(self, content: str, media_info: Dict[str, Any]) -> str:
        """Replace local image paths with WordPress URLs."""
        for filename, info in media_info.items():
            # Replace various possible image reference patterns
            patterns = [
                rf'src="[^"]*{re.escape(filename)}"',
                rf"src='[^']*{re.escape(filename)}'",
                rf'{re.escape(filename)}'
            ]
            
            for pattern in patterns:
                content = re.sub(pattern, f'src="{info["url"]}"', content)
        
        return content

    async def _create_wordpress_post(
        self,
        client: WordPressClient,
        title: str,
        content: str,
        metadata: PostMetadata,
        status: str,
        date: Optional[str] = None,
        images: Optional[Dict[str, bytes]] = None
    ) -> PublishResult:
        """Create WordPress post with all metadata."""
        try:
            # Upload images first
            media_info = await self._upload_images(client, images)
            
            # Replace image URLs in content
            if media_info:
                content = await self._replace_image_urls(content, media_info)
            
            # Ensure categories and tags exist
            category_ids = await client.ensure_categories(metadata.categories)
            tag_ids = await client.ensure_tags(metadata.tags)
            
            # Handle featured image
            featured_media_id = None
            if metadata.featured_image and metadata.featured_image in media_info:
                featured_media_id = media_info[metadata.featured_image]["id"]
            
            # Create post
            post_data = await client.create_post(
                title=title,
                content=self.sanitize_content(content),
                status=status,
                slug=metadata.slug,
                excerpt=metadata.excerpt,
                categories=category_ids,
                tags=tag_ids,
                featured_media=featured_media_id,
                date=date
            )
            
            return PublishResult(
                success=True,
                post_id=str(post_data["id"]),
                post_url=post_data["link"],
                published_at=datetime.fromisoformat(post_data["date"].replace("Z", "+00:00")),
                metadata={
                    "wordpress_id": post_data["id"],
                    "status": post_data["status"],
                    "media_info": media_info,
                    "category_ids": category_ids,
                    "tag_ids": tag_ids
                }
            )
            
        except Exception as e:
            logger.error(f"WordPress post creation failed: {e}")
            return PublishResult(
                success=False,
                error_message=str(e),
                error_code="WORDPRESS_POST_FAILED"
            )

    async def publish_draft(
        self,
        title: str,
        content: str,
        metadata: PostMetadata,
        images: Optional[Dict[str, bytes]] = None
    ) -> PublishResult:
        """Publish as draft."""
        client = await self._get_client()
        async with client:
            return await self._create_wordpress_post(
                client, title, content, metadata, "draft", images=images
            )

    async def publish_immediately(
        self,
        title: str,
        content: str,
        metadata: PostMetadata,
        images: Optional[Dict[str, bytes]] = None
    ) -> PublishResult:
        """Publish immediately."""
        client = await self._get_client()
        async with client:
            return await self._create_wordpress_post(
                client, title, content, metadata, "publish", images=images
            )

    async def schedule_publish(
        self,
        title: str,
        content: str,
        metadata: PostMetadata,
        scheduled_datetime: datetime,
        images: Optional[Dict[str, bytes]] = None
    ) -> PublishResult:
        """Schedule publication."""
        client = await self._get_client()
        async with client:
            # WordPress expects ISO format for scheduled posts
            date_str = scheduled_datetime.isoformat()
            
            return await self._create_wordpress_post(
                client, title, content, metadata, "future", date=date_str, images=images
            )

    async def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get post by ID."""
        client = await self._get_client()
        async with client:
            return await client.get_post(post_id)

    async def update_post(
        self,
        post_id: str,
        title: str,
        content: str,
        metadata: PostMetadata
    ) -> PublishResult:
        """Update existing post."""
        client = await self._get_client()
        async with client:
            try:
                # Ensure categories and tags exist
                category_ids = await client.ensure_categories(metadata.categories)
                tag_ids = await client.ensure_tags(metadata.tags)
                
                post_data = await client.update_post(
                    post_id,
                    title=title,
                    content=self.sanitize_content(content),
                    slug=metadata.slug,
                    excerpt=metadata.excerpt,
                    categories=category_ids,
                    tags=tag_ids
                )
                
                return PublishResult(
                    success=True,
                    post_id=post_id,
                    post_url=post_data["link"],
                    published_at=datetime.fromisoformat(post_data["modified"].replace("Z", "+00:00"))
                )
                
            except Exception as e:
                logger.error(f"WordPress post update failed: {e}")
                return PublishResult(
                    success=False,
                    error_message=str(e),
                    error_code="WORDPRESS_UPDATE_FAILED"
                )

    async def delete_post(self, post_id: str) -> bool:
        """Delete post."""
        client = await self._get_client()
        async with client:
            return await client.delete_post(post_id)