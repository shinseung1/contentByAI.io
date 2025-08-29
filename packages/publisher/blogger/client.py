"""Google Blogger API client."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from packages.core.exceptions import APIError, AuthenticationError
from packages.core.logging import get_logger
from packages.core.retry import async_retry_on_exception
import asyncio

logger = get_logger("blogger")


class BloggerClient:
    """Google Blogger API client."""

    def __init__(self, client_id: str, client_secret: str, refresh_token: str, blog_id: str):
        """Initialize Blogger client."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.blog_id = blog_id
        
        self.credentials = None
        self.service = None
        
        self._init_credentials()

    def _init_credentials(self):
        """Initialize OAuth2 credentials."""
        self.credentials = Credentials(
            token=None,
            refresh_token=self.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=["https://www.googleapis.com/auth/blogger"]
        )

    def _get_service(self):
        """Get Blogger API service."""
        if not self.service or not self.credentials.valid:
            if self.credentials.expired:
                self.credentials.refresh(Request())
            
            self.service = build("blogger", "v3", credentials=self.credentials, cache_discovery=False)
        
        return self.service

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to Blogger."""
        try:
            service = self._get_service()
            
            # Run in thread pool to avoid blocking
            def _test():
                blog = service.blogs().get(blogId=self.blog_id).execute()
                return {
                    "status": "connected",
                    "blog_id": blog["id"],
                    "blog_name": blog["name"],
                    "blog_url": blog["url"],
                    "posts_count": blog.get("posts", {}).get("totalItems", 0)
                }
            
            result = await asyncio.get_event_loop().run_in_executor(None, _test)
            return result
            
        except HttpError as e:
            if e.resp.status == 401:
                raise AuthenticationError("Blogger authentication failed")
            else:
                raise APIError(f"Blogger API error: {e}")
        except Exception as e:
            raise APIError(f"Connection to Blogger failed: {e}")

    async def create_post(
        self,
        title: str,
        content: str,
        labels: Optional[List[str]] = None,
        is_draft: bool = True
    ) -> Dict[str, Any]:
        """Create a new blog post."""
        try:
            service = self._get_service()
            
            post_body = {
                "title": title,
                "content": content
            }
            
            if labels:
                post_body["labels"] = labels
            
            def _create():
                return service.posts().insert(
                    blogId=self.blog_id,
                    body=post_body,
                    isDraft=is_draft
                ).execute()
            
            result = await asyncio.get_event_loop().run_in_executor(None, _create)
            return result
            
        except HttpError as e:
            logger.error(f"Blogger post creation failed: {e}")
            raise APIError(f"Failed to create Blogger post: {e}")

    async def publish_post(self, post_id: str, publish_date: Optional[str] = None) -> Dict[str, Any]:
        """Publish a post."""
        try:
            service = self._get_service()
            
            def _publish():
                if publish_date:
                    # Schedule publication
                    return service.posts().publish(
                        blogId=self.blog_id,
                        postId=post_id,
                        publishDate=publish_date
                    ).execute()
                else:
                    # Publish immediately
                    return service.posts().publish(
                        blogId=self.blog_id,
                        postId=post_id
                    ).execute()
            
            result = await asyncio.get_event_loop().run_in_executor(None, _publish)
            return result
            
        except HttpError as e:
            logger.error(f"Blogger post publishing failed: {e}")
            raise APIError(f"Failed to publish Blogger post: {e}")

    async def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get post by ID."""
        try:
            service = self._get_service()
            
            def _get():
                return service.posts().get(
                    blogId=self.blog_id,
                    postId=post_id
                ).execute()
            
            result = await asyncio.get_event_loop().run_in_executor(None, _get)
            return result
            
        except HttpError as e:
            if e.resp.status == 404:
                return None
            logger.error(f"Failed to get Blogger post: {e}")
            raise APIError(f"Failed to get Blogger post: {e}")

    async def update_post(
        self,
        post_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Update existing post."""
        try:
            service = self._get_service()
            
            # Get current post first
            current_post = await self.get_post(post_id)
            if not current_post:
                raise APIError(f"Post {post_id} not found")
            
            # Update fields
            post_body = {
                "id": post_id,
                "title": title or current_post["title"],
                "content": content or current_post["content"]
            }
            
            if labels is not None:
                post_body["labels"] = labels
            elif "labels" in current_post:
                post_body["labels"] = current_post["labels"]
            
            def _update():
                return service.posts().patch(
                    blogId=self.blog_id,
                    postId=post_id,
                    body=post_body
                ).execute()
            
            result = await asyncio.get_event_loop().run_in_executor(None, _update)
            return result
            
        except HttpError as e:
            logger.error(f"Blogger post update failed: {e}")
            raise APIError(f"Failed to update Blogger post: {e}")

    async def delete_post(self, post_id: str) -> bool:
        """Delete post."""
        try:
            service = self._get_service()
            
            def _delete():
                service.posts().delete(
                    blogId=self.blog_id,
                    postId=post_id
                ).execute()
                return True
            
            result = await asyncio.get_event_loop().run_in_executor(None, _delete)
            return result
            
        except HttpError as e:
            if e.resp.status == 404:
                return True  # Already deleted
            logger.error(f"Failed to delete Blogger post {post_id}: {e}")
            return False

    async def revert_to_draft(self, post_id: str) -> Dict[str, Any]:
        """Revert published post to draft."""
        try:
            service = self._get_service()
            
            def _revert():
                return service.posts().revert(
                    blogId=self.blog_id,
                    postId=post_id
                ).execute()
            
            result = await asyncio.get_event_loop().run_in_executor(None, _revert)
            return result
            
        except HttpError as e:
            logger.error(f"Failed to revert Blogger post to draft: {e}")
            raise APIError(f"Failed to revert post to draft: {e}")

    async def get_blog_info(self) -> Dict[str, Any]:
        """Get blog information."""
        try:
            service = self._get_service()
            
            def _get_info():
                return service.blogs().get(blogId=self.blog_id).execute()
            
            result = await asyncio.get_event_loop().run_in_executor(None, _get_info)
            return result
            
        except HttpError as e:
            logger.error(f"Failed to get blog info: {e}")
            raise APIError(f"Failed to get blog info: {e}")

    async def search_posts(
        self,
        query: str,
        max_results: int = 20,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search posts."""
        try:
            service = self._get_service()
            
            def _search():
                request = service.posts().search(
                    blogId=self.blog_id,
                    q=query,
                    maxResults=max_results
                )
                
                if status:
                    request = request.status(status)
                
                return request.execute()
            
            result = await asyncio.get_event_loop().run_in_executor(None, _search)
            return result.get("items", [])
            
        except HttpError as e:
            logger.error(f"Failed to search posts: {e}")
            raise APIError(f"Failed to search posts: {e}")