"""WordPress REST API client."""

import base64
from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx

from packages.core.exceptions import APIError, AuthenticationError
from packages.core.logging import get_logger
from packages.core.retry import async_retry_on_exception

logger = get_logger("wordpress")


class WordPressClient:
    """WordPress REST API client."""

    def __init__(self, base_url: str, username: str, password: str):
        """Initialize WordPress client."""
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        
        # Create Basic Auth token
        credentials = f"{username}:{password}"
        token = base64.b64encode(credentials.encode()).decode()
        
        self.headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "User-Agent": "AIWriter/1.0"
        }
        
        self.client = httpx.AsyncClient(headers=self.headers, timeout=30.0)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    @async_retry_on_exception(max_retries=3)
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to WordPress site."""
        try:
            response = await self.client.get(f"{self.base_url}/wp-json/wp/v2/users/me")
            if response.status_code == 200:
                user_data = response.json()
                return {
                    "status": "connected",
                    "user_id": user_data.get("id"),
                    "username": user_data.get("username"),
                    "capabilities": user_data.get("capabilities", {})
                }
            elif response.status_code == 401:
                raise AuthenticationError("WordPress authentication failed")
            else:
                response.raise_for_status()
        except httpx.RequestError as e:
            raise APIError(f"Connection to WordPress failed: {e}")

    @async_retry_on_exception(max_retries=3)
    async def upload_media(
        self, 
        file_data: bytes, 
        filename: str,
        alt_text: Optional[str] = None,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload media file to WordPress."""
        try:
            headers = {
                **self.headers,
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "application/octet-stream"
            }
            
            response = await self.client.post(
                f"{self.base_url}/wp-json/wp/v2/media",
                content=file_data,
                headers=headers
            )
            
            if response.status_code == 201:
                media_data = response.json()
                media_id = media_data["id"]
                
                # Update alt text and caption if provided
                if alt_text or caption:
                    update_data = {}
                    if alt_text:
                        update_data["alt_text"] = alt_text
                    if caption:
                        update_data["caption"] = {"rendered": caption}
                    
                    await self.client.post(
                        f"{self.base_url}/wp-json/wp/v2/media/{media_id}",
                        json=update_data
                    )
                
                return media_data
            else:
                response.raise_for_status()
                
        except httpx.RequestError as e:
            raise APIError(f"Media upload failed: {e}")

    @async_retry_on_exception(max_retries=3)
    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get all categories."""
        try:
            response = await self.client.get(
                f"{self.base_url}/wp-json/wp/v2/categories",
                params={"per_page": 100}
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise APIError(f"Failed to get categories: {e}")

    @async_retry_on_exception(max_retries=3)
    async def get_tags(self) -> List[Dict[str, Any]]:
        """Get all tags."""
        try:
            response = await self.client.get(
                f"{self.base_url}/wp-json/wp/v2/tags",
                params={"per_page": 100}
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise APIError(f"Failed to get tags: {e}")

    @async_retry_on_exception(max_retries=2)
    async def create_category(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create new category."""
        try:
            data = {"name": name, "description": description}
            response = await self.client.post(
                f"{self.base_url}/wp-json/wp/v2/categories",
                json=data
            )
            
            if response.status_code == 201:
                return response.json()
            else:
                response.raise_for_status()
                
        except httpx.RequestError as e:
            raise APIError(f"Failed to create category: {e}")

    @async_retry_on_exception(max_retries=2)
    async def create_tag(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create new tag."""
        try:
            data = {"name": name, "description": description}
            response = await self.client.post(
                f"{self.base_url}/wp-json/wp/v2/tags",
                json=data
            )
            
            if response.status_code == 201:
                return response.json()
            else:
                response.raise_for_status()
                
        except httpx.RequestError as e:
            raise APIError(f"Failed to create tag: {e}")

    async def ensure_categories(self, category_names: List[str]) -> List[int]:
        """Ensure categories exist and return their IDs."""
        if not category_names:
            return []
            
        existing_categories = await self.get_categories()
        category_map = {cat["name"].lower(): cat["id"] for cat in existing_categories}
        
        category_ids = []
        for name in category_names:
            name_lower = name.lower()
            if name_lower in category_map:
                category_ids.append(category_map[name_lower])
            else:
                # Create new category
                new_category = await self.create_category(name)
                category_ids.append(new_category["id"])
                logger.info(f"Created new category: {name}")
        
        return category_ids

    async def ensure_tags(self, tag_names: List[str]) -> List[int]:
        """Ensure tags exist and return their IDs."""
        if not tag_names:
            return []
            
        existing_tags = await self.get_tags()
        tag_map = {tag["name"].lower(): tag["id"] for tag in existing_tags}
        
        tag_ids = []
        for name in tag_names:
            name_lower = name.lower()
            if name_lower in tag_map:
                tag_ids.append(tag_map[name_lower])
            else:
                # Create new tag
                new_tag = await self.create_tag(name)
                tag_ids.append(new_tag["id"])
                logger.info(f"Created new tag: {name}")
        
        return tag_ids

    @async_retry_on_exception(max_retries=3)
    async def create_post(
        self,
        title: str,
        content: str,
        status: str = "draft",
        slug: Optional[str] = None,
        excerpt: Optional[str] = None,
        categories: Optional[List[int]] = None,
        tags: Optional[List[int]] = None,
        featured_media: Optional[int] = None,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create WordPress post."""
        try:
            data = {
                "title": title,
                "content": content,
                "status": status
            }
            
            if slug:
                data["slug"] = slug
            if excerpt:
                data["excerpt"] = excerpt
            if categories:
                data["categories"] = categories
            if tags:
                data["tags"] = tags
            if featured_media:
                data["featured_media"] = featured_media
            if date:
                data["date"] = date
            
            response = await self.client.post(
                f"{self.base_url}/wp-json/wp/v2/posts",
                json=data
            )
            
            if response.status_code == 201:
                return response.json()
            else:
                response.raise_for_status()
                
        except httpx.RequestError as e:
            raise APIError(f"Failed to create post: {e}")

    @async_retry_on_exception(max_retries=3)
    async def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get post by ID."""
        try:
            response = await self.client.get(
                f"{self.base_url}/wp-json/wp/v2/posts/{post_id}"
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                response.raise_for_status()
                
        except httpx.RequestError as e:
            raise APIError(f"Failed to get post: {e}")

    @async_retry_on_exception(max_retries=3)
    async def update_post(
        self,
        post_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        status: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Update existing post."""
        try:
            data = {}
            if title:
                data["title"] = title
            if content:
                data["content"] = content
            if status:
                data["status"] = status
            data.update(kwargs)
            
            response = await self.client.post(
                f"{self.base_url}/wp-json/wp/v2/posts/{post_id}",
                json=data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                response.raise_for_status()
                
        except httpx.RequestError as e:
            raise APIError(f"Failed to update post: {e}")

    @async_retry_on_exception(max_retries=3)
    async def delete_post(self, post_id: str) -> bool:
        """Delete post."""
        try:
            response = await self.client.delete(
                f"{self.base_url}/wp-json/wp/v2/posts/{post_id}",
                params={"force": True}
            )
            
            return response.status_code == 200
            
        except httpx.RequestError as e:
            logger.error(f"Failed to delete post {post_id}: {e}")
            return False