"""Image service for content generation."""

import aiohttp
import asyncio
import hashlib
import base64
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from database import DatabaseManager, ImageCache
import io


class ImageService:
    """Service for fetching related images with caching."""
    
    def __init__(self):
        self.unsplash_access_key = None  # Add to config if needed
        self.db = DatabaseManager()
        self._ai_config = None  # AI configuration for image term generation
    
    async def get_related_images(self, topic: str, count: int = 5) -> List[Dict[str, Any]]:
        """Get related images for a topic with caching."""
        try:
            # Try Unsplash API first if available
            if self.unsplash_access_key:
                images = await self._get_unsplash_images(topic, count)
            else:
                # Fallback to curated image suggestions
                images = self._get_fallback_images(topic, count)
            
            # Cache and process images
            processed_images = []
            for img in images:
                cached_img = await self._process_and_cache_image(img)
                if cached_img:
                    processed_images.append(cached_img)
            
            return processed_images
        except Exception as e:
            print(f"Error getting related images: {e}")
            # Always return fallback images if API fails
            return self._get_fallback_images(topic, count)
    
    async def _get_unsplash_images(self, topic: str, count: int) -> List[Dict[str, Any]]:
        """Get images from Unsplash API."""
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
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
        """Get fallback images using topic-related keywords with consistent URLs."""
        images = []
        
        # Get related search terms for better image relevance
        related_terms = self._get_suggested_search_terms(topic)
        
        # Create deterministic seed based on topic for consistent images
        import hashlib
        topic_seed = int(hashlib.md5(topic.encode()).hexdigest()[:8], 16)
        
        from .models import create_image_info
        for i in range(min(count, 5)):
            # Use different related terms for variety
            search_term = related_terms[i % len(related_terms)] if related_terms else "business"
            
            # Use deterministic image ID based on topic and index for consistent caching
            image_id = (topic_seed + i) % 1000
            
            # Use specific image IDs from Unsplash for consistent results
            images.append(create_image_info(
                url=f"https://source.unsplash.com/800x450/?{search_term}&sig={image_id}",
                alt=f"{topic} 관련 이미지 {i+1} - {search_term}",
                caption=f"{topic}에 대한 {search_term} 관련 이미지"
            ))
        
        return images
    
    def _get_suggested_search_terms(self, topic: str) -> List[str]:
        """Get suggested search terms for better image results."""
        topic_lower = topic.lower()
        
        # Enhanced keyword mapping for better image search
        keyword_map = {
            # Tech & AI
            "ai": ["artificial-intelligence", "robot", "technology", "future", "digital"],
            "인공지능": ["artificial-intelligence", "robot", "technology", "future"],
            "chatgpt": ["ai", "chatbot", "conversation", "technology"],
            "기술": ["technology", "innovation", "digital", "computer"],
            "디지털": ["digital", "technology", "computer", "innovation"],
            
            # Business & Marketing
            "비즈니스": ["business", "office", "meeting", "corporate", "professional"],
            "마케팅": ["marketing", "advertising", "business", "strategy"],
            "창업": ["startup", "entrepreneur", "business", "innovation"],
            "쇼핑몰": ["ecommerce", "shopping", "business", "retail"],
            "온라인": ["online", "digital", "internet", "technology"],
            
            # Content & Social Media
            "블로그": ["blog", "writing", "content", "laptop", "desk"],
            "sns": ["social-media", "smartphone", "communication", "network"],
            "유튜브": ["youtube", "video", "content", "camera"],
            "콘텐츠": ["content", "creation", "writing", "media"],
            
            # Finance & Investment
            "투자": ["investment", "finance", "money", "stock"],
            "수익": ["profit", "money", "success", "growth"],
            "돈": ["money", "finance", "cash", "wealth"],
            
            # Health & Lifestyle
            "건강": ["health", "wellness", "fitness", "exercise"],
            "운동": ["exercise", "fitness", "gym", "sport"],
            "음식": ["food", "cooking", "restaurant", "healthy"],
            "요리": ["cooking", "chef", "kitchen", "food"],
            
            # Education & Learning
            "교육": ["education", "learning", "school", "student"],
            "학습": ["learning", "study", "education", "book"],
            "공부": ["study", "learning", "education", "desk"],
            
            # Travel & Lifestyle
            "여행": ["travel", "vacation", "adventure", "landscape"],
            "휴가": ["vacation", "relax", "beach", "travel"],
            
            # Web & Programming
            "웹": ["web", "website", "computer", "coding"],
            "프로그래밍": ["programming", "coding", "computer", "developer"],
            "개발": ["development", "coding", "programming", "technology"],
        }
        
        # Check for matches in topic
        for key, terms in keyword_map.items():
            if key in topic_lower:
                return terms[:4]  # Return top 4 related terms for variety
        
        # Fallback: extract meaningful words and use business as default
        import re
        words = re.findall(r'\b[가-힣a-zA-Z]{2,}\b', topic)
        if words:
            return [words[0].lower(), "business", "professional", "modern"]
        
        return ["business", "professional", "modern", "technology"]
    
    async def get_section_specific_images(self, section_title: str, main_topic: str, count: int = 1) -> List[Dict[str, Any]]:
        """Get images specific to a section title within the main topic."""
        # Get AI-generated search terms for this specific section
        section_terms = await self._get_section_search_terms(section_title, main_topic)
        
        images = []
        from .models import create_image_info
        import hashlib
        
        # Create deterministic seed for consistent images
        combined_text = f"{main_topic}_{section_title}".lower()
        seed = int(hashlib.md5(combined_text.encode()).hexdigest()[:8], 16)
        
        for i in range(count):
            search_term = section_terms[i % len(section_terms)]
            image_id = (seed + i) % 1000
            
            images.append(create_image_info(
                url=f"https://source.unsplash.com/800x450/?{search_term}&sig={image_id}",
                alt=f"{section_title} - {search_term}",
                caption=f"{section_title}와 관련된 {search_term} 이미지"
            ))
        
        return images
    
    def _extract_keywords_from_title(self, title: str) -> List[str]:
        """Extract relevant keywords from section title."""
        import re
        
        # Remove numbers, special characters, common words
        cleaned = re.sub(r'^\d+\.\s*', '', title)  # Remove "1. " prefix
        cleaned = re.sub(r'[^\w\s가-힣]', ' ', cleaned)  # Keep only letters and Korean
        
        # Split into words and filter
        words = [word.lower().strip() for word in cleaned.split() if len(word) > 1]
        
        # Remove common words
        common_words = ['이란', '무엇인가', '방법', '사용법', '활용', '가이드', '설명']
        keywords = [word for word in words if word not in common_words]
        
        return keywords[:3]  # Return top 3 keywords
    
    async def _get_section_search_terms(self, section_title: str, main_topic: str) -> List[str]:
        """Get search terms specific to section title using AI-based analysis."""
        # Use actual AI to generate contextually relevant image search terms
        try:
            ai_terms = await self._get_ai_suggested_image_terms_async(section_title, main_topic)
            return ai_terms if ai_terms else self._get_fallback_search_terms(section_title, main_topic)
        except Exception as e:
            print(f"AI image term generation failed: {e}")
            return self._get_fallback_search_terms(section_title, main_topic)
    
    def _get_url_hash(self, url: str) -> str:
        """Generate hash for image URL."""
        return hashlib.md5(url.encode()).hexdigest()
    
    async def _process_and_cache_image(self, img_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Process and cache image, return cached version."""
        original_url = img_dict.get("url", "")
        if not original_url:
            return img_dict
        
        url_hash = self._get_url_hash(original_url)
        
        # Check if image is already cached
        cached_image = self.db.get_image_cache(url_hash)
        if cached_image:
            # Return cached image as data URL
            data_url = f"data:{cached_image.mime_type};base64,{base64.b64encode(cached_image.image_data).decode()}"
            return {
                "url": data_url,
                "alt": cached_image.alt_text,
                "caption": cached_image.caption,
                "cached": True,
                "original_url": cached_image.original_url
            }
        
        # Download and cache new image
        try:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(original_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        mime_type = response.headers.get('content-type', 'image/jpeg')
                        
                        # Get image dimensions (simplified - skip for now)
                        width, height = None, None
                        # Note: Image dimensions extraction requires PIL
                        # For now, we'll skip this and store None values
                        
                        # Save to cache
                        cache_entry = ImageCache(
                            url_hash=url_hash,
                            original_url=original_url,
                            alt_text=img_dict.get("alt", ""),
                            caption=img_dict.get("caption", ""),
                            image_data=image_data,
                            mime_type=mime_type,
                            file_size=len(image_data),
                            width=width,
                            height=height,
                            created_at=datetime.now().isoformat(),
                            access_count=1
                        )
                        
                        self.db.save_image_cache(cache_entry)
                        
                        # Return as data URL
                        data_url = f"data:{mime_type};base64,{base64.b64encode(image_data).decode()}"
                        return {
                            "url": data_url,
                            "alt": img_dict.get("alt", ""),
                            "caption": img_dict.get("caption", ""),
                            "cached": True,
                            "original_url": original_url
                        }
        except Exception as e:
            print(f"Failed to cache image {original_url}: {e}")
            # Return original URL if caching fails
            return img_dict
        
        # Return original if everything fails
        return img_dict
    
    def cleanup_cache(self, days_old: int = 30, max_size_mb: int = 100):
        """Clean up old cached images."""
        try:
            self.db.cleanup_old_images(days_old, max_size_mb)
            print(f"Image cache cleanup completed")
        except Exception as e:
            print(f"Image cache cleanup failed: {e}")
    
    def _get_ai_suggested_image_terms(self, section_title: str, main_topic: str) -> List[str]:
        """Use AI-like intelligent analysis to generate contextually relevant image search terms."""
        title_lower = section_title.lower()
        topic_lower = main_topic.lower()
        
        # Extract meaningful words from both title and topic
        import re
        title_words = re.findall(r'[가-힣a-zA-Z]{2,}', section_title)
        topic_words = re.findall(r'[가-힣a-zA-Z]{2,}', main_topic)
        
        # Filter out common non-descriptive words
        exclude_words = ['가이드', '방법', '설명', '사용법', '활용', '소개', '정보', '내용', '관련', '전체', '통합본', '완전', '정복']
        meaningful_title_words = [word for word in title_words if word.lower() not in exclude_words and len(word) >= 2]
        meaningful_topic_words = [word for word in topic_words if word.lower() not in exclude_words and len(word) >= 2]
        
        # Advanced contextual analysis - AI-like semantic understanding
        search_terms = []
        
        # Semantic mapping based on context analysis
        semantic_mappings = {
            # Travel & Tourism
            'travel_locations': {
                'keywords': ['할리우드', 'hollywood', '레드락', 'red rock', '그랜드캐년', 'grand canyon', '제주도', '제주', '서울', '부산', '경복궁', '명동'],
                'terms': ['travel-destination', 'tourist-attraction', 'landscape', 'landmark']
            },
            'transportation': {
                'keywords': ['항공', '마일리지', 'skypass', '지하철', '버스', '택시', '교통'],
                'terms': ['transportation', 'travel', 'vehicle', 'service']
            },
            'accommodation': {
                'keywords': ['호텔', '숙박', '리조트'],
                'terms': ['hotel', 'accommodation', 'hospitality', 'resort']
            },
            
            # Food & Dining
            'food_culture': {
                'keywords': ['한식', '김치', '음식', '요리', '맛집', '카페', '커피'],
                'terms': ['korean-cuisine', 'food-culture', 'restaurant', 'dining']
            },
            'markets': {
                'keywords': ['시장', '전통시장'],
                'terms': ['traditional-market', 'street-food', 'vendors', 'local-market']
            },
            
            # Business & Finance
            'business_services': {
                'keywords': ['은행', '비즈니스', '회사', '직장', '서비스'],
                'terms': ['business', 'professional', 'corporate', 'service']
            },
            'shopping': {
                'keywords': ['쇼핑', '백화점', '상점'],
                'terms': ['shopping', 'retail', 'commercial', 'marketplace']
            },
            
            # Technology & Digital
            'technology': {
                'keywords': ['기술', '디지털', '인터넷', 'ai', '인공지능'],
                'terms': ['technology', 'digital', 'innovation', 'modern']
            },
            
            # Nature & Recreation
            'nature': {
                'keywords': ['산', '등산', '바다', '해변', '공원', '강'],
                'terms': ['nature', 'outdoor', 'landscape', 'recreational']
            },
            
            # Culture & Arts
            'culture': {
                'keywords': ['문화', '역사', '예술', '축제', '전통'],
                'terms': ['cultural', 'heritage', 'traditional', 'artistic']
            },
            
            # Health & Wellness
            'healthcare': {
                'keywords': ['병원', '건강', '의료'],
                'terms': ['healthcare', 'medical', 'wellness', 'health']
            },
            
            # Education
            'education': {
                'keywords': ['학교', '대학교', '교육'],
                'terms': ['education', 'academic', 'learning', 'institutional']
            }
        }
        
        # Apply semantic analysis
        combined_text = f"{title_lower} {topic_lower}"
        matched_categories = []
        
        for category, mapping in semantic_mappings.items():
            for keyword in mapping['keywords']:
                if keyword in combined_text:
                    matched_categories.extend(mapping['terms'])
                    break
        
        # Add primary meaningful words from title and topic
        for word in meaningful_title_words[:2]:
            if word.lower() not in [term.lower() for term in search_terms]:
                search_terms.append(word.lower().replace(' ', '-'))
        
        # Add semantic terms
        search_terms.extend(matched_categories[:2])
        
        # Add contextual words from topic
        for word in meaningful_topic_words[:1]:
            if word.lower() not in [term.lower() for term in search_terms]:
                search_terms.append(word.lower().replace(' ', '-'))
        
        # Intelligent fallback based on content analysis
        if not search_terms:
            # Emergency fallback with intelligent defaults
            if any(word in topic_lower for word in ['여행', 'travel', '관광']):
                search_terms = ['travel', 'destination', 'tourism', 'adventure']
            elif any(word in topic_lower for word in ['음식', 'food', '요리']):
                search_terms = ['cuisine', 'food', 'culinary', 'dining']
            elif any(word in topic_lower for word in ['비즈니스', 'business']):
                search_terms = ['business', 'professional', 'corporate', 'meeting']
            elif any(word in topic_lower for word in ['기술', 'technology', 'tech']):
                search_terms = ['technology', 'innovation', 'digital', 'modern']
            else:
                # Ultimate fallback - use topic words directly
                search_terms = meaningful_topic_words[:2] + ['professional', 'modern']
        
        # Ensure we have exactly 4 unique, relevant terms
        unique_terms = []
        for term in search_terms:
            if term not in unique_terms and len(unique_terms) < 4:
                unique_terms.append(term)
        
        # Fill remaining slots with intelligent defaults if needed
        while len(unique_terms) < 4:
            defaults = ['professional', 'modern', 'lifestyle', 'concept']
            for default in defaults:
                if default not in unique_terms:
                    unique_terms.append(default)
                    break
        
        return unique_terms[:4]
    
    async def _get_ai_suggested_image_terms_async(self, section_title: str, main_topic: str) -> List[str]:
        """Use actual AI to generate contextually relevant image search terms."""
        try:
            # Import AI components
            from packages.ai_clients import AIClientFactory, AIProvider, AIRequest, AIMessage, AIClientConfig
            
            # Get AI configuration
            ai_config = self._get_ai_config()
            if not ai_config:
                print("No AI configuration available for image term generation")
                return []
            
            provider, config = ai_config
            
            # Create AI client
            client = AIClientFactory.create_client(provider, config)
            
            # Create prompt for AI to analyze section and generate image terms
            prompt = f"""분석 대상:
주제: "{main_topic}"  
섹션 제목: "{section_title}"

위 섹션 제목과 주제를 분석하여, 이미지 검색에 최적화된 영어 검색어 4개를 생성해주세요.

요구사항:
1. 섹션 제목의 핵심 내용을 정확히 반영
2. 실제 이미지 검색에서 관련성 높은 결과가 나올 수 있는 용어
3. 구체적이고 시각적으로 표현 가능한 개념
4. 영어로만, 하이픈(-)으로 단어 연결

예시:
- "할리우드 관광" → ["hollywood-boulevard", "hollywood-sign", "los-angeles-tourism", "movie-studios"]
- "한국 음식" → ["korean-cuisine", "traditional-food", "kimchi", "korean-restaurant"]

응답 형식 (JSON):
{{"image_terms": ["term1", "term2", "term3", "term4"]}}"""

            ai_request = AIRequest(
                messages=[
                    AIMessage(role="system", content="당신은 이미지 검색 전문가입니다. 주어진 주제와 섹션에 가장 적합한 이미지 검색어를 생성합니다."),
                    AIMessage(role="user", content=prompt)
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            # Generate terms using AI
            async with client:
                response = await client.generate(ai_request)
            
            # Parse AI response
            terms = self._parse_ai_image_terms_response(response.content)
            if terms and len(terms) >= 2:
                return terms[:4]
            else:
                print(f"AI returned insufficient terms: {terms}")
                return []
                
        except Exception as e:
            print(f"Error in AI image term generation: {e}")
            return []
    
    def _get_ai_config(self):
        """Get AI configuration from environment for image term generation."""
        try:
            from packages.core.config import get_settings
            from packages.ai_clients import AIProvider, AIClientConfig
            
            settings = get_settings()
            
            # Try to use available AI providers
            if settings.OPENAI_API_KEY:
                config = AIClientConfig(
                    api_key=settings.OPENAI_API_KEY,
                    model=settings.OPENAI_MODEL,
                    max_tokens=200,
                    temperature=0.3
                )
                return AIProvider.OPENAI, config
            elif settings.CLAUDE_API_KEY:
                config = AIClientConfig(
                    api_key=settings.CLAUDE_API_KEY,
                    model=settings.CLAUDE_MODEL,
                    max_tokens=200,
                    temperature=0.3
                )
                return AIProvider.CLAUDE, config
            elif settings.GEMINI_API_KEY:
                config = AIClientConfig(
                    api_key=settings.GEMINI_API_KEY,
                    model=settings.GEMINI_MODEL,
                    max_tokens=200,
                    temperature=0.3
                )
                return AIProvider.GEMINI, config
                
        except Exception as e:
            print(f"Failed to get AI config: {e}")
            
        return None
    
    def _parse_ai_image_terms_response(self, ai_response: str) -> List[str]:
        """Parse AI response to extract image search terms."""
        try:
            # Try to extract JSON from the response
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = ai_response[start_idx:end_idx]
                data = json.loads(json_str)
                return data.get("image_terms", [])
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Failed to parse AI image terms response: {e}")
        
        return []
    
    def _get_fallback_search_terms(self, section_title: str, main_topic: str) -> List[str]:
        """Fallback method when AI fails - use simplified intelligent analysis."""
        # Simplified version of the previous AI-like method
        title_lower = section_title.lower()
        topic_lower = main_topic.lower()
        
        # Basic intelligent mapping for common cases
        if any(term in title_lower for term in ['할리우드', 'hollywood']):
            return ['hollywood-sign', 'hollywood-boulevard', 'los-angeles', 'entertainment']
        elif any(term in title_lower for term in ['제주', 'jeju']):
            return ['jeju-island', 'korea-tourism', 'hallasan-mountain', 'island-landscape']
        elif any(term in title_lower for term in ['서울', 'seoul']):
            return ['seoul-skyline', 'korea-city', 'han-river', 'urban-landscape']
        elif any(term in title_lower for term in ['음식', 'food', '요리']):
            return ['korean-cuisine', 'food-culture', 'restaurant', 'traditional-food']
        elif any(term in title_lower for term in ['항공', 'airline']):
            return ['airplane', 'aviation', 'airport', 'flight']
        elif any(term in title_lower for term in ['호텔', 'hotel']):
            return ['luxury-hotel', 'accommodation', 'hospitality', 'hotel-room']
        elif any(term in topic_lower for term in ['여행', 'travel']):
            return ['travel-destination', 'tourism', 'vacation', 'adventure']
        elif any(term in topic_lower for term in ['비즈니스', 'business']):
            return ['business-meeting', 'corporate', 'professional', 'office']
        else:
            # Extract meaningful words and create basic terms
            import re
            words = re.findall(r'[가-힣a-zA-Z]{2,}', f"{section_title} {main_topic}")
            meaningful_words = [word.lower().replace(' ', '-') for word in words[:2] if len(word) >= 2]
            return meaningful_words + ['professional', 'modern'][:4-len(meaningful_words)]