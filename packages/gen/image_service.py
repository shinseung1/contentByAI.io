"""Image service for content generation."""

import aiohttp
import asyncio
from typing import List, Optional, Dict, Any


class ImageService:
    """Service for fetching related images."""
    
    def __init__(self):
        self.unsplash_access_key = None  # Add to config if needed
    
    async def get_related_images(self, topic: str, count: int = 5) -> List[Dict[str, Any]]:
        """Get related images for a topic."""
        try:
            # Try Unsplash API first if available
            if self.unsplash_access_key:
                return await self._get_unsplash_images(topic, count)
            else:
                # Fallback to curated image suggestions
                return self._get_fallback_images(topic, count)
        except Exception:
            # Always return fallback images if API fails
            return self._get_fallback_images(topic, count)
    
    async def _get_unsplash_images(self, topic: str, count: int) -> List[Dict[str, Any]]:
        """Get images from Unsplash API."""
        async with aiohttp.ClientSession() as session:
            url = f"https://api.unsplash.com/search/photos"
            params = {
                "query": topic,
                "per_page": count,
                "orientation": "landscape"
            }
            headers = {
                "Authorization": f"Client-ID {self.unsplash_access_key}"
            }
            
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    images = []
                    
                    for photo in data.get("results", []):
                        from .models import create_image_info
                        images.append(create_image_info(
                            url=photo["urls"]["regular"],
                            alt=photo.get("alt_description", f"Image related to {topic}"),
                            caption=photo.get("description", f"Related to {topic}")
                        ))
                    
                    return images
                else:
                    return self._get_fallback_images(topic, count)
    
    def _get_fallback_images(self, topic: str, count: int) -> List[Dict[str, Any]]:
        """Get fallback images using Picsum or suggested topics."""
        images = []
        
        # Generate different image placeholders
        from .models import create_image_info
        for i in range(min(count, 5)):
            images.append(create_image_info(
                url=f"https://picsum.photos/800/450?random={hash(topic + str(i)) % 1000}",
                alt=f"{topic} 관련 이미지 {i+1}",
                caption=f"{topic}에 대한 일러스트레이션 {i+1}"
            ))
        
        return images
    
    def _get_suggested_search_terms(self, topic: str) -> List[str]:
        """Get suggested search terms for better image results."""
        # Basic keyword mapping for better image search
        keyword_map = {
            "AI": ["artificial intelligence", "robot", "technology", "future"],
            "인공지능": ["artificial intelligence", "robot", "technology", "future"],
            "ChatGPT": ["AI", "chatbot", "conversation", "technology"],
            "미래": ["future", "tomorrow", "innovation", "progress"],
            "기술": ["technology", "innovation", "digital", "computer"],
            "비즈니스": ["business", "office", "meeting", "corporate"],
            "교육": ["education", "learning", "school", "knowledge"],
            "건강": ["health", "wellness", "medical", "fitness"],
            "여행": ["travel", "vacation", "adventure", "explore"],
            "음식": ["food", "cooking", "restaurant", "cuisine"]
        }
        
        for key, terms in keyword_map.items():
            if key.lower() in topic.lower():
                return terms[:3]  # Return top 3 related terms
        
        return [topic]  # Return original topic if no mapping found