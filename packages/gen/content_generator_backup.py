"""Content generator using AI clients."""

import asyncio
import uuid
import json
import os
import re
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path


def safe_print(text):
    """Safe text for printing that replaces problematic Unicode with ? for debugging.
    IMPORTANT: This function preserves Korean characters (Hangul: U+AC00-U+D7AF)."""
    if not isinstance(text, str):
        return text
    
    # Precise emoji pattern that excludes Korean characters
    emoji_pattern = re.compile("["
                              u"\U0001F600-\U0001F64F"  # emoticons
                              u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                              u"\U0001F680-\U0001F6FF"  # transport & map symbols
                              u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                              u"\U00002600-\U000027B0"  # misc symbols
                              u"\U000024C2-\U000024FF"  # enclosed symbols
                              u"\U00002700-\U000027BF"  # dingbats
                              u"\U0001F900-\U0001F9FF"  # supplemental symbols
                              "]+", flags=re.UNICODE)
    return emoji_pattern.sub('?', text)

def remove_emojis(text):
    """Remove emoji characters from text to avoid encoding issues on Windows cp949.
    IMPORTANT: This function preserves Korean characters (Hangul: U+AC00-U+D7AF)."""
    if not isinstance(text, str):
        return text
    
    # Precise emoji pattern that excludes Korean characters
    # Korean Hangul Syllables: U+AC00-U+D7AF
    # Korean Jamo: U+1100-U+11FF, U+3130-U+318F
    emoji_pattern = re.compile("["
                              u"\U0001F600-\U0001F64F"  # emoticons
                              u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                              u"\U0001F680-\U0001F6FF"  # transport & map symbols
                              u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                              u"\U00002600-\U000027B0"  # misc symbols (airplane, etc)
                              u"\U000024C2-\U000024FF"  # enclosed symbols
                              u"\U00002700-\U000027BF"  # dingbats
                              u"\U0001F900-\U0001F9FF"  # supplemental symbols
                              "]+", flags=re.UNICODE)
    return emoji_pattern.sub('', text)

from packages.ai_clients import (
    AIClientFactory,
    AIProvider,
    AIRequest,
    AIMessage,
    AIClientConfig
)
from .models import GenerationRequest, GenerationResponse, GeneratedContent, GenerationStatus
from .image_service import ImageService
from database import DatabaseManager


class ContentGenerator:
    """Content generator using AI APIs."""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.image_service = ImageService()
    
    def safe_print_str(self, text):
        """Safe print method for backward compatibility.
        IMPORTANT: This function preserves Korean characters (Hangul: U+AC00-U+D7AF)."""
        if not isinstance(text, str):
            return str(text)
        
        # Precise emoji pattern that excludes Korean characters
        import re
        emoji_pattern = re.compile("["
                                  u"\U0001F600-\U0001F64F"  # emoticons
                                  u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                  u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                  u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                  u"\U00002600-\U000027B0"  # misc symbols
                                  u"\U000024C2-\U000024FF"  # enclosed symbols
                                  u"\U00002700-\U000027BF"  # dingbats
                                  u"\U0001F900-\U0001F9FF"  # supplemental symbols
                                  "]+", flags=re.UNICODE)
        return emoji_pattern.sub(r'?', text)
    
    def create_job_id(self) -> str:
        """Create a unique job ID."""
        return str(uuid.uuid4())
    
    
    def _get_workflow_template(self, topic: str = "", template_name: str = None, template_id: int = None) -> str:
        """Get workflow template from database based on topic or name."""
        try:
            from database import DatabaseManager
            db = DatabaseManager()
            
            # Priority 1: Get specific template by ID
            if template_id:
                template = db.get_workflow_template(template_id)
                if template and template.status == 'active':
                    import json
                    steps = json.loads(template.steps)
                    # Use the first step's prompt template
                    if steps and len(steps) > 0:
                        print(f"DEBUG: Using workflow template by ID: {template.name}")
                        return steps[0].get('prompt_template', '')
            
            # Priority 2: Get specific template by name
            if template_name:
                # Get specific template by name
                templates = db.get_active_workflow_templates()
                for template in templates:
                    if template.name == template_name:
                        import json
                        steps = json.loads(template.steps)
                        # Use the first step's prompt template
                        if steps and len(steps) > 0:
                            return steps[0].get('prompt_template', '')
            else:
                # Smart template selection based on topic
                templates = db.get_active_workflow_templates()
                selected_template = None
                
                # Topic-based template selection
                topic_lower = topic.lower()
                
                # 여행 관련 키워드들
                travel_keywords = ['여행', '관광', '휴가', '해외', '국내여행', '배낭여행', '신혼여행', 
                                 '가족여행', 'solo여행', '혼여행', '호텔', '펜션', '맛집', '관광지', 
                                 '여행지', '명소', '축제', '문화', '역사', '자연', '바다', '산', 
                                 '온천', '캠핑', '트레킹', '하이킹', '스키', '해변', '섬', '도시',
                                 'travel', 'trip', 'tour', 'vacation', 'destination', 'hotel',
                                 '일본', '중국', '동남아', '유럽', '미국', '태국', '베트남',
                                 '서울', '부산', '제주도', '강원도', '경주', '전주']
                
                # 시사 관련 키워드들  
                news_keywords = ['정치', '경제', '사회', '국제', '뉴스', '이슈', '정책', '법', 
                               '선거', '정부', '국회', '대통령', '시장', '주식', '부동산', 
                               '금융', '투자', '인플레이션', '금리', '환율', '무역', '산업',
                               '코로나', '백신', '의료', '교육', '환경', '기후', '에너지',
                               '북한', '중국', '미국', '일본', '러시아', '우크라이나',
                               '분석', '전망', '동향', '트렌드', '현황', '문제', '해결',
                               '정책변화', '시장영향', '경제정책', '사회현상', '국정감사',
                               '정치분석', '경제분석', '사회분석', '국제정세', '외교',
                               'news', 'politics', 'economy', 'social', 'international',
                               'policy', 'market', 'analysis', 'trend']
                
                # 시사 템플릿 선택 (우선순위 높음)
                if any(keyword in topic_lower for keyword in news_keywords):
                    for template in templates:
                        if '시사' in template.name or 'news' in template.name.lower() or '정보전달' in template.name:
                            selected_template = template
                            print(f"DEBUG: Selected news template: {template.name}")
                            break
                
                # 여행 템플릿 선택
                elif any(keyword in topic_lower for keyword in travel_keywords):
                    for template in templates:
                        if '여행' in template.name or 'travel' in template.name.lower():
                            selected_template = template
                            print(f"DEBUG: Selected travel template: {template.name}")
                            break
                
                # 요리/음식 관련 주제는 템플릿 사용하지 않음
                cooking_keywords = ['요리', '음식', '레시피', '만들기', '조리법', '파스타', 
                                  '라면', '김치', '찌개', '국', '밥', '반찬', '디저트', 
                                  '케이크', '빵', 'cooking', 'recipe', 'food']
                
                if any(keyword in topic_lower for keyword in cooking_keywords):
                    print(f"DEBUG: Cooking topic detected, no template will be used")
                    selected_template = None
                
                # 템플릿이 선택되지 않고 요리 주제가 아니면서 활성 템플릿이 있으면 사용 안함
                # (기본 가이던스 시스템 사용하도록)
                
                if selected_template:
                    import json
                    steps = json.loads(selected_template.steps)
                    # Use the first step's prompt template
                    if steps and len(steps) > 0:
                        return steps[0].get('prompt_template', '')
            
            return ""
        except Exception as e:
            print(f"DEBUG: Failed to get workflow template: {e}")
            return ""

    
    def save_job_status(self, job_id: str, response: GenerationResponse) -> None:
        """Save job status to database."""
        from database import GenerationJob as DBGenerationJob
        
        job = DBGenerationJob(
            job_id=job_id,
            provider=response.content.get('provider', 'unknown') if response.content else 'unknown',
            topic=response.message,  # temporary
            tone='professional',  # temporary  
            status=response.status.value,
            progress=int((response.progress or 0) * 100),
            content=response.content.content if response.content else None,
            error_message=response.error,
            created_at=response.created_at or datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        self.db.save_generation_job(job)
    
    def get_job_result(self, job_id: str) -> GenerationResponse:
        """Get job result from database."""
        print(f"DEBUG: Starting get_job_result for {job_id}")
        db_job = self.db.get_generation_job(job_id)
        if not db_job:
            raise FileNotFoundError(f"Job {job_id} not found")
        
        content = None
        if db_job.content and db_job.status == 'completed':
            try:
                # Try to parse content as JSON to extract markdown_content and images
                import json
                content_data = json.loads(db_job.content)
                if isinstance(content_data, dict):
                    # Process images from saved content  
                    from .models import ImageInfo
                    processed_images = []
                    images_data = content_data.get("images", [])
                    for img in images_data:
                        if isinstance(img, dict):
                            processed_images.append(ImageInfo(
                                url=img.get("url", ""),
                                alt=img.get("alt", ""),
                                caption=img.get("caption", "")
                            ))
                    
                    content = GeneratedContent(
                        title=content_data.get("title", db_job.topic),
                        content=content_data.get("html_content", content_data.get("content", db_job.content)),
                        markdown_content=content_data.get("markdown_content"),
                        summary=content_data.get("summary"),
                        tags=content_data.get("tags", []),
                        images=processed_images,
                        word_count_actual=content_data.get("word_count_actual")
                    )
                else:
                    content = GeneratedContent(
                        title=db_job.topic,
                        content=db_job.content,
                        markdown_content=None,
                        tags=[],
                        images=[]
                    )
            except (json.JSONDecodeError, TypeError):
                content = GeneratedContent(
                    title=db_job.topic,
                    content=db_job.content,
                    markdown_content=None,
                    tags=[],
                    images=[]
                )
        
        try:
            print(f"DEBUG: db_job.tone = {safe_print(str(db_job.tone))}")
        except UnicodeEncodeError:
            print("DEBUG: db_job.tone contains Unicode characters")
        try:
            print(f"DEBUG: db_job.word_count = {db_job.word_count}")
        except UnicodeEncodeError:
            print("DEBUG: db_job.word_count contains Unicode characters")
        
        response = GenerationResponse(
            job_id=db_job.job_id,
            status=GenerationStatus(db_job.status),
            message=db_job.topic,  # Use topic as message for display
            progress=db_job.progress / 100.0 if db_job.progress else 0.0,
            content=content,
            error=db_job.error_message,
            created_at=db_job.created_at,
            completed_at=db_job.updated_at if db_job.status in ['completed', 'failed'] else None,
            tone=db_job.tone,
            word_count=db_job.word_count
        )
        
        try:
            print(f"DEBUG: response.tone = {safe_print(str(response.tone))}")
        except UnicodeEncodeError:
            print("DEBUG: response.tone contains Unicode characters")
        try:
            print(f"DEBUG: response.word_count = {response.word_count}")
        except UnicodeEncodeError:
            print("DEBUG: response.word_count contains Unicode characters")
        
        return response
    
    def list_jobs(self) -> List[str]:
        """List all job IDs from database."""
        jobs = self.db.get_generation_jobs()
        return [job.job_id for job in jobs]
    
    async def generate_content_async(self, job_id: str, request: GenerationRequest) -> None:
        """Generate content asynchronously."""
        from database import GenerationJob as DBGenerationJob
        
        print(f"DEBUG: Starting generation for job {job_id}")
        
        # Create initial job in database
        initial_job = DBGenerationJob(
            job_id=job_id,
            provider=request.provider or 'unknown',
            topic=request.topic,
            tone=request.tone or 'professional',
            word_count=request.word_count or 800,
            include_images=request.include_images,
            target_language=request.target_language,
            status='in_progress',
            progress=0,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        self.db.save_generation_job(initial_job)
        
        try:
            print(f"DEBUG: Getting AI config for {request.provider}")
            # Get AI client configuration
            ai_config = self._get_ai_config(request.provider)
            if not ai_config:
                raise ValueError("No AI configuration found")
            
            provider, config = ai_config
            print(f"DEBUG: AI config obtained, generating content")
            
            # Generate content using AI
            content = await self._generate_with_ai(provider, config, request)
            print(f"DEBUG: AI content generated: {type(content)}")
            print(f"DEBUG: Content images: {len(content.images)} items")
            
            # Re-enable image processing with new ImageInfo-as-dict approach
            if request.include_images and content:
                try:
                    images = await self.image_service.get_related_images(request.topic, 5)
                    if images:
                        content.images = images
                        print(f"DEBUG: Successfully loaded {len(images)} images")
                    else:
                        print("DEBUG: No images returned from image service")
                        content.images = []
                except Exception as e:
                    print(f"DEBUG: Image loading failed: {e}")
                    content.images = []
            
            # Update status to completed - save full content as JSON
            # Process images as plain dicts to ensure JSON serializability
            processed_images = []
            if content.images:
                for img in content.images:
                    if isinstance(img, dict):
                        # It's already a dict
                        processed_images.append(img)
                    elif hasattr(img, 'url'):
                        # It's an ImageInfo object - convert to dict
                        processed_images.append({
                            "url": img.url,
                            "alt": img.alt,
                            "caption": img.caption
                        })
            
            
            content_json = {
                "title": remove_emojis(content.title),
                "html_content": remove_emojis(content.content),
                "summary": remove_emojis(content.summary) if content.summary else None,
                "tags": [remove_emojis(tag) for tag in content.tags] if content.tags else [],
                "images": processed_images
            }
            
            # Update with separate HTML and markdown content
            job = self.db.get_generation_job(job_id)
            if job:
                job.status = 'completed'
                job.progress = 100
                # Add extensive debugging before JSON serialization
                print(f"DEBUG: About to serialize content_json")
                print(f"DEBUG: content_json type: {type(content_json)}")
                print(f"DEBUG: content_json keys: {content_json.keys()}")
                
                # Check each field for problematic objects
                for key, value in content_json.items():
                    print(f"DEBUG: {key} = {type(value)}")
                    if key == "images" and value:
                        print(f"DEBUG: images content: {value}")
                        for i, img in enumerate(value):
                            print(f"DEBUG: image {i}: {type(img)} = {img}")
                
                # Use a safer JSON serialization approach
                def safe_json_serialize(obj):
                    """Safely serialize objects to JSON, converting problematic types and handling Unicode."""
                    if hasattr(obj, '__dict__'):
                        # If it's a custom object, convert to dict
                        if hasattr(obj, 'url') and hasattr(obj, 'alt'):  # ImageInfo-like
                            return {"url": str(obj.url), "alt": str(obj.alt), "caption": str(obj.caption)}
                        return obj.__dict__
                    elif isinstance(obj, (list, tuple)):
                        return [safe_json_serialize(item) for item in obj]
                    elif isinstance(obj, dict):
                        return {k: safe_json_serialize(v) for k, v in obj.items()}
                    elif isinstance(obj, str):
                        # Handle Unicode characters by encoding/decoding safely for Windows cp949
                        try:
                            # Try to encode as cp949, if it fails, replace problematic characters
                            obj.encode('cp949')
                            return obj
                        except UnicodeEncodeError:
                            # Replace problematic Unicode characters (like emojis) with placeholder
                            import re
                            # Remove or replace emoji characters
                            emoji_pattern = re.compile("["
                                                      u"\U0001F600-\U0001F64F"  # emoticons
                                                      u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                                      u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                                      u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                                      u"\U00002702-\U000027B0"
                                                      u"\U000024C2-\U0001F251"
                                                      "]+", flags=re.UNICODE)
                            cleaned_text = emoji_pattern.sub('', obj)  # Remove emojis
                            return cleaned_text
                    else:
                        return obj
                
                try:
                    # Apply safe serialization to the entire content_json
                    safe_content_json = safe_json_serialize(content_json)
                    job.content = json.dumps(safe_content_json, ensure_ascii=False, default=str)
                    print("DEBUG: Safe JSON serialization successful")
                except Exception as json_error:
                    print(f"DEBUG: Even safe JSON failed: {json_error}")
                    # Ultimate fallback: just save the HTML content
                    job.content = json.dumps({
                        "title": remove_emojis(str(content.title)),
                        "html_content": remove_emojis(str(content.content)),
                        "summary": remove_emojis(str(content.summary)) if content.summary else "",
                        "tags": [remove_emojis(str(tag)) for tag in content.tags] if content.tags else [],
                        "images": []  # Skip images entirely if serialization fails
                    }, ensure_ascii=False)
                job.html_content = remove_emojis(content.content)
                job.markdown_content = None  # Do not save markdown content
                job.updated_at = datetime.now().isoformat()
                self.db.save_generation_job(job)
            
        except Exception as e:
            # Update status to failed
            import traceback
            error_msg = str(e)
            full_trace = traceback.format_exc()
            
            # Log to file and console for debugging with proper encoding
            try:
                import os, sys
                log_path = os.path.abspath("generation_errors.log")
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"\n=== GENERATION ERROR for job {job_id} ===\n")
                    f.write(f"Error: {error_msg}\n")
                    f.write(f"Full trace:\n{full_trace}\n")
                    f.write(f"Provider: {request.provider}\n")
                    f.write(f"Topic: {request.topic}\n")
                    f.write(f"Include images: {request.include_images}\n")
                    f.write("=== END ERROR ===\n")
                    f.flush()
                # Safe console output to avoid Unicode encoding errors
                try:
                    print(f"Error logged to: {log_path}", file=sys.stderr)
                    print(f"GENERATION ERROR: {error_msg}", file=sys.stderr)
                except UnicodeEncodeError:
                    print("Generation error occurred (with Unicode characters)", file=sys.stderr)
            except Exception as log_error:
                try:
                    print(f"Failed to write error log: {log_error}", file=sys.stderr)
                    print(f"Original error: {error_msg}", file=sys.stderr)
                except UnicodeEncodeError:
                    print("Error logging failed (Unicode encoding issue)", file=sys.stderr)
            
            self.db.update_generation_job_status(
                job_id=job_id,
                status='failed',
                progress=0,
                error_message=error_msg
            )
    
    def _get_ai_config(self, requested_provider: Optional[str] = None) -> Optional[tuple[AIProvider, AIClientConfig]]:
        """Get AI configuration from environment."""
        from packages.core.config import get_settings
        settings = get_settings()
        
        # Use requested provider if available, otherwise use primary provider
        target_provider = requested_provider.lower() if requested_provider else settings.PRIMARY_AI_PROVIDER.lower()
        
        # Try requested/primary provider first
        if target_provider == "openai" and settings.OPENAI_API_KEY:
            config = AIClientConfig(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE
            )
            return AIProvider.OPENAI, config
        
        elif target_provider == "claude" and settings.CLAUDE_API_KEY:
            config = AIClientConfig(
                api_key=settings.CLAUDE_API_KEY,
                model=settings.CLAUDE_MODEL,
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE
            )
            return AIProvider.CLAUDE, config
            
        elif target_provider == "gemini" and settings.GEMINI_API_KEY:
            config = AIClientConfig(
                api_key=settings.GEMINI_API_KEY,
                model=settings.GEMINI_MODEL,
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE
            )
            return AIProvider.GEMINI, config
            
        elif target_provider == "grok" and settings.GROK_API_KEY:
            config = AIClientConfig(
                api_key=settings.GROK_API_KEY,
                model=settings.GROK_MODEL,
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE
            )
            return AIProvider.GROK, config
        
        # Fallback: try any available API key
        if settings.OPENAI_API_KEY:
            config = AIClientConfig(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE
            )
            return AIProvider.OPENAI, config
            
        if settings.CLAUDE_API_KEY:
            config = AIClientConfig(
                api_key=settings.CLAUDE_API_KEY,
                model=settings.CLAUDE_MODEL,
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE
            )
            return AIProvider.CLAUDE, config
            
        if settings.GEMINI_API_KEY:
            config = AIClientConfig(
                api_key=settings.GEMINI_API_KEY,
                model=settings.GEMINI_MODEL,
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE
            )
            return AIProvider.GEMINI, config
            
        if settings.GROK_API_KEY:
            config = AIClientConfig(
                api_key=settings.GROK_API_KEY,
                model=settings.GROK_MODEL,
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE
            )
            return AIProvider.GROK, config
        
        return None
    
    async def _generate_with_ai(
        self, 
        provider: AIProvider, 
        config: AIClientConfig, 
        request: GenerationRequest
    ) -> GeneratedContent:
        """Generate content using AI client."""
        
        # Create AI client
        client = AIClientFactory.create_client(provider, config)
        
        # Create prompt
        system_prompt = self._create_system_prompt(request)
        user_prompt = self._create_user_prompt(request)
        
        ai_request = AIRequest(
            messages=[
                AIMessage(role="system", content=system_prompt),
                AIMessage(role="user", content=user_prompt)
            ],
            max_tokens=config.max_tokens,
            temperature=config.temperature
        )
        
        # Generate content
        async with client:
            response = await client.generate(ai_request)
        
        # Parse response into structured content
        print(f"DEBUG: Raw AI response length: {len(response.content)}")
        try:
            # Use safe printing to avoid Unicode encoding errors
            safe_preview = safe_print(response.content[:500])
            print(f"DEBUG: Raw AI response first 500 chars: {safe_preview}")
        except (UnicodeEncodeError, AttributeError):
            print("DEBUG: Raw AI response contains Unicode characters (preview skipped)")
        content = self._parse_ai_response(response.content, request)
        
        # Post-process HTML to remove white text, fix newlines, process inline links, and remove prohibited links
        if content.content:
            content.content = self._fix_white_text(content.content)
            content.content = self._fix_newline_display(content.content)
            content.content = self._process_inline_links(content.content)
            content.content = self._remove_prohibited_links_from_content(content.content)
            # Replace placeholder image URLs with actual image URLs
            if request.include_images and content.images:
                content.images = await self._replace_placeholder_images(content.images, request.topic)
                content.content = self._insert_images_into_content(content.content, content.images)
            # Try news-specific links first for current affairs topics
            content.content = await self._add_news_specific_links(content.content, request.topic, provider, config)
            # Then add place-specific links if not a news topic
            content.content = await self._add_specific_place_links(content.content, request.topic, provider, config)
            # Add specific website links (booking sites, official sites, etc.)
            content.content = self._add_specific_site_links(content.content, request.topic)
            # Move links from titles to paragraph endings
            content.content = self._move_title_links_to_paragraphs(content.content)
            # Final pass to remove any remaining Google/search links
            content.content = self._final_google_link_cleanup(content.content)
            # Skip AI-generated section links, use only inline links within content
            # content.content = await self._add_ai_generated_links(content.content, request.topic, provider, config)
        
        return content
    
    def _load_template_structure(self) -> str:
        """Load key template structure from reference_doc/templete.md"""
        import os
        try:
            # Get the project root directory
            current_dir = os.path.dirname(__file__)
            project_root = os.path.dirname(os.path.dirname(current_dir))
            template_path = os.path.join(project_root, 'reference_doc', 'templete.md')
            
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract key structure patterns from template
            key_patterns = [
                "한 줄 요약:",
                "어디로 갈까?",
                "선택 1) 비행기 + 렌터카(가장 빠름)",
                "선택 2) 자가용(로드트립 감성", 
                "선택 3) 기차·버스(느리지만",
                "한눈에 비교 표",
                "케이스별 추천",
                "자주 묻는 질문(FAQ)",
                "요약 박스"
            ]
            
            return "\n".join([f"- {pattern}" for pattern in key_patterns])
            
        except Exception as e:
            print(f"Warning: Could not load template structure: {e}")
            return ""
    
    def _create_system_prompt(self, request: GenerationRequest) -> str:
        """Create system prompt for AI using workflow templates."""
        
        # 언어 설정
        language_instruction = ""
        if request.target_language == "ko":
            language_instruction = "모든 응답은 한국어로 작성해주세요."
        elif request.target_language == "en":
            language_instruction = "Please respond in English."
        
        # 워크플로우 템플릿 확인 (ID 우선, 그 다음 주제를 기반으로 적절한 템플릿 선택)
        workflow_template = self._get_workflow_template(request.topic, template_id=request.workflow_template_id)
        if workflow_template:
            # 워크플로우 템플릿이 있으면 {topic}을 실제 주제로 교체
            template_prompt = workflow_template.replace('{topic}', request.topic)
            
            # 이미지 지시사항 (템플릿 기반일 때만)
            image_instructions = ""
            if request.include_images:
                image_instructions = f"""
**📷 이미지 포함 지시사항:**
- 총 3-5개의 관련 이미지 포함
- 각 주요 섹션마다 적절한 이미지 배치
- 이미지 alt text와 caption 상세 작성
"""
            
            return f"""
{language_instruction}

당신은 전문 콘텐츠 작성자입니다. 아래 워크플로우 템플릿에 따라 고품질 콘텐츠를 작성해주세요:

{template_prompt}

{image_instructions}

**작성 요구사항:**
- 톤: {request.tone}
- 분량: 약 {request.word_count}단어
- 대상 언어: {request.target_language}

**출력 형식:**
반드시 JSON 형태로 응답하되, 다음 구조를 따라주세요:
{{
    "title": "흥미롭고 구체적인 제목",
    "html_content": "완전한 HTML 형태의 본문 내용 (마크다운 아님, 순수 HTML로 작성)",
    "summary": "핵심 내용을 담은 2-3문장 요약",
    "tags": ["관련태그1", "관련태그2", "관련태그3"]
}}

**중요: html_content는 반드시 HTML 형식으로 작성해주세요:**
- 제목은 <h1>, <h2>, <h3> 태그 사용
- 본문은 <p> 태그 사용
- 강조는 <strong>, <em> 태그 사용
- 목록은 <ul>, <ol>, <li> 태그 사용
- 표는 <table>, <tr>, <td>, <th> 태그 사용
- 마크다운 문법(#, **, *, -, 등) 절대 사용 금지

**HTML 스타일링 지침:**
- 메인 제목: 중앙 정렬, 그라데이션 배경
- 섹션 제목: 눈에 띄는 색상과 적절한 여백
- 본문: 읽기 쉬운 폰트와 줄간격
- 강조: 배경색을 활용한 하이라이트
- 테이블: 깔끔한 헤더와 구분선
- 절대 흰색(#ffffff, #fff, white) 텍스트 금지

위 워크플로우 템플릿에 따라 "{request.topic}"에 대해 {request.word_count}단어 분량의 전문적인 콘텐츠를 작성해주세요.
"""
        
        # 워크플로우 템플릿이 없으면 기본 템플릿 사용
        return f"""
{language_instruction}

당신은 전문 콘텐츠 작성자입니다. 주제에 대한 고품질 콘텐츠를 작성해주세요.

**작성 요구사항:**
- 주제: {request.topic}
- 톤: {request.tone}
- 분량: 약 {request.word_count}단어
- 대상 언어: {request.target_language}

**기본 작성 원칙:**
- 독자에게 실질적 도움이 되는 내용 작성
- 정확하고 신뢰할 수 있는 정보 제공
- 명확하고 읽기 쉬운 구조
- SEO 최적화된 제목과 부제목 사용

**출력 형식:**
반드시 JSON 형태로 응답하되, 다음 구조를 따라주세요:
{{
    "title": "흥미롭고 구체적인 제목",
    "html_content": "완전한 HTML 형태의 본문 내용 (마크다운 아님, 순수 HTML로 작성)",
    "summary": "핵심 내용을 담은 2-3문장 요약",
    "tags": ["관련태그1", "관련태그2", "관련태그3"]
}}

**중요: html_content는 반드시 HTML 형식으로 작성해주세요:**
- 제목은 <h1>, <h2>, <h3> 태그 사용
- 본문은 <p> 태그 사용
- 강조는 <strong>, <em> 태그 사용
- 목록은 <ul>, <ol>, <li> 태그 사용
- 표는 <table>, <tr>, <td>, <th> 태그 사용
- 마크다운 문법(#, **, *, -, 등) 절대 사용 금지
"""
    

    
    def _create_user_prompt(self, request: GenerationRequest) -> str:
        """Create user prompt for AI."""
        return f"주제 '{request.topic}'에 대해 위의 지시사항에 따라 콘텐츠를 작성해주세요."
                is_ranking_topic_user = True
                break
        
        # Also check Korean numbers for user prompt
        korean_numbers = {
            '세': 3, '삼': 3, '네': 4, '사': 4, '다섯': 5, '오': 5,
            '여섯': 6, '육': 6, '일곱': 7, '칠': 7, '여덟': 8, '팔': 8,
            '아홉': 9, '구': 9, '열': 10
        }
        
        for korean_num, num_val in korean_numbers.items():
            if korean_num in topic_lower and ('가지' in topic_lower or '개' in topic_lower):
                ranking_number_user = num_val
                is_ranking_topic_user = True
                break
        
        comparison_reminder = ""
        top_reminder = ""
        
        # Generate TOP reminder if it's a ranking topic
        if is_ranking_topic_user and ranking_number_user:
            ranking_emojis = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
            section_list = []
            
            for i in range(ranking_number_user):
                rank_num = i + 1
                emoji = ranking_emojis[i] if i < len(ranking_emojis) else f"{rank_num}️⃣"
                section_list.append(f"- ## {emoji} {rank_num}위 (또는 TOP{rank_num}): [구체적 항목명] - 매우 상세한 설명 (최소 400-500단어)")
            
            sections_text = '\n'.join(section_list)
            
            top_reminder = f"""
**🏆 TOP{ranking_number_user}/순위 주제 절대 필수사항 (매우 중요!):**
주제 "{request.topic}"는 TOP{ranking_number_user} 순위 주제입니다. 반드시 다음을 지켜주세요:

**📊 필수 구조 (절대 준수):**
{sections_text}

**⚠️ 절대 규칙:**
- **정확히 {ranking_number_user}개 항목** 모두 포함 (하나도 빠뜨리면 안됨)
- **각 항목별로 큰 독립 섹션** 구성 (작은 카드로 쪼개지 말고)
- **모든 항목 균등한 분량** (400-500단어씩)
- **종합 랭킹 비교표 필수** - {ranking_number_user}개 항목 한눈에 비교
- **선택 가이드표 필수** - 상황별 추천 가이드

"""
        
        if is_comparison_topic:
            comparison_reminder = f"""
**🔥 비교 주제 필수 준수사항 (매우 중요!):**
주제 "{request.topic}"는 비교 주제입니다. 반드시 다음을 지켜주세요:
- 양쪽 모두 동등한 분량과 깊이로 다루기 (예: 동부힙합 40% + 서부힙합 40% + 비교분석 20%)
- 각 측면의 특징, 장단점, 대표 사례를 상세히 설명
- 직접 비교표 최소 3개 필수: ①기본 특징 비교 ②장단점 비교 ③선택 가이드 비교
- 편향 없는 균형잡힌 시각 유지
- 상황별 추천 가이드 제공

**⚠️ 절대 필수: HTML 비교표 3개 이상 생성**
각 비교표는 반드시 다음과 같은 완전한 HTML table 구조를 사용하세요:

```html
<table style="border-collapse: collapse; width: 100%; margin: 25px 0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
<thead>
<tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
<th style="padding: 15px 20px; text-align: left; font-weight: 600; border: none;">구분</th>
<th style="padding: 15px 20px; text-align: left; font-weight: 600; border: none;">동부힙합</th>
<th style="padding: 15px 20px; text-align: left; font-weight: 600; border: none;">서부힙합</th>
</tr>
</thead>
<tbody>
<tr style="transition: background-color 0.3s ease;">
<td style="padding: 12px 20px; border-bottom: 1px solid #eee; border-left: none; border-right: none;">특징1</td>
<td style="padding: 12px 20px; border-bottom: 1px solid #eee; border-left: none; border-right: none;">동부 특징</td>
<td style="padding: 12px 20px; border-bottom: 1px solid #eee; border-left: none; border-right: none;">서부 특징</td>
</tr>
<tr style="background-color: #f8f9ff; transition: background-color 0.3s ease;">
<td style="padding: 12px 20px; border-bottom: 1px solid #eee; border-left: none; border-right: none;">특징2</td>
<td style="padding: 12px 20px; border-bottom: 1px solid #eee; border-left: none; border-right: none;">동부 특징2</td>
<td style="padding: 12px 20px; border-bottom: 1px solid #eee; border-left: none; border-right: none;">서부 특징2</td>
</tr>
</tbody>
</table>
```

**비교표 없이는 응답하지 마세요!**

"""

        return f"""주제: {request.topic}

템플릿을 참고하여 매우 상세하고 풍부한 완전 가이드를 작성해주세요.

{comparison_reminder}

{top_reminder}

**🚫 절대 금지 (매우 중요):**
- "자세히 보기", "바로가기", "더 보기", "상세 보기" 링크 버튼 절대 생성 금지
- <a> 태그 사용 절대 금지
- 모든 외부 링크 절대 금지
- 역사, 배경, 기원, 유래 등 역사적 내용 절대 포함 금지
- "~가이드", "~완전정복", "~총정리" 같은 뻔한 제목 패턴 절대 금지
- Wikipedia, 외부 웹사이트의 실제 이미지 URL 사용 절대 금지
- <img> 태그에 실제 URL 넣지 마세요 - 이미지는 별도 처리됩니다
- **🚫 이미지 관련 텍스트 절대 금지**: "이미지", "사진", "그림", "관련 이미지", "대표 이미지", "상징하는 이미지" 등 모든 이미지 관련 텍스트 설명 절대 금지
- **🚫 이미지 설명문 절대 금지**: "(동부힙합을 상징하는 이미지)", "(관련 사진)", "(대표 이미지)" 같은 모든 형태의 이미지 설명문 생성 절대 금지
- **🚫 이미지 태그 금지**: <img> 태그나 이미지 관련 HTML 태그 직접 생성 절대 금지 - 이미지는 시스템에서 자동 처리됩니다

**📋 상세 작성 요구사항:**
각 소제목마다 다음을 반드시 포함:
- 최소 3-4개의 상세한 문단 (각 문단 150자 이상)
- 구체적인 사례와 실제 수치 제시
- 단계별 상세 설명 (1단계 → 2단계 → 3단계)
- 주의사항과 제한 조건 명시
- 실무 팁과 노하우 포함

**🎯 제목 작성 예시:**
- 김치찌개 → "집에서도 맛집 김치찌개! 황금 레시피 대공개"
- 신용카드 포인트 → "놓치면 손해! 신용카드 포인트 200% 활용 비법"
- 마일리지 적립 → "이제 걱정 끝! 마일리지 폭탄 적립 완벽 공략"

**핵심 구조 (매우 상세하게):**
# [창의적이고 매력적인 제목]
> 한 줄 요약 (실용적 혜택 강조)

## 🎯 어디로 갈까? (개요 설명)

## 🚀 선택 1) 첫 번째 방법 (3-4문단으로 상세 설명)
**⚠️ 절대 필수**: 선택 1, 2, 3을 모두 동일한 분량으로 작성해야 합니다!

## 🚗 선택 2) 두 번째 방법 (3-4문단으로 상세 설명)
**⚠️ 절대 필수**: 선택 1과 동일한 길이와 상세함으로 작성

## 🚌 선택 3) 세 번째 방법 (3-4문단으로 상세 설명)
**⚠️ 절대 필수**: 선택 1, 2와 동일한 수준의 분량과 상세함으로 작성

## 📊 한눈에 비교 표 (상세 비교표)
## 🎯 케이스별 추천 (각 케이스마다 상세 설명)
## ❓ 자주 묻는 질문(FAQ) (5개 이상, 각각 상세 답변)
## 📝 요약 박스 (핵심 정리)

**품질 기준:**
- {min_words}-{max_words}단어 (매우 풍부한 내용)
- 테이블 5-7개 이상{"" if not is_comparison_topic else " (비교 주제는 비교표 3개 필수)"}
- 링크 절대 생성 금지
- 톤: {request.tone}

{important_points}"""
        
        # Add topic-specific guidance based on detected topic type
        topic_specific_guidance = ""
        
        if is_transportation_topic:
            topic_specific_guidance = """

🚨 **교통/이동방법 주제 특별 요구사항:**
- **구체적인 교통수단 상세 설명**: 버스, 지하철, 택시, 자동차, 도보, 자전거, 기차, 항공편 등
- **실용적 정보 필수 포함**: 소요시간, 정확한 요금, 노선번호, 정류장명, 환승방법
- **단계별 이동 경로**: 출발지 → 경유지 → 목적지까지 상세한 순서 설명
- **시간표 정보**: 운행간격, 첫차/막차 시간, 주말/평일 차이점

**각 선택지별 필수 내용:**
- 선택 1: 가장 빠른 이동방법 (시간 중심)
- 선택 2: 가장 경제적인 이동방법 (비용 중심)  
- 선택 3: 가장 편리한 이동방법 (편의성 중심)"""

        elif is_food_topic:
            topic_specific_guidance = """

🍽️ **음식/요리 주제 특별 요구사항:**
- **재료 및 조리법 상세 설명**: 필수 재료, 대체 재료, 정확한 계량, 조리 순서
- **맛집 정보**: 위치, 대표 메뉴, 가격대, 영업시간, 예약 방법
- **영양 정보**: 칼로리, 영양소, 건강 효과, 주의사항
- **보관 및 섭취 팁**: 보관법, 먹는 방법, 곁들일 음식

**각 선택지별 필수 내용:**
- 선택 1: 전통적/정통 방식 
- 선택 2: 간편한/현대적 방식
- 선택 3: 고급/특별한 방식"""

        elif is_health_topic:
            topic_specific_guidance = """

🏥 **건강/의료 주제 특별 요구사항:**
- **증상 및 원인 설명**: 구체적 증상, 발생 원인, 진행 과정
- **예방 및 관리법**: 생활습관 개선, 주의사항, 예방법
- **전문 의료진 조언**: 병원 진료 시기, 검사 방법, 치료 옵션
- **⚠️ 면책조항**: "본 정보는 일반적인 건강 정보이며, 개인별 상황에 따라 다를 수 있습니다. 정확한 진단과 치료는 반드시 의료진과 상담하세요."

**각 선택지별 필수 내용:**
- 선택 1: 즉시 대처법 (응급 상황)
- 선택 2: 생활 관리법 (일상 관리)
- 선택 3: 전문 치료법 (의료진 상담)"""

        elif is_weather_topic:
            topic_specific_guidance = """

🌤️ **날씨/기후 주제 특별 요구사항:**
- **기상 정보 상세 분석**: 온도, 습도, 강수확률, 바람, 자외선 지수
- **계절별/지역별 특성**: 지역 기후 특징, 계절별 변화, 극값 정보
- **생활 영향 및 대비**: 옷차림, 외출 준비, 건강 관리, 농업/산업 영향
- **날씨 예보 해석**: 기상청 용어 설명, 확률 의미, 주의보/경보

**각 선택지별 필수 내용:**
- 선택 1: 단기 예보 (1-3일)
- 선택 2: 중기 예보 (1주일)  
- 선택 3: 장기 전망 (계절/연간)"""

        elif is_music_topic:
            topic_specific_guidance = """

🎵 **음악/엔터테인먼트 주제 특별 요구사항:**
- **장르 및 특성 분석**: 음악적 특징, 대표 아티스트, 역사적 배경
- **추천 리스트**: 상황별 추천곡, 플레이리스트 구성, 분위기별 선곡
- **감상 포인트**: 악기 구성, 보컬 특징, 가사 해석, 프로듀싱 기법
- **접근 방법**: 스트리밍 서비스, 음원 구매, 콘서트 정보

**각 선택지별 필수 내용:**
- 선택 1: 클래식/정통 추천
- 선택 2: 인기/트렌드 추천
- 선택 3: 숨은 명곡/마니아 추천"""

        elif is_tourism_topic:
            topic_specific_guidance = """

🗺️ **관광/여행지 주제 특별 요구사항:**
- **명소 상세 정보**: 위치, 특징, 볼거리, 역사적 의미, 최적 관람 시간
- **실용 정보**: 입장료, 운영시간, 주차, 대중교통 접근법, 주변 편의시설
- **계절별/시간별 특징**: 계절별 매력, 시간대별 추천, 혼잡도 정보
- **주변 관광 코스**: 인근 명소, 추천 코스, 소요시간, 연계 여행

**각 선택지별 필수 내용:**
- 선택 1: 대표 명소 (Must-See)
- 선택 2: 숨은 명소 (Hidden Gems)
- 선택 3: 체험 활동 (Activities)"""

        else:
            # Universal guidance for all other topics
            topic_specific_guidance = f"""

🎯 **"{request.topic}" 주제 맞춤 요구사항:**
- **주제의 핵심 가치**: 해당 주제가 사용자에게 제공하는 실질적 가치와 혜택을 명확히 설명
- **단계별 접근법**: 초보자부터 숙련자까지 단계별로 접근할 수 있는 방법 제시
- **실용적 팁과 노하우**: 실제 경험에서 나오는 유용한 팁과 주의사항
- **다양한 관점 제시**: 여러 각도에서 주제를 바라보고 균형잡힌 시각 제공

**각 선택지별 필수 내용:**
- 선택 1: 기본/입문자 접근법
- 선택 2: 중급/실용적 접근법  
- 선택 3: 고급/전문가 접근법

**주제 정확성 절대 준수**: 반드시 "{request.topic}"와 직접 관련된 내용만 작성하고, 다른 주제로 벗어나지 마세요."""

        if topic_specific_guidance:
            prompt += topic_specific_guidance
        
        return prompt
    
    def _convert_markdown_to_html(self, markdown_content: str) -> str:
        """Convert markdown content to HTML."""
        import re
        
        if not markdown_content:
            return ""
        
        # Convert markdown to HTML
        html = markdown_content
        
        # Headers
        html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # Bold text
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        
        # Italic text
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        
        # Blockquotes
        html = re.sub(r'^> (.*?)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)
        
        # Unordered lists
        lines = html.split('\n')
        in_list = False
        result_lines = []
        
        for line in lines:
            if re.match(r'^[\s]*[-*+] ', line):
                if not in_list:
                    result_lines.append('<ul>')
                    in_list = True
                list_item = re.sub(r'^[\s]*[-*+] (.*)', r'<li>\1</li>', line)
                result_lines.append(list_item)
            else:
                if in_list:
                    result_lines.append('</ul>')
                    in_list = False
                result_lines.append(line)
        
        if in_list:
            result_lines.append('</ul>')
        
        html = '\n'.join(result_lines)
        
        # Tables
        table_lines = html.split('\n')
        in_table = False
        table_html = []
        
        for i, line in enumerate(table_lines):
            if '|' in line and line.strip().startswith('|'):
                if not in_table:
                    table_html.append('<table>')
                    in_table = True
                
                # Check if this is a header separator line
                if re.match(r'^\|[\s\-\|]+\|$', line.strip()):
                    continue
                
                # Process table row
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                if i == 0 or (i > 0 and not re.match(r'^\|[\s\-\|]+\|$', table_lines[i-1])):
                    # First row or not preceded by separator = header
                    row_html = '<tr>' + ''.join(f'<th>{cell}</th>' for cell in cells) + '</tr>'
                else:
                    # Data row
                    row_html = '<tr>' + ''.join(f'<td>{cell}</td>' for cell in cells) + '</tr>'
                table_html.append(row_html)
            else:
                if in_table:
                    table_html.append('</table>')
                    in_table = False
                table_html.append(line)
        
        if in_table:
            table_html.append('</table>')
        
        html = '\n'.join(table_html)
        
        # Paragraphs - wrap non-HTML lines in <p> tags
        lines = html.split('\n')
        result_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not re.match(r'^<[^>]+>', line):
                # Not an HTML tag line, wrap in paragraph
                result_lines.append(f'<p>{line}</p>')
            else:
                result_lines.append(line)
        
        return '\n'.join(result_lines)

    def _parse_ai_response(self, ai_content: str, request: GenerationRequest) -> GeneratedContent:
        """Parse AI response into GeneratedContent."""
        try:
            # Remove markdown code blocks if present
            content = ai_content.strip()
            if content.startswith('```json'):
                content = content[7:]  # Remove ```json
            if content.startswith('```'):
                content = content[3:]   # Remove ```
            if content.endswith('```'):
                content = content[:-3]  # Remove closing ```
            content = content.strip()
            
            # Try to extract JSON from the response
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                
                # Parse JSON - handle encoding issues gracefully
                try:
                    data = json.loads(json_str)
                    print(f"DEBUG: JSON parsing successful")
                except json.JSONDecodeError as e:
                    print(f"DEBUG: Initial JSON parsing failed: {e}")
                    
                    # Try to fix potential encoding issues in the JSON string
                    try:
                        # First, ensure we have proper string encoding
                        if isinstance(json_str, str):
                            # Try to encode/decode to fix any encoding issues
                            json_bytes = json_str.encode('utf-8', errors='ignore')
                            fixed_json_str = json_bytes.decode('utf-8', errors='ignore')
                            data = json.loads(fixed_json_str)
                            print(f"DEBUG: JSON parsing successful after UTF-8 cleanup")
                        else:
                            raise e
                    except json.JSONDecodeError:
                        print(f"DEBUG: JSON parsing failed even after encoding fixes")
                        print(f"DEBUG: Problematic JSON (first 300 chars): {repr(json_str[:300])}")
                        # Fall back to creating basic content structure
                        data = {
                            "title": f"Content about {request.topic}",
                            "html_content": content,  # Use the raw content
                            "summary": None,
                            "tags": [],
                            "images": []
                        }
                        print(f"DEBUG: Using fallback content structure")
                
                # Process images data - now ImageInfo is dict-based so should be safe
                images_data = data.get("images", [])
                processed_images = []
                if images_data:
                    for img in images_data:
                        if isinstance(img, dict):
                            from .models import ImageInfo
                            processed_images.append(ImageInfo(
                                url=img.get("url", ""),
                                alt=img.get("alt", ""),
                                caption=img.get("caption", "")
                            ))
                
                # Handle multiple options if present
                num_options = getattr(request, 'num_options', 1)
                balance_word_count = getattr(request, 'balance_word_count', True)
                
                if num_options > 1:
                    # Check if AI response contains multiple options
                    options_data = data.get("options", [])
                    if options_data and len(options_data) >= num_options:
                        # Process multiple options
                        processed_options = []
                        contents_for_balancing = []
                        
                        for option_data in options_data[:num_options]:
                            option_content = option_data.get("html_content", option_data.get("content", ""))
                            contents_for_balancing.append(option_content)
                        
                        # Apply word count balancing if enabled
                        if balance_word_count:
                            contents_for_balancing = self._balance_word_counts(
                                contents_for_balancing, 
                                request.word_count, 
                                num_options
                            )
                        
                        # Create GeneratedContent for each option
                        for i, (option_data, balanced_content) in enumerate(zip(options_data[:num_options], contents_for_balancing)):
                            actual_word_count = self._calculate_word_count(balanced_content)
                            option = GeneratedContent(
                                title=option_data.get("title", f"Option {i+1}: {request.topic}"),
                                content=balanced_content,
                                markdown_content=option_data.get("markdown_content"),
                                summary=option_data.get("summary"),
                                tags=option_data.get("tags", []),
                                images=processed_images,
                                word_count_actual=actual_word_count
                            )
                            processed_options.append(option)
                        
                        # Return first option as main content with options array
                        main_content = processed_options[0] if processed_options else None
                        if main_content:
                            main_content.options = processed_options[1:] if len(processed_options) > 1 else None
                            return main_content
                
                # Single option or fallback
                main_content = data.get("html_content", data.get("content", ai_content))
                nested_data = None
                
                # Convert markdown to HTML if content appears to be markdown
                if isinstance(main_content, str):
                    print(f"DEBUG: Checking if content needs markdown conversion")
                    print(f"DEBUG: Content sample: {main_content[:200]}")
                    if ('# ' in main_content or '## ' in main_content or '**' in main_content or '|' in main_content or main_content.startswith('#')):
                        print(f"DEBUG: Converting markdown content to HTML")
                        main_content = self._convert_markdown_to_html(main_content)
                        print(f"DEBUG: Markdown converted to HTML, new length: {len(main_content)}")
                        print(f"DEBUG: HTML sample: {main_content[:200]}")
                
                # Check if main_content is nested JSON (common AI response issue)
                if isinstance(main_content, str) and main_content.strip().startswith('```json'):
                    try:
                        # Extract JSON from nested format
                        nested_content = main_content.strip()
                        if nested_content.startswith('```json'):
                            nested_content = nested_content[7:]  # Remove ```json
                        if nested_content.startswith('```'):
                            nested_content = nested_content[3:]   # Remove ```
                        if nested_content.endswith('```'):
                            nested_content = nested_content[:-3]  # Remove closing ```
                        nested_content = nested_content.strip()
                        
                        # Try to parse the nested JSON
                        nested_start = nested_content.find('{')
                        nested_end = nested_content.rfind('}') + 1
                        if nested_start != -1 and nested_end > nested_start:
                            nested_json = nested_content[nested_start:nested_end]
                            
                            # Parse nested JSON directly
                            try:
                                nested_data = json.loads(nested_json)
                                print(f"DEBUG: Nested JSON parsing successful")
                            except json.JSONDecodeError as e:
                                print(f"DEBUG: Nested JSON parsing failed: {e}")
                                # If nested JSON parsing fails, skip nested processing
                                nested_data = None
                            # Use the html_content from the nested JSON if successful
                            if nested_data:
                                main_content = nested_data.get("html_content", nested_data.get("content", main_content))
                                print(f"DEBUG: Fixed nested JSON content, new length: {len(main_content)}")
                    except Exception as e:
                        print(f"DEBUG: Failed to parse nested JSON: {e}")
                        # Keep original content if parsing fails
                        pass
                
                actual_word_count = self._calculate_word_count(main_content)
                
                # Extract other fields, preferring nested JSON if available
                if nested_data:
                    title = nested_data.get("title", data.get("title", f"Content about {request.topic}"))
                    markdown_content = nested_data.get("markdown_content", data.get("markdown_content"))
                    summary = nested_data.get("summary", data.get("summary"))
                    tags = nested_data.get("tags", data.get("tags", []))
                    print(f"DEBUG: Using nested JSON fields - title: {title[:50] if title else 'None'}...")
                else:
                    title = data.get("title", f"Content about {request.topic}")
                    markdown_content = data.get("markdown_content")
                    summary = data.get("summary")
                    tags = data.get("tags", [])
                
                return GeneratedContent(
                    title=title,
                    content=main_content,
                    markdown_content=markdown_content,
                    summary=summary,
                    tags=tags,
                    images=processed_images,
                    word_count_actual=actual_word_count
                )
            else:
                # Fallback: treat entire response as content  
                return GeneratedContent(
                    title=f"Content about {request.topic}",
                    content=ai_content,
                    markdown_content=None,
                    summary=None,
                    tags=[],
                    images=[]  # Force empty
                )
                
        except json.JSONDecodeError:
            # Fallback: treat entire response as content
            return GeneratedContent(
                title=f"Content about {request.topic}",
                content=ai_content,
                markdown_content=None,
                summary=None,
                tags=[],
                images=[]  # Force empty
            )
    
    def _fix_white_text(self, html_content: str) -> str:
        """Fix white, light colored, and non-black text in HTML content to use only black for base text."""
        import re
        
        if not html_content:
            return html_content
        
        # More aggressive pattern matching to ensure all non-emphasis colors become black
        color_patterns = [
            r'color:\s*#fff\b',
            r'color:\s*#ffffff\b', 
            r'color:\s*white\b',
            r'color:\s*#f[9-f]{5}\b',  # Very light colors
            r'color:\s*#[ef][ef][ef][ef][ef][ef]\b',  # Very light hex colors
            r'color:\s*rgb\(\s*25[0-5],\s*25[0-5],\s*25[0-5]\s*\)',  # RGB white/near-white
            r'color:\s*#2c3e50\b',  # Replace gray with black
            r'color:\s*#27ae60\b',  # Replace green with black (for headings)
            r'color:\s*#74b9ff\b',  # Replace light blue with black
            r'color:\s*#667eea\b',  # Replace purple with black
            r'color:\s*#3f4c6b\b',  # Replace dark blue with black
            r'color:\s*#555\b',     # Replace medium gray with black
            r'color:\s*#666\b',     # Replace medium gray with black
            r'color:\s*#777\b',     # Replace light gray with black
            r'color:\s*#888\b',     # Replace lighter gray with black
            r'color:\s*#999\b',     # Replace very light gray with black
            # Replace ANY hex color that isn't black or emphasis colors
            r'color:\s*#(?!000000|e74c3c|2980b9|e67e22|3498db)[0-9a-fA-F]{6}\b',
        ]
        
        # Default replacement color (black)
        replacement_color = '#000000'
        
        # Replace problematic colors
        fixed_html = html_content
        for pattern in color_patterns:
            fixed_html = re.sub(pattern, f'color: {replacement_color}', fixed_html, flags=re.IGNORECASE)
        
        # Force black color on common text elements - simplified approach without complex regex
        text_elements = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span', 'li', 'td', 'th']
        for element in text_elements:
            # Simple pattern to find elements with style attributes
            pattern = rf'<{element}([^>]*?)style="([^"]*?)"([^>]*?)>'
            
            def add_color_if_missing(match):
                pre = match.group(1)
                style = match.group(2)
                post = match.group(3)
                if 'color:' not in style.lower():
                    if not style.endswith(';'):
                        style += ';'
                    style += ' color: #000000;'
                return f'<{element}{pre}style="{style}"{post}>'
            
            try:
                fixed_html = re.sub(pattern, add_color_if_missing, fixed_html, flags=re.IGNORECASE)
            except re.error:
                # If regex fails, skip this element
                print(f"Regex error for element {element}, skipping...")
                continue
        
        return fixed_html
    
    def _fix_newline_display(self, html_content: str) -> str:
        """Fix visible newline characters (\\n, \\N) in HTML content."""
        import re
        
        if not html_content:
            return html_content
        
        # Simple string replacements for common problematic patterns
        fixed_html = html_content
        
        # Replace literal backslash-n and backslash-N sequences
        fixed_html = fixed_html.replace('\\n', '')
        fixed_html = fixed_html.replace('\\N', '')
        
        # Replace in quoted contexts
        fixed_html = fixed_html.replace('"\\n', '"')
        fixed_html = fixed_html.replace('"\\N', '"') 
        fixed_html = fixed_html.replace('\\n"', '"')
        fixed_html = fixed_html.replace('\\N"', '"')
        
        # Replace in HTML encoded quotes
        fixed_html = fixed_html.replace('&quot;\\n', '&quot;')
        fixed_html = fixed_html.replace('&quot;\\N', '&quot;')
        
        # Replace escaped quotes
        fixed_html = fixed_html.replace('\\&quot;', '&quot;')
        fixed_html = fixed_html.replace('\\"', '"')
        
        # Clean up multiple spaces between tags only
        fixed_html = re.sub(r'>\s+<', '><', fixed_html)
        
        return fixed_html
    
    def _process_inline_links(self, html_content: str) -> str:
        """Convert inline text links format like '사우스림(https://...)' to proper HTML links."""
        import re
        
        if not html_content:
            return html_content
        
        # Pattern to match text followed by (https://...)
        # This matches: 텍스트(https://url) or 텍스트(http://url)
        inline_link_pattern = r'([가-힣a-zA-Z0-9\s]+)\((https?://[^\)]+)\)'
        
        def replace_inline_link(match):
            text = match.group(1).strip()
            url = match.group(2)
            
            # Create styled HTML link
            return f'<a href="{url}" target="_blank" style="color: #3498db; text-decoration: none; font-weight: 500;">{text}</a>'

        # Replace all inline links
        processed_html = re.sub(inline_link_pattern, replace_inline_link, html_content)
        
        return processed_html
    
    def _remove_prohibited_links_from_content(self, html_content: str) -> str:
        """Remove any prohibited links that AI might have generated in the content."""
        import re
        
        if not html_content:
            return html_content
        
        # Find all links in the content
        link_pattern = r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>([^<]*)</a>'
        
        def filter_link(match):
            url = match.group(1).lower()
            link_text = match.group(2)
            
            # Check if URL contains prohibited patterns
            prohibited_patterns = [
                'google.com',
                'search.naver.com',
                'bing.com',
                'yahoo.com',
                '/search?',
                '/search/',
                'q=',
                '%EC%',  # URL encoded Korean
                'query=',
                'searchterm=',
            ]
            
            is_prohibited = any(pattern in url for pattern in prohibited_patterns)
            
            if is_prohibited:
                print(f"DEBUG: Removing prohibited link from content: {url}")
                # Return just the text without the link
                return link_text
            else:
                # Keep the original link
                return match.group(0)
        
        # Replace prohibited links with plain text
        cleaned_content = re.sub(link_pattern, filter_link, html_content)
        
        return cleaned_content
    
    def _insert_images_into_content(self, html_content: str, images: list) -> str:
        """Insert provided images into HTML content, replacing any existing img tags."""
        import re
        
        if not images or not html_content:
            return html_content
        
        # Remove any existing img tags from AI-generated content
        html_content = re.sub(r'<img[^>]*>', '', html_content, flags=re.IGNORECASE)
        
        # Remove image description texts that AI might have generated
        image_text_patterns = [
            r'\([^)]*이미지[^)]*\)',
            r'\([^)]*사진[^)]*\)',
            r'\([^)]*그림[^)]*\)',
            r'\([^)]*픽쳐[^)]*\)',
            r'\([^)]*picture[^)]*\)',
            r'\([^)]*photo[^)]*\)',
            r'[가-힣]*이미지[가-힣]*',
            r'[가-힣]*사진[가-힣]*',
            r'[가-힣]*그림[가-힣]*',
            r'관련\s*이미지',
            r'상징하는\s*이미지',
            r'대표\s*이미지',
            r'.*를\s*상징하는\s*이미지',
            r'.*에\s*관련된\s*이미지',
            r'.*의\s*대표\s*이미지',
            r'TOP\d+.*이미지',
            r'\d+위.*이미지',
            r'랭킹.*이미지',
            r'순위.*이미지'
        ]
        
        for pattern in image_text_patterns:
            html_content = re.sub(pattern, '', html_content, flags=re.IGNORECASE)
        
        # Clean up extra spaces left from removal
        html_content = re.sub(r'\s+', ' ', html_content)
        html_content = re.sub(r'>\s+<', '><', html_content)
        
        # Find good insertion points (after h2 or h3 headers)
        insertion_points = []
        h2_matches = re.finditer(r'</h2>', html_content, re.IGNORECASE)
        h3_matches = re.finditer(r'</h3>', html_content, re.IGNORECASE)
        
        for match in h2_matches:
            insertion_points.append(match.end())
        for match in h3_matches:
            insertion_points.append(match.end())
            
        insertion_points = sorted(insertion_points)
        
        if not insertion_points:
            # If no headers found, insert at the beginning
            insertion_points = [0]
        
        # Insert images at strategic points
        inserted_count = 0
        offset = 0
        
        for i, image in enumerate(images[:min(len(images), len(insertion_points))]):
            if inserted_count >= len(insertion_points):
                break
                
            point = insertion_points[inserted_count] + offset
            
            # Create image HTML
            image_url = image.get('url') if isinstance(image, dict) else getattr(image, 'url', '')
            image_alt = image.get('alt') if isinstance(image, dict) else getattr(image, 'alt', f'관련 이미지 {i+1}')
            image_caption = image.get('caption') if isinstance(image, dict) else getattr(image, 'caption', '')
            
            img_html = f"""
<div style="text-align: center; margin: 20px 0;">
    <img src="{image_url}" alt="{image_alt}" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />
    {f'<p style="margin-top: 8px; font-size: 14px; color: #666; font-style: italic;">{image_caption}</p>' if image_caption else ''}
</div>"""
            
            html_content = html_content[:point] + img_html + html_content[point:]
            offset += len(img_html)
            inserted_count += 1
        
        return html_content
    
    async def _replace_placeholder_images(self, images: list, topic: str) -> list:
        """Replace placeholder image URLs with actual image URLs from ImageService."""
        if not images:
            return images
        
        # Import ImageService
        from .image_service import ImageService
        image_service = ImageService()
        
        updated_images = []
        for i, image in enumerate(images):
            if hasattr(image, 'url') and image.url:
                # Check if this is a placeholder URL
                if any(placeholder in image.url for placeholder in ['section_specific_image_', 'item_', '_image']):
                    try:
                        # Generate section-specific title from image alt text or use generic
                        section_title = image.alt if hasattr(image, 'alt') and image.alt else f"섹션 {i+1}"
                        
                        # Get actual images for this section
                        real_images = await image_service.get_section_specific_images(
                            section_title, topic, count=1
                        )
                        
                        if real_images:
                            # Replace placeholder with real image URL
                            real_image = real_images[0]
                            from .models import ImageInfo
                            updated_image = ImageInfo(
                                url=real_image.get('url', image.url),
                                alt=real_image.get('alt', image.alt if hasattr(image, 'alt') else ''),
                                caption=real_image.get('caption', image.caption if hasattr(image, 'caption') else '')
                            )
                            updated_images.append(updated_image)
                        else:
                            # Keep original if image generation fails
                            updated_images.append(image)
                    except Exception as e:
                        print(f"Failed to replace placeholder image {i}: {e}")
                        # Keep original image if replacement fails
                        updated_images.append(image)
                else:
                    # Not a placeholder, keep as is
                    updated_images.append(image)
            else:
                # No URL or invalid image, keep as is
                updated_images.append(image)
        
        return updated_images

    def _add_specific_site_links(self, html_content: str, topic: str) -> str:
        """Add links to specific known sites when they are mentioned in content."""
        import re
        
        # Define specific sites with their official URLs for different categories
        site_mapping = {
            # Travel booking sites
            'booking.com': 'https://www.booking.com',
            'booking': 'https://www.booking.com',
            '부킹닷컴': 'https://www.booking.com',
            'agoda': 'https://www.agoda.com',
            '아고다': 'https://www.agoda.com',
            'expedia': 'https://www.expedia.com',
            '익스피디아': 'https://www.expedia.com',
            'hotels.com': 'https://www.hotels.com',
            'airbnb': 'https://www.airbnb.com',
            '에어비앤비': 'https://www.airbnb.com',
            
            # Airlines - Korean
            '대한항공': 'https://www.koreanair.com',
            '아시아나': 'https://www.flyasiana.com',
            '제주항공': 'https://www.jejuair.net',
            '진에어': 'https://www.jinair.com',
            
            # Tour booking
            'klook': 'https://www.klook.com',
            '클룩': 'https://www.klook.com',
            'viator': 'https://www.viator.com',
            'getyourguide': 'https://www.getyourguide.com',
            
            # Transportation
            'uber': 'https://www.uber.com',
            '우버': 'https://www.uber.com',
            'lyft': 'https://www.lyft.com',
            'grab': 'https://www.grab.com',
            
            # Flight search
            'skyscanner': 'https://www.skyscanner.com',
            '스카이스캐너': 'https://www.skyscanner.com',
            'kayak': 'https://www.kayak.com',
            
            # Grand Canyon specific (for this topic)
            'grand canyon national park': 'https://www.nps.gov/grca',
            '그랜드캐년 국립공원': 'https://www.nps.gov/grca',
            'papillion': 'https://www.papillon.com',
            'maverick helicopters': 'https://www.maverickhelicopter.com',
            
            # Las Vegas specific
            'las vegas': 'https://www.visitlasvegas.com',
            '라스베가스': 'https://www.visitlasvegas.com',
            'mccarran airport': 'https://www.harryreidairport.com',
            'harry reid airport': 'https://www.harryreidairport.com',
            
            # Car rental
            'hertz': 'https://www.hertz.com',
            'avis': 'https://www.avis.com',
            'enterprise': 'https://www.enterprise.com',
            'budget': 'https://www.budget.com',
        }
        
        # Apply site links - add them in parentheses format
        for site_name, url in site_mapping.items():
            # Create pattern to match the site name (case insensitive)
            pattern = re.compile(rf'\b{re.escape(site_name)}\b', re.IGNORECASE)
            
            # Only add link if the site is mentioned but not already linked
            if pattern.search(html_content) and url not in html_content:
                # Replace first occurrence with linked version in parentheses format
                replacement = f'{site_name}({url})'
                html_content = pattern.sub(replacement, html_content, count=1)
        
        print(f"DEBUG: Added specific site links for topic: {topic}")
        return html_content

    def _move_title_links_to_paragraphs(self, html_content: str) -> str:
        """Move links from titles (h1, h2, h3) to the end of following paragraphs."""
        import re
        
        def move_link_to_paragraph(match):
            # Extract the title content and link
            tag_start = match.group(1)  # <h1...>
            title_content = match.group(2)  # title content
            tag_end = match.group(3)  # </h1>
            
            # Check if title contains a link
            link_pattern = r'\((https://[^)]+)\)'
            link_match = re.search(link_pattern, title_content)
            
            if link_match:
                # Remove link from title
                clean_title = re.sub(link_pattern, '', title_content).strip()
                extracted_link = link_match.group(1)
                
                # Reconstruct clean title
                clean_header = f"{tag_start}{clean_title}{tag_end}"
                
                # Find the next paragraph after this header
                remaining_content = html_content[match.end():]
                para_pattern = r'(<p[^>]*>.*?</p>)'
                para_match = re.search(para_pattern, remaining_content, re.DOTALL)
                
                if para_match:
                    # Add link to end of first paragraph
                    original_para = para_match.group(1)
                    # Insert link before closing </p> tag
                    modified_para = re.sub(r'</p>$', f' ({extracted_link})</p>', original_para)
                    
                    # Replace in content
                    before_header = html_content[:match.start()]
                    before_para = html_content[match.end():match.end() + para_match.start()]
                    after_para = html_content[match.end() + para_match.end():]
                    
                    return before_header + clean_header + before_para + modified_para + after_para
                else:
                    # No paragraph found, keep clean header
                    return html_content[:match.start()] + clean_header + html_content[match.end():]
            else:
                # No link in title, return as is
                return match.group(0)
        
        # Pattern to match headers with potential links
        header_pattern = r'(<h[1-3][^>]*>)(.*?)(</h[1-3]>)'
        
        # Check if any headers contain links
        if re.search(r'<h[1-3][^>]*>.*?\(https://[^)]+\).*?</h[1-3]>', html_content):
            # Process each header
            result = html_content
            for match in re.finditer(header_pattern, html_content, re.DOTALL):
                result = move_link_to_paragraph(match)
                if result != html_content:
                    print(f"DEBUG: Moved link from title to paragraph")
                    break  # Process one at a time to avoid overlap issues
            return result
        
        return html_content

    def _final_google_link_cleanup(self, html_content: str) -> str:
        """Final pass to remove any remaining Google search links and ALL problematic links."""
        import re
        
        # ULTRA AGGRESSIVE LINK REMOVAL - Remove ALL links completely
        
        # Step 1: Remove ALL <a> tags with any content - more thorough patterns
        html_content = re.sub(r'<a[^>]*>.*?</a>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
        html_content = re.sub(r'<a\s[^>]*href[^>]*>.*?</a>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
        
        # Step 2: Remove any remaining href attributes anywhere
        html_content = re.sub(r'href\s*=\s*["\'][^"\']*["\']', '', html_content, flags=re.IGNORECASE)
        
        # Step 3: Remove link-related text patterns that might remain
        html_content = re.sub(r'자세히\s*보기', '', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'바로\s*가기', '', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'더\s*보기', '', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'상세\s*보기', '', html_content, flags=re.IGNORECASE)
        
        # Step 4: Remove empty elements left from link removal
        html_content = re.sub(r'<div[^>]*>\s*</div>', '', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'<span[^>]*>\s*</span>', '', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'<p[^>]*>\s*</p>', '', html_content, flags=re.IGNORECASE)

        # Step 5: Remove any standalone URLs
        html_content = re.sub(r'https?://[^\s<>"]*google[^\s<>"]*', '', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'https?://[^\s<>"]*search[^\s<>"]*', '', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'https?://[^\s<>"]*\?q=[^\s<>"]*', '', html_content, flags=re.IGNORECASE)

        # Step 6: Clean up multiple spaces and line breaks left from removals
        html_content = re.sub(r'\s+', ' ', html_content)
        html_content = re.sub(r'>\s+<', '><', html_content)
        html_content = re.sub(r'<([^>]+)>\s*<(/[^>]+)>', r'<\1><\2>', html_content)
        
        print(f"DEBUG: Removed ALL links completely, remaining content length: {len(html_content)}")
        
        return html_content
    
    async def _add_news_specific_links(self, html_content: str, topic: str, provider: AIProvider, config: AIClientConfig) -> str:
        """Add news-specific links for hot topics and current issues."""
        try:
            # Check if this is a news/current affairs topic - expanded keywords
            news_keywords = ['트럼프', 'trump', '관세', 'tariff', '핫', '이슈', 'top', '순위', '뉴스', '사건', '정치', '경제', '사회', '최신', '화제', '트렌드', '현안', '대통령', '정부', '정책', '행정부', '통상', '무역']
            topic_lower = topic.lower()
            
            is_news_topic = any(keyword in topic_lower for keyword in news_keywords)
            print(f"DEBUG: Topic '{topic}' is news topic: {is_news_topic}")
            
            if not is_news_topic:
                return html_content  # Not a news topic, return as is
            
            # Create AI prompt for finding news links
            news_prompt = f"""주제: "{topic}"

위 주제와 관련된 실제 뉴스 기사나 공식 발표 자료의 링크를 찾아주세요.

⚠️ **절대 금지사항**: 
- Google 검색 링크 (google.com/search) 절대 생성 금지
- 검색 엔진 링크 일체 금지
- URL 인코딩된 링크 금지

✅ **허용되는 링크만**:
1. **정부기관**: .gov.kr, .go.kr 도메인
2. **언론사**: KBS, MBC, SBS, 연합뉴스, 조선일보, 중앙일보 등
3. **공식기관**: 청와대, 국정원, 각 부처 공식 사이트

**트럼프 관세 주제 예시**:
- 기획재정부: https://www.mosf.go.kr/
- 산업통상자원부: https://www.motie.go.kr/ 
- 연합뉴스: https://www.yna.co.kr/
- KBS 뉴스: https://news.kbs.co.kr/
- 한국무역협회: https://www.kita.net/

응답 형식 (JSON):
{{"news_links": [{{"title": "관련 기관/뉴스명", "url": "실제URL", "source": "기관명"}}]}}

**중요**: 반드시 위 허용 도메인만 사용하고, 구글 링크나 검색 링크는 절대 생성하지 마세요."""

            # Generate news links using AI
            ai_request = AIRequest(
                messages=[
                    AIMessage(role="system", content="당신은 뉴스 및 공식 정보 전문가입니다. 주어진 주제와 관련된 실제 뉴스 기사나 공식 웹사이트를 찾아줍니다."),
                    AIMessage(role="user", content=news_prompt)
                ],
                max_tokens=300,
                temperature=0.2
            )

            async with AIClientFactory.create_client(provider, config) as client:
                response = await client.generate(ai_request)
            
            # Parse AI response for news links
            news_links = self._parse_news_links_response(response.content)
            
            if news_links:
                # Replace generic links with specific news links
                modified_content = self._replace_generic_with_news_links(html_content, news_links, topic)
                return modified_content
            
        except Exception as e:
            print(f"Error generating news-specific links: {e}")
        
        return html_content
    
    def _parse_news_links_response(self, ai_response: str) -> list:
        """Parse AI response to extract news links."""
        try:
            # Try to extract JSON from the response
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = ai_response[start_idx:end_idx]
                data = json.loads(json_str)
                return data.get("news_links", [])
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Failed to parse news links response: {e}")
        
        return []
    
    def _replace_generic_with_news_links(self, html_content: str, news_links: list, topic: str) -> str:
        """Add specific news links to content sections."""
        if not news_links:
            return html_content
        
        import re
        
        # Since all links were removed by _final_google_link_cleanup, 
        # we need to add useful news links at the end of major sections
        
        # Find h2 and h3 headings to add relevant links after them
        section_pattern = r'(<h[23][^>]*>.*?</h[23]>)'
        sections = re.findall(section_pattern, html_content, re.IGNORECASE)
        
        print(f"DEBUG: Found {len(sections)} sections, have {len(news_links)} news links")
        
        # Add news links after the first few major sections
        sections_with_links = 0
        max_sections_with_links = min(3, len(news_links))  # Max 3 sections get links
        
        def add_news_link_after_section(match):
            nonlocal sections_with_links
            
            if sections_with_links < max_sections_with_links and news_links:
                news_link = news_links[sections_with_links]
                url = news_link.get('url', '#')
                title = news_link.get('title', '관련 정보')
                source = news_link.get('source', '')
                
                # Verify URL is not prohibited
                if any(prohibited in url.lower() for prohibited in ['google.com', 'search', '%ec%', '%ed%', '%ea%']):
                    sections_with_links += 1
                    return match.group(0)  # Skip this prohibited link
                
                # Create clean display text
                display_text = title if len(title) < 40 else f"{title[:37]}..."
                if source and len(source) < 15:
                    display_text += f" ({source})"
                
                news_link_html = f'''
<div style="text-align: center; margin: 30px 0; padding: 25px; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.12);">
    <p style="color: #2c3e50; margin: 0 0 15px 0; font-weight: 700; font-size: 16px; text-transform: uppercase; letter-spacing: 1px;">📰 관련 정보</p>
    <a href="{url}" target="_blank" 
       style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%); 
              color: white; text-decoration: none; font-weight: 700; font-size: 15px; 
              padding: 15px 30px; border-radius: 50px; box-shadow: 0 8px 32px rgba(0,0,0,0.2); 
              transform: translateY(0); transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); 
              text-transform: uppercase; letter-spacing: 1px; position: relative; overflow: hidden;">
        <span style="position: relative; z-index: 1;">{display_text}</span>
        <div style="position: absolute; top: 0; left: -100%; width: 100%; height: 100%; 
                    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent); 
                    transition: all 0.5s;"></div>
    </a>
</div>'''
                sections_with_links += 1
                return match.group(0) + news_link_html
            
            return match.group(0)
        
        # Add news links after sections
        modified_content = re.sub(section_pattern, add_news_link_after_section, html_content, flags=re.IGNORECASE)
        
        print(f"DEBUG: Added {sections_with_links} news links to content")
        return modified_content
    
    async def _add_specific_place_links(self, html_content: str, topic: str, provider: AIProvider, config: AIClientConfig) -> str:
        """Add specific restaurant/place links based on content analysis using AI."""
        import re
        
        if not html_content:
            return html_content
        
        try:
            # Create AI client
            client = AIClientFactory.create_client(provider, config)
            
            # Extract sections that might need specific place links
            section_pattern = r'<h[23][^>]*>([^<]*미식[^<]*|[^<]*맛집[^<]*|[^<]*레스토랑[^<]*|[^<]*관광[^<]*|[^<]*명소[^<]*)</h[23]>'
            sections_needing_links = re.findall(section_pattern, html_content, flags=re.IGNORECASE)
            
            if not sections_needing_links:
                return html_content
            
            print(f"DEBUG: Found sections needing specific links: {sections_needing_links}")
            
            # Create prompt for AI to find specific places/restaurants
            places_prompt = f"""주제: "{topic}"

다음 섹션들에서 언급될 수 있는 구체적인 장소/맛집의 공식 웹사이트를 찾아주세요:

섹션들: {', '.join(sections_needing_links)}

요구사항:
1. **실제 존재하는 공식 사이트만** (레스토랑 자체 웹사이트, 관광명소 공식 사이트)
2. **구체적인 장소명과 URL 제공**
3. **검색엔진 링크 절대 금지** (google.com, search 등 절대 안됨)

예시 형식:
- 샌프란시스코 미식이면: Tartine Bakery (https://www.tartinebakery.com), Swan Oyster Depot (공식사이트), Ghirardelli Square (https://www.ghirardellisq.com)
- 관광명소면: Golden Gate Bridge (https://www.goldengatebridge.org), Alcatraz Island (https://www.alcatrazcruises.com)

응답 형식 (JSON):
{{
  "places": [
    {{
      "name": "장소명",
      "url": "https://공식사이트.com",
      "category": "restaurant" // or "attraction"
    }}
  ]
}}"""

            ai_request = AIRequest(
                messages=[
                    AIMessage(role="system", content="당신은 여행 정보 전문가입니다. 특정 지역의 유명한 맛집과 관광명소의 공식 웹사이트를 정확히 찾아 제공합니다."),
                    AIMessage(role="user", content=places_prompt)
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            # Generate specific place links using AI
            async with client:
                response = await client.generate(ai_request)
            
            # Parse AI response
            places_data = self._parse_places_response(response.content)
            print(f"DEBUG: AI suggested {len(places_data)} specific places")
            
            if places_data:
                # Apply specific place links to content
                enhanced_content = self._apply_specific_place_links(html_content, places_data)
                return enhanced_content
            
        except Exception as e:
            print(f"DEBUG: Specific place link generation failed: {e}")
        
        return html_content
    
    def _parse_places_response(self, ai_response: str) -> list:
        """Parse AI response to extract specific places data."""
        import json
        try:
            # Try to extract JSON from the response
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = ai_response[start_idx:end_idx]
                data = json.loads(json_str)
                return data.get("places", [])
        except (json.JSONDecodeError, ValueError) as e:
            print(f"DEBUG: Failed to parse places response: {e}")
        
        return []
    
    def _apply_specific_place_links(self, html_content: str, places_data: list) -> str:
        """Apply specific place links to content."""
        import re
        
        enhanced_content = html_content
        
        for place_info in places_data:
            place_name = place_info.get("name", "")
            place_url = place_info.get("url", "")
            
            if not place_name or not place_url:
                continue
            
            # Skip prohibited URLs
            if any(pattern in place_url.lower() for pattern in ['google.com', 'search', 'q=']):
                print(f"DEBUG: Skipping prohibited URL for {place_name}: {place_url}")
                continue
            
            # Find mentions of this place name in the content and add links
            # Look for the place name in text (not already in links)
            place_pattern = rf'\b{re.escape(place_name)}\b(?![^<]*</a>)'
            
            def add_link(match):
                return f'<a href="{place_url}" target="_blank" style="color: #3498db; text-decoration: none; font-weight: 500;">{match.group(0)}</a>'
            
            # Replace first occurrence only to avoid over-linking
            enhanced_content = re.sub(place_pattern, add_link, enhanced_content, count=1, flags=re.IGNORECASE)
        
        return enhanced_content
    
    async def _add_ai_generated_links(self, html_content: str, topic: str, provider: AIProvider, config: AIClientConfig) -> str:
        """Use AI to generate relevant links for each section heading."""
        import re
        
        if not html_content:
            return html_content
        
        print("DEBUG: Starting AI-generated links process")
        
        # Extract all H2 and H3 headings
        heading_pattern = r'<h[23][^>]*>(.*?)</h[23]>'
        headings = re.findall(heading_pattern, html_content, flags=re.IGNORECASE | re.DOTALL)
        
        if not headings:
            print("DEBUG: No headings found")
            return html_content
        
        # Clean headings (remove HTML tags)
        clean_headings = []
        for heading in headings:
            clean_heading = re.sub(r'<[^>]+>', '', heading).strip()
            clean_headings.append(clean_heading)
        
        print(f"DEBUG: Found {len(clean_headings)} headings: {clean_headings}")
        
        # Create AI client for link generation
        client = AIClientFactory.create_client(provider, config)
        
        # Create prompt for AI to find relevant links
        link_prompt = self._create_link_generation_prompt(topic, clean_headings)
        
        ai_request = AIRequest(
            messages=[
                AIMessage(role="system", content="당신은 웹 검색 전문가입니다. 주어진 주제와 섹션 제목에 대해 가장 적절하고 신뢰할 수 있는 웹사이트 링크를 찾아 제공합니다."),
                AIMessage(role="user", content=link_prompt)
            ],
            max_tokens=1000,
            temperature=0.3  # Lower temperature for more consistent results
        )
        
        try:
            # Generate links using AI
            async with client:
                response = await client.generate(ai_request)
            
            # Parse AI response to get links
            links_data = self._parse_links_response(response.content)
            print(f"DEBUG: AI generated {len(links_data)} links")
            
            # Filter out prohibited links
            filtered_links = self._filter_prohibited_links(links_data)
            print(f"DEBUG: After filtering: {len(filtered_links)} links")
            
            # Apply links to HTML content
            enhanced_html = self._apply_ai_links_to_html(html_content, filtered_links)
            return enhanced_html
            
        except Exception as e:
            print(f"DEBUG: AI link generation failed: {e}")
            # Fallback to original method if AI fails
            return self._add_section_links(html_content, topic)
    
    def _calculate_word_count(self, html_content: str) -> int:
        """Calculate word count from HTML content, excluding HTML tags."""
        import re
        # Remove HTML tags
        text_only = re.sub(r'<[^>]+>', ' ', html_content)
        # Remove extra whitespace and count words
        words = text_only.split()
        return len(words)
    
    def _balance_word_counts(self, contents: List[str], target_total: int, num_options: int) -> List[str]:
        """Balance word counts across multiple content options."""
        if num_options <= 1:
            return contents
            
        # Calculate target word count per option
        base_count_per_option = target_total // num_options
        remainder = target_total % num_options
        
        # Create target counts for each option
        target_counts = []
        for i in range(num_options):
            target = base_count_per_option
            if i < remainder:  # Distribute remainder across first few options
                target += 1
            target_counts.append(target)
        
        print(f"DEBUG: Balancing {num_options} options with target counts: {target_counts}")
        
        balanced_contents = []
        for i, content in enumerate(contents):
            if i >= len(target_counts):
                break
                
            current_count = self._calculate_word_count(content)
            target_count = target_counts[i]
            
            print(f"DEBUG: Option {i+1}: Current={current_count}, Target={target_count}")
            
            # Adjust content length if needed
            if current_count < target_count * 0.9:  # If significantly under target
                adjusted_content = self._expand_content(content, target_count)
            elif current_count > target_count * 1.1:  # If significantly over target
                adjusted_content = self._trim_content(content, target_count)
            else:
                adjusted_content = content
            
            balanced_contents.append(adjusted_content)
        
        return balanced_contents
    
    def _expand_content(self, content: str, target_count: int) -> str:
        """Expand content to reach target word count."""
        # For now, return original content
        # This could be enhanced to add more detailed sections
        return content
    
    def _trim_content(self, content: str, target_count: int) -> str:
        """Trim content to reach target word count."""
        import re
        
        # Split content into sentences while preserving HTML structure
        sentences = re.split(r'([.!?](?:\s*</[^>]*>)*\s*)', content)
        
        current_count = self._calculate_word_count(content)
        if current_count <= target_count:
            return content
        
        # Remove sentences from the end until we reach target count
        while len(sentences) > 2 and self._calculate_word_count(''.join(sentences)) > target_count * 1.1:
            # Remove from end, keeping pairs (sentence + punctuation)
            if len(sentences) >= 2:
                sentences.pop()
                sentences.pop()
        
        return ''.join(sentences)
    
    def _create_link_generation_prompt(self, topic: str, headings: list) -> str:
        """Create prompt for AI to generate relevant links."""
        headings_text = "\n".join([f"- {heading}" for heading in headings])
        
        return f"""주제: "{topic}"

다음 섹션 제목들을 분석하여 **실제 존재하는 공식 사이트 URL**을 제공해주세요:

{headings_text}

🎯 **링크 생성 기준**:
1. **실제로 존재하는 공식 사이트만** (예: 대한항공 → https://www.koreanair.com/kr/ko/booking/skypass)
2. **5-7개 섹션에 상세한 링크 제공** (가능한 많은 유용한 섹션에 링크)
3. **섹션 내용과 직접 관련된 구체적인 서비스 페이지** 링크
4. **실무에 도움되는 실제 사용 가능한 사이트만**

🚫 **절대 금지 사항 (매우 중요)**:
- ❌ google.com 포함된 모든 URL 절대 금지
- ❌ search.naver.com, bing.com, yahoo.com 등 검색엔진 절대 금지  
- ❌ URL에 "search", "q=" 파라미터 포함 절대 금지
- ❌ 결론/요약/마무리 섹션에는 링크 제공하지 마세요
- ❌ 존재하지 않는 URL 생성 절대 금지
- ❌ 검색 결과 페이지로 이동하는 모든 링크 금지

✅ **반드시 준수사항**:
- 오직 공식 사이트 홈페이지만 허용 (예: vancouver.ca, translink.ca)
- 정부기관, 관광청, 교통공사 등 공식 기관만
- 실제 서비스를 제공하는 공식 웹사이트만

📋 **섹션별 맞춤 링크 예시**:
- **환전/통화**: 한국은행 환율정보, 시중은행 환전 서비스
- **교통편**: 공항철도, 공항버스, 택시 예약 사이트  
- **항공**: 항공사 공식 홈페이지, 체크인 서비스
- **숙박**: 호텔 공식 사이트, 예약 플랫폼
- **보험**: 여행자보험 공식 사이트
- **비자/여권**: 외교부, 영사관 공식 사이트
- **쇼핑**: 면세점 공식 사이트
- **통신**: 해외 로밍 서비스, 유심 대여 사이트

**주요 공식 사이트 예시**:
- 대한항공 마일리지: https://www.koreanair.com/kr/ko/booking/skypass
- 아시아나항공: https://flyasiana.com/kr/ko/loyalty/asiana_club
- 제주관광공사: https://www.visitjeju.net
- 한국관광공사: https://korean.visitkorea.or.kr
- KB국민은행: https://www.kbstar.com
- 삼성전자: https://www.samsung.com/kr
- LG전자: https://www.lge.co.kr
- 현대자동차: https://www.hyundai.com/kr/ko
- 네이버: https://www.naver.com
- 카카오: https://www.kakaocorp.com
- 여행자보험: https://www.samsungfire.com/product/travel
- 신라면세점: https://www.shilladfs.com
- 대한항공: https://www.koreanair.com/kr/ko
- 공항철도 A'REX: https://www.arex.or.kr
- 인천국제공항: https://www.airport.kr
- 한국은행 환율정보: https://www.bok.or.kr/portal/singl/baseRate/
- 외교부 영사서비스: https://www.0404.go.kr
- 하나은행 환전: https://www.hanabank.com/exchange
- 우리은행 환전: https://spot.wooribank.com/pot/Dream?withyou=FXCNT0010
- KT 로밍: https://roaming.kt.com
- SK텔레콤 로밍: https://www.tworld.co.kr/roaming
- 롯데면세점: https://www.lottedfs.com



응답 형식 (JSON):
{{
  "links": [
    {{
      "heading": "정확한 섹션 제목",
      "url": "https://실제존재하는공식사이트.com/구체적페이지", 
      "description": "공식 사이트 설명",
      "relevance_score": 9
    }}
  ]
}}

**중요**: 존재하지 않는 URL은 절대 제공하지 마세요. 실제 공식 사이트만 사용하세요."""
    
    def _filter_prohibited_links(self, links_data: list) -> list:
        """Filter out prohibited links like Google search, invalid URLs."""
        filtered_links = []
        
        prohibited_patterns = [
            'google.com',  # Block all google.com URLs
            'www.google',  # Block google variants
            'search.google',  # Block google search
            'search.naver.com',
            'bing.com',
            'yahoo.com',
            'search.',  # Any search subdomain
            '/search?',  # Any search query parameter
            '/search/',  # Any search path
            'q=',  # Query parameter
            '%EC%',  # URL encoded Korean characters (often in search URLs)
            '%ED%',  # More Korean URL encoding
            '%EA%',  # More Korean URL encoding
            'query=',
            'searchterm=',
            'keyword=',
            'google.com/search',  # Explicit Google search blocking
            'https://google',  # Any google URL
            'http://google',  # Any google URL
        ]
        
        conclusion_keywords = [
            '결론', '마무리', '요약', '정리', '끝으로', '마지막',
            '행동유도', '행동', '유도', 'conclusion', 'summary'
        ]
        
        for link_info in links_data:
            url = link_info.get("url", "").lower()
            heading = link_info.get("heading", "").lower()
            
            # Skip prohibited URLs
            is_prohibited = any(pattern in url for pattern in prohibited_patterns)
            if is_prohibited:
                print(f"DEBUG: Filtering out prohibited URL: {url}")
                continue
            
            # Skip conclusion/summary sections
            is_conclusion = any(keyword in heading for keyword in conclusion_keywords)
            if is_conclusion:
                print(f"DEBUG: Filtering out conclusion section: {heading}")
                continue
            
            # Only allow valid URLs
            if url.startswith(('http://', 'https://')):
                filtered_links.append(link_info)
            else:
                print(f"DEBUG: Filtering out invalid URL: {url}")
        
        return filtered_links
    
    def _parse_links_response(self, ai_response: str) -> list:
        """Parse AI response to extract links data."""
        import json
        try:
            # Try to extract JSON from the response
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = ai_response[start_idx:end_idx]
                data = json.loads(json_str)
                return data.get("links", [])
        except (json.JSONDecodeError, ValueError) as e:
            print(f"DEBUG: Failed to parse AI links response: {e}")
        
        return []
    
    def _apply_ai_links_to_html(self, html_content: str, links_data: list) -> str:
        """Apply AI-generated links to HTML content."""
        import re
        
        if not links_data:
            return html_content
        
        # Create a mapping of headings to URLs
        heading_to_url = {}
        for link_info in links_data:
            heading = link_info.get("heading", "").strip()
            url = link_info.get("url", "")
            if heading and url:
                heading_to_url[heading.lower()] = url
        
        print(f"DEBUG: Created heading-to-URL mapping: {heading_to_url}")
        
        # Premium centered link template with sophisticated styling
        link_template = '''<div style="text-align: center; margin: 25px 0;">
            <a href="{}" target="_blank" 
               style="display: inline-block; 
                      background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%); 
                      color: white; 
                      text-decoration: none; 
                      font-weight: 700; 
                      font-size: 15px;
                      padding: 15px 30px; 
                      border-radius: 50px;
                      box-shadow: 0 8px 32px rgba(0,0,0,0.2);
                      transform: translateY(0);
                      transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                      text-transform: uppercase;
                      letter-spacing: 1px;
                      position: relative;
                      overflow: hidden;">
                <span style="position: relative; z-index: 1;">{}</span>
                <div style="position: absolute; top: 0; left: -100%; width: 100%; height: 100%; 
                            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent); 
                            transition: all 0.5s;"></div>
            </a>
        </div>'''
        
        # Find H2 and H3 headings and add selective AI-generated links
        processed_headings = set()  # Track which headings got links
        
        def add_ai_link_after_heading(match):
            full_heading = match.group(0)
            # Extract heading text (remove HTML tags)
            heading_text = re.sub(r'<[^>]+>', '', full_heading).strip()
            
            # Skip unnecessary sections (conclusion, summary, tips, etc.)
            skip_keywords = ['요약', '결론', '마무리', '팁', '정리', '마지막', '끝으로', '종합', '총정리']
            if any(keyword in heading_text.lower() for keyword in skip_keywords):
                return full_heading
            
            # Allow more links (limit to 7-8 per content for better coverage)
            if len(processed_headings) >= 8:
                return full_heading
            
            # Find matching URL from AI response with improved matching
            relevant_url = None
            matched_heading = None
            heading_lower = heading_text.lower()
            
            # Direct match first
            for stored_heading, url in heading_to_url.items():
                if stored_heading in heading_lower or heading_lower in stored_heading:
                    relevant_url = url
                    matched_heading = stored_heading
                    break
            
            # If no direct match, try keyword-based matching
            if not relevant_url:
                # Extract key words from heading for better matching
                import re
                heading_words = re.findall(r'[가-힣a-zA-Z]{2,}', heading_lower)
                for stored_heading, url in heading_to_url.items():
                    stored_words = re.findall(r'[가-힣a-zA-Z]{2,}', stored_heading)
                    # Check if any significant word matches
                    if any(word in stored_words for word in heading_words if len(word) >= 2):
                        relevant_url = url
                        matched_heading = stored_heading
                        break
            
            if not relevant_url:
                # No relevant link found - return heading without link
                return full_heading
            
            # Mark this heading as processed
            processed_headings.add(matched_heading)
            
            # Create clean display text for link
            display_text = heading_text
            # Remove section numbers and clean up
            display_text = re.sub(r'^\d+\.\s*', '', display_text)  # Remove "1. " prefix
            
            # Create simple section name format (no "바로가기" text)
            if len(display_text) > 15:
                display_text = display_text[:12] + "..."
            link_text = display_text  # Remove "바로가기" completely
            
            # Create simple link button
            link_button = link_template.format(relevant_url, link_text)
            
            return full_heading + '\n' + link_button
        
        # Pattern to match H2 and H3 headings
        heading_pattern = r'<h[23][^>]*>.*?</h[23]>'
        
        # Add AI-generated links after each heading
        enhanced_html = re.sub(heading_pattern, add_ai_link_after_heading, html_content, flags=re.IGNORECASE | re.DOTALL)
        
        return enhanced_html
    
    def _add_section_links(self, html_content: str, topic: str = "") -> str:
        """Fallback: Return content without adding any links if AI link generation fails."""
        print("DEBUG: AI link generation failed, returning content without additional links")
        return html_content