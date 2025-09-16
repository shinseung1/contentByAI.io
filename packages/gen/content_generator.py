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
    """Safe text for printing that replaces problematic Unicode with ? for debugging."""
    if not isinstance(text, str):
        return text
    emoji_pattern = re.compile("["
                              u"\U0001F600-\U0001F64F"  # emoticons
                              u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                              u"\U0001F680-\U0001F6FF"  # transport & map symbols
                              u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                              u"\U00002600-\U000027B0"  # includes airplane ✈ symbol
                              u"\U000024C2-\U0001F251"
                              "]+", flags=re.UNICODE)
    return emoji_pattern.sub('?', text)

def remove_emojis(text):
    """Remove emoji characters from text to avoid encoding issues on Windows cp949."""
    if not isinstance(text, str):
        return text
    emoji_pattern = re.compile("["
                              u"\U0001F600-\U0001F64F"  # emoticons
                              u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                              u"\U0001F680-\U0001F6FF"  # transport & map symbols
                              u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                              u"\U00002600-\U000027B0"  # includes airplane ✈ symbol
                              u"\U000024C2-\U0001F251"
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
    
    def create_job_id(self) -> str:
        """Create a unique job ID."""
        return str(uuid.uuid4())
    
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
            print(f"DEBUG: db_job.tone = {str(db_job.tone)}")
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
            print(f"DEBUG: response.tone = {str(response.tone)}")
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
        """Create system prompt for AI."""
        language_instruction = ""
        if request.target_language == "ko":
            language_instruction = "모든 응답은 한국어로 작성해주세요."
        elif request.target_language == "en":
            language_instruction = "Please respond in English."
        
        # Load template structure
        template_structure = self._load_template_structure()
        
        # Detect comparison topics
        is_comparison_topic = any(keyword in request.topic.lower() for keyword in ['vs', 'versus', '대', '비교', '차이'])
        
        # Detect TOP/ranking topics and extract number
        import re
        topic_lower = request.topic.lower()
        ranking_number = None
        is_ranking_topic = False
        
        # Check for TOP patterns
        top_patterns = [
            r'top\s*(\d+)', r'톱\s*(\d+)', r'베스트\s*(\d+)', r'best\s*(\d+)', 
            r'추천\s*(\d+)', r'(\d+)가지', r'(\d+)개', r'(\d+)종류', 
            r'(\d+)위', r'(\d+)순위'
        ]
        
        for pattern in top_patterns:
            match = re.search(pattern, topic_lower)
            if match:
                ranking_number = int(match.group(1))
                is_ranking_topic = True
                break
        
        # Also check for written numbers in Korean
        korean_numbers = {
            '세': 3, '삼': 3, '네': 4, '사': 4, '다섯': 5, '오': 5,
            '여섯': 6, '육': 6, '일곱': 7, '칠': 7, '여덟': 8, '팔': 8,
            '아홉': 9, '구': 9, '열': 10
        }
        
        for korean_num, num_val in korean_numbers.items():
            if korean_num in topic_lower and ('가지' in topic_lower or '개' in topic_lower):
                ranking_number = num_val
                is_ranking_topic = True
                break
        
        comparison_instruction = ""
        top3_instruction = ""
        
        # Detect choice/selection topics as well
        choice_patterns = [
            r'(\d+)\s*가지', r'(\d+)\s*개', r'(\d+)\s*종류', r'(\d+)\s*유형', 
            r'(\d+)\s*방법', r'(\d+)\s*선택', r'(\d+)\s*옵션'
        ]
        
        choice_number = None
        is_choice_topic = False
        
        for pattern in choice_patterns:
            match = re.search(pattern, topic_lower)
            if match:
                choice_number = int(match.group(1))
                is_choice_topic = True
                break
        
        # Use either ranking_number or choice_number
        final_number = ranking_number if is_ranking_topic else choice_number
        is_multi_item_topic = is_ranking_topic or is_choice_topic

        # TOP/Ranking/Choice topic instructions
        if is_multi_item_topic and final_number:
            # Generate emoji list for rankings
            ranking_emojis = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
            section_examples = []
            
            for i in range(final_number):
                rank_num = i + 1
                emoji = ranking_emojis[i] if i < len(ranking_emojis) else f"{rank_num}️⃣"
                if is_ranking_topic:
                    section_examples.append(f"  * ## {emoji} {rank_num}위 (또는 TOP{rank_num}): [항목명] - 매우 상세한 설명 (4-5문단)")
                else:
                    section_examples.append(f"  * ## {emoji} 선택 {rank_num}: [항목명] - 매우 상세한 설명 (4-5문단)")
            
            section_structure = '\n'.join(section_examples)
            
            topic_type = "TOP" if is_ranking_topic else "선택"
            
            top3_instruction = f"""
**🏆 {topic_type}{final_number}/다중항목 주제 특별 요구사항 (절대 필수):**
주제 "{request.topic}"는 {final_number}개 항목을 다루는 주제입니다. 반드시 다음을 지켜주세요:

**📊 구조 요구사항 (매우 중요):**
- **정확히 {final_number}개의 항목**을 다뤄야 합니다 (명시된 숫자와 정확히 일치)
- **각 항목별로 독립된 큰 섹션** 구성: 
{section_structure}
- **각 항목마다 최소 400-600단어** 할당하여 매우 상세하게 작성
- **전체 {final_number}개 항목이 균등한 분량**으로 작성 (어느 하나도 빠뜨리거나 짧게 쓰지 말 것)
- **모든 항목에 동일한 구조** 적용: 개요 → 특징 → 장단점 → 사용법/방법 → 추천상황

**📋 필수 테이블 (반드시 포함):**
- **종합 비교표**: {final_number}개 항목의 특징, 장단점, 점수를 한눈에 비교
- **선택 가이드표**: 상황별/목적별로 어떤 항목을 선택해야 하는지 상세 가이드  
- **케이스별 추천표**: 다양한 상황에서의 추천 항목과 이유
- **항목별 상세 정보표**: 각 항목의 핵심 정보를 정리한 표

**🚨 테이블 완성도 필수 사항 🚨:**
- 모든 테이블은 반드시 완전한 HTML 구조로 생성 (opening과 closing 태그 모두 필수)
- 각 테이블은 최소 3-5개의 완전한 행(row)을 포함해야 함
- 테이블이 중간에 잘리거나 불완전하게 끝나면 안됨
- `<table>` 태그로 시작했으면 반드시 `</table>` 태그로 완료
- 모든 `<tr>` 태그는 반드시 `</tr>`로 완료
- 모든 `<td>`와 `<th>` 태그는 반드시 완전히 닫혀야 함

**✅ 각 항목별 필수 내용:**
- **선정 이유** (왜 이 항목인지)
- **핵심 특징 및 장점** (구체적 예시 포함)
- **단점 및 한계사항** (솔직한 평가)
- **구체적 사용 사례/활용법** (실제 예시)
- **추천 대상 및 상황** (언제, 누구에게)
- **실제 후기/평가 정보** (가능한 경우)

**⚠️ 절대 준수 사항:**
- {final_number}개 항목 **모두 반드시 포함** (하나도 빠뜨리면 안됨)
- 모든 항목이 **동일한 깊이와 상세함**으로 작성 (균등 분배)
- 각 섹션은 **큰 덩어리로 구성** (작은 카드들로 쪼개지 말고 항목1 전체, 항목2 전체, 항목3 전체로)
- **케이스별 추천 섹션** 반드시 포함 (어떤 상황에서 어떤 선택을 해야 하는지)

"""
        
        if is_comparison_topic:
            comparison_instruction = f"""
**🔥 비교 주제 특별 요구사항 (절대 필수):**
주제 "{request.topic}"는 비교 주제입니다.
- 반드시 양쪽 모두 동등하게 다뤄야 합니다 (예: 동부힙합 + 서부힙합 모두)
- 각 측면별로 최소 3-4개 섹션씩 할당
- 직접 비교하는 상세 비교표 최소 3개 필수 (매우 중요!)
- 장단점, 특징, 차이점을 명확히 대비
- 어느 한쪽에 편향되지 않고 균형잡힌 시각으로 작성
- 결론에서 상황별 선택 가이드 제공

**비교표 필수 항목 (반드시 HTML <table> 태그 사용):**
1. 기본 특징 비교표 - <table><thead><tr><th>구분</th><th>A측면</th><th>B측면</th></tr></thead><tbody>...
2. 장단점 비교표 - <table><thead><tr><th>항목</th><th>A측면 장점</th><th>A측면 단점</th><th>B측면 장점</th><th>B측면 단점</th></tr></thead>...
3. 추천 상황별 비교표 - <table><thead><tr><th>상황</th><th>A측면 추천도</th><th>B측면 추천도</th><th>이유</th></tr></thead>...

**테이블 스타일링 필수 (더 아름다운 디자인):**
모든 <table>에 style="border-collapse: collapse; width: 100%; margin: 25px 0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);" 적용
<thead> <tr>에 style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;" 적용
모든 <th>에 style="padding: 15px 20px; text-align: left; font-weight: 600; border: none;" 적용
모든 <td>에 style="padding: 12px 20px; border-bottom: 1px solid #eee; border-left: none; border-right: none;" 적용
<tbody> <tr>에 style="transition: background-color 0.3s ease;" 적용
<tbody> <tr>:nth-child(even)에 style="background-color: #f8f9ff;" 적용
"""
        
        image_instructions = ""
        if request.include_images:
            # Generate image instructions based on the number of items
            image_count = final_number if is_multi_item_topic and final_number else 5
            image_list = []
            
            for i in range(image_count):
                image_num = i + 1
                if is_multi_item_topic:
                    image_list.append(f"""        {{
            "url": "item_{image_num}_image",
            "alt": "{image_num}번째 선택/항목과 관련된 구체적인 이미지 설명",
            "caption": "{image_num}번째 항목 관련 이미지"
        }}""")
                else:
                    image_list.append(f"""        {{
            "url": "section_specific_image_{image_num}",
            "alt": "{image_num}번째 주요 섹션과 관련된 구체적인 이미지 설명",
            "caption": "{image_num}번째 섹션 제목에 맞는 이미지 캡션"
        }}""")
            
            images_json = ',\n'.join(image_list)
            image_instructions = f"""    "images": [
{images_json}
    ],"""
        else:
            image_instructions = """    "images": [],"""
        
        template_instruction = ""
        if template_structure:
            template_instruction = f"""
**템플릿 구조 (반드시 적용):**
{template_structure}

위 구조를 참고하여 동일한 패턴으로 작성하세요.
"""
        
        return f"""당신은 한국어 여행/마일리지 전문 에디터입니다.

{comparison_instruction}

{top3_instruction}

{template_instruction}

**🎯 제목 생성 규칙 (매우 중요):**
- 창의적이고 감각적인 제목 필수: "집에서도 맛집 김치찌개! 황금 레시피 대공개"
- 흥미를 끄는 표현: "놓치면 후회하는", "진짜 알아야 할", "숨겨진 비밀", "완벽한 공략법"
- 구체적 혜택 강조: "5분만에 완성", "비용 50% 절약", "실패 없는 방법"
- 감정적 호소: "이제 걱정 끝!", "드디어 찾았다", "정말 쉬워요"

**📝 콘텐츠 품질 기준:**
- 각 소제목마다 최소 3-4개 문단 작성 (문단당 최소 150자 이상)
- 구체적 사례, 수치, 단계별 설명으로 내용 풍부하게 작성
- 실무에 바로 활용 가능한 상세한 정보 포함
- 표와 리스트를 활용하여 정보를 체계적으로 정리
- **오직 실용적이고 현재 유용한 정보만 포함**

**📊 테이블 생성 필수 규칙 (매우 중요):**
- 비교 정보가 있으면 반드시 비교표 작성 (장단점, 가격, 특징, 차이점 등)
- 단계별 과정은 단계표로 정리 (절차, 순서, 방법 등)  
- 수치/통계 데이터는 데이터표로 작성 (요금, 시간, 비용, 성과 등)
- 분류 정보는 분류표로 정리 (유형, 종류, 카테고리 등)
- **케이스별 추천표 필수**: 상황/목적별로 어떤 선택을 해야 하는지 상세 표 작성
- 각 주요 섹션마다 최소 1개 이상의 테이블 포함 필수
- 전체 글에서 최소 6-8개의 테이블 필수 포함 (케이스별 추천표 포함)
- 테이블은 정보 전달의 핵심 수단으로 활용

**📋 요약박스 생성 필수 규칙:**
- **글의 마지막 부분에 요약박스 필수 포함**
- 요약박스 내용: 핵심 포인트 3-5개, 최종 추천사항, 주의사항
- 요약박스 디자인: 눈에 띄는 스타일로 별도 박스 처리
- "📋 핵심 요약" 또는 "💡 정리하면" 등의 제목 사용 

**작성 원칙:**
- {request.word_count}단어 분량 (HTML 태그 제외)
- 테이블 5-7개 이상 포함 (필수){"" if not is_comparison_topic else " - 비교 주제는 비교표 최소 3개 필수"}
- 브런치 포맷: H2/H3 섹션 구성
- 톤: {request.tone}
- 언어: {request.target_language}

{language_instruction}

**🚨 중요: JSON 형식 준수 🚨**
응답은 반드시 유효한 JSON 구조로 제공해주세요. HTML 속성의 따옴표는 반드시 \" 로 이스케이프해야 합니다.

응답 형식:
{{
    "title": "창의적이고 매력적인 제목",
    "html_content": "완전한 HTML 콘텐츠 (모든 HTML 속성의 따옴표는 반드시 \\\"로 이스케이프)",
    "markdown_content": "체계적 구조의 마크다운 콘텐츠", 
    "summary": "2-3문장의 핵심 요약",
    "tags": ["실무", "가이드", "관련주제"],
{image_instructions}
}}

**JSON 작성 규칙:**
- HTML 속성의 모든 따옴표는 \" 형태로 이스케이프 필수
- 예시: "html_content": "<h1 style=\\"color: #000\\">제목</h1>"
- 줄바꿈은 \\n으로 표현
- 백슬래시는 \\\\로 이스케이프

**🎨 HTML 스타일 참고** (JSON에 넣을 때는 반드시 따옴표 이스케이프!):
- **메인 제목**: <h1 style="color: #2c3e50; font-size: 2.8em; font-weight: 800; margin-bottom: 0.8em; line-height: 1.2; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">창의적인 제목</h1>
- **도입부**: <div style="color: #2c3e50; font-size: 1.2em; line-height: 1.9; margin-bottom: 3em; background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 50%, #ffeaa7 100%); padding: 30px; border-radius: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.12); border: 1px solid rgba(255,255,255,0.2); backdrop-filter: blur(10px); position: relative; overflow: hidden;">
    <div style="position: absolute; top: -50%; right: -50%; width: 200%; height: 200%; background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%); pointer-events: none;"></div>
    <div style="position: relative; z-index: 1;">✨ 인트로 내용</div>
</div>
- **섹션 제목**: <h2 style="color: #2c3e50; font-size: 2.1em; font-weight: 700; margin-top: 3.5em; margin-bottom: 1.5em; background: linear-gradient(135deg, #74b9ff 0%, #0984e3 50%, #6c5ce7 100%); padding: 20px 30px; border-radius: 15px; box-shadow: 0 6px 20px rgba(0,0,0,0.15); text-align: center; color: white; transform: perspective(1000px) rotateX(5deg); transition: all 0.3s ease;">🎯 섹션제목</h2>
- **이미지 삽입**: <img src="이미지URL" alt="설명" style="width: 100%; max-width: 700px; height: auto; margin: 2em auto; display: block; border-radius: 20px; box-shadow: 0 12px 40px rgba(0,0,0,0.2); border: 4px solid white; filter: brightness(1.05) contrast(1.1);">
- **본문**: <p style="color: #2c3e50; line-height: 1.9; font-size: 17px; margin-bottom: 2em; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 25px; border-radius: 12px; border-left: 6px solid #74b9ff; box-shadow: 0 4px 16px rgba(0,0,0,0.08); font-weight: 400;">상세한 본문 내용</p>
- **강조**: <strong style="color: white; font-weight: 700; background: linear-gradient(135deg, #e17055 0%, #d63031 50%, #e84393 100%); padding: 4px 10px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">중요한 내용</strong>
- **리스트**: <ul style="color: #2c3e50; margin: 2em 0; padding: 25px; background: linear-gradient(135deg, #ddd6fe 0%, #c084fc 20%, #e879f9 100%); border-radius: 15px; box-shadow: 0 6px 24px rgba(0,0,0,0.12); list-style: none;"><li style="margin-bottom: 1em; line-height: 1.7; background: white; padding: 15px 20px; border-radius: 10px; margin: 8px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 4px solid #74b9ff; font-weight: 500; transition: all 0.3s ease;">🔹 항목: 상세 설명</li></ul>
- **테이블**: <table style="width: 100%; border-collapse: separate; border-spacing: 0; margin: 2em 0; border-radius: 15px; overflow: hidden; box-shadow: 0 8px 32px rgba(0,0,0,0.15); background: white;"><thead><tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);"><th style="border: none; padding: 20px; text-align: center; font-weight: 700; color: white; font-size: 16px; text-transform: uppercase; letter-spacing: 1px;">항목</th><th style="border: none; padding: 20px; text-align: center; font-weight: 700; color: white; font-size: 16px; text-transform: uppercase; letter-spacing: 1px;">기준</th><th style="border: none; padding: 20px; text-align: center; font-weight: 700; color: white; font-size: 16px; text-transform: uppercase; letter-spacing: 1px;">혜택</th></tr></thead><tbody><tr style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);"><td style="border: none; padding: 18px; color: #2c3e50; text-align: center; border-bottom: 1px solid rgba(0,0,0,0.05); font-weight: 500;">내용</td></tr></tbody></table>
- **팁 박스**: <div style="background: linear-gradient(135deg, #fdcb6e 0%, #e17055 50%, #fd79a8 100%); border: none; padding: 25px; margin: 2.5em 0; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.15); position: relative; overflow: hidden;">
    <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(circle at top right, rgba(255,255,255,0.2) 0%, transparent 50%); pointer-events: none;"></div>
    <p style="color: white; margin: 0; font-style: italic; font-weight: 600; font-size: 16px; position: relative; z-index: 1; text-shadow: 0 1px 3px rgba(0,0,0,0.3);">💡 실전 팁: 구체적인 조언</p>
</div>
- **구분선**: <hr style="border: none; height: 4px; background: linear-gradient(90deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #667eea 75%, #764ba2 100%); margin: 4em 0; border-radius: 2px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
- **주의사항**: <span style="color: white; font-weight: 700; background: linear-gradient(135deg, #ff6b6b 0%, #feca57 50%, #ff9ff3 100%); padding: 12px 20px; border-radius: 25px; box-shadow: 0 4px 16px rgba(0,0,0,0.2); display: inline-block; font-size: 15px; text-transform: uppercase; letter-spacing: 0.5px;">⚠️ 주의사항</span>
- **카드 박스**: <div style="background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%); padding: 30px; margin: 25px 0; border-radius: 20px; box-shadow: 0 12px 48px rgba(0,0,0,0.12); border: 1px solid rgba(0,0,0,0.05); backdrop-filter: blur(10px); position: relative; overflow: hidden;">
    <div style="position: absolute; top: -2px; left: -2px; right: -2px; bottom: -2px; background: linear-gradient(135deg, #667eea, #764ba2, #f093fb); border-radius: 22px; z-index: -1;"></div>
    카드 내용
</div>
- **링크 버튼**: <div style="text-align: center; margin: 25px 0;"><a href="#" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%); color: white; text-decoration: none; font-weight: 700; font-size: 15px; padding: 15px 30px; border-radius: 50px; box-shadow: 0 8px 32px rgba(0,0,0,0.2); transform: translateY(0); transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); text-transform: uppercase; letter-spacing: 1px; position: relative; overflow: hidden;">
    <span style="position: relative; z-index: 1;">버튼 텍스트</span>
    <div style="position: absolute; top: 0; left: -100%; width: 100%; height: 100%; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent); transition: all 0.5s;"></div>
</a></div>
- **요약박스**: <div style="background: linear-gradient(135deg, #74b9ff 0%, #0984e3 50%, #6c5ce7 100%); padding: 35px; margin: 3em 0; border-radius: 25px; box-shadow: 0 15px 50px rgba(0,0,0,0.2); border: 3px solid rgba(255,255,255,0.1); position: relative; overflow: hidden;">
    <div style="position: absolute; top: -50%; right: -50%; width: 200%; height: 200%; background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%); pointer-events: none;"></div>
    <h3 style="color: white; margin: 0 0 25px 0; font-size: 1.6em; font-weight: 800; text-align: center; text-shadow: 0 2px 4px rgba(0,0,0,0.3); position: relative; z-index: 1;">📋 핵심 요약</h3>
    <div style="color: white; line-height: 1.8; font-size: 16px; font-weight: 500; position: relative; z-index: 1; text-shadow: 0 1px 3px rgba(0,0,0,0.2);">요약 내용</div>
</div>

**중요: 절대 흰색(#ffffff, #fff, white) 또는 매우 밝은 색상을 사용하지 마세요.**

마크다운 작성 규칙 (브런치 스타일):
- 제목: # 메인 제목
- 인트로를 위한 구분: > 인트로 내용 (인용문으로 표현)
- 부제목: ## 부제목  
- 소제목: ### 소제목
- 본문: 일반 텍스트 (줄바꿈 두 번으로 문단 구분)
- 강조: **강조 텍스트**
- 리스트: - 항목 또는 1. 번호 항목
- 표 형식: | 제목1 | 제목2 | 제목3 | (마크다운 테이블 문법 사용)
- 팁/정보: > 💡 **유용한 팁**: 팁 내용
- 관련 링크: [소제목](#) (버튼 형태로 표현)

**목표 단어 수({request.word_count}단어)에 정확히 맞춰 작성하되, 브런치 스타일의 깔끔하고 체계적인 구조를 유지하세요.**

**⚠️ 필수사항: 각 섹션마다 관련페이지로 이동할 수 있는 링크를 반드시 포함해야 합니다!**"""
    
    def _create_user_prompt(self, request: GenerationRequest) -> str:
        """Create user prompt for AI."""
        image_instructions = ""
        if request.include_images:
            image_instructions = "3. **섹션별 관련 이미지**: 각 주요 섹션 제목에 직접 관련된 구체적인 이미지 3-5개 포함 (예: '대한항공' 섹션 → 대한항공/항공기 이미지)\n"
        
        # Calculate target range - use 10% margin as requested
        margin = max(200, int(request.word_count * 0.1))  # 10% or minimum 200 words
        min_words = request.word_count - margin
        max_words = request.word_count + margin
        
        word_count_instruction = f"""1. **🚨 절대적 단어수 준수 🚨**: HTML 태그를 완전히 제외한 순수 텍스트가 반드시 {min_words}-{max_words}단어 사이여야 합니다.
   
   ⚠️ 중요 계산 방식:
   - 목표 단어수: {request.word_count}단어
   - 허용 범위: {min_words}단어 ~ {max_words}단어 (±{margin}단어)
   - HTML 태그는 단어수에 포함되지 않습니다
   - <p>, <h1>, <div> 등 모든 태그 제외하고 순수 텍스트만 계산
   
   📝 작성 전략 (절대 준수):
   - 현재 {request.word_count}단어는 상당히 긴 분량입니다 - 반드시 이 분량을 채워야 합니다
   - 각 섹션을 매우 상세하고 길게 작성하세요 (섹션당 최소 150-200단어)
   - 구체적 예시, 상세한 설명, 실무 팁을 풍부하게 추가
   - 8-12개 정도의 상세한 섹션으로 구성 
   - 단어수가 부족하면 반드시 더 많은 내용 추가
   - 모든 문단은 최소 3-4문장 이상으로 구성
   - 나열형 설명보다는 서술형 상세 설명 위주로 작성
   - 반드시 {min_words}단어 이상 작성 - 이것은 절대 기준입니다!"""
            
        important_points = f"""{word_count_instruction}
2. HTML 버전과 마크다운 버전 모두 제공하세요
{image_instructions}
4. **인라인 텍스트 링크 필수**: 콘텐츠 내용 중에 구체적인 장소, 서비스, 앱 언급 시 반드시 "(https://...)" 형태로 링크 추가
   - 스탠리 파크 언급 시: "스탠리 파크(https://vancouver.ca/parks-recreation-culture/stanley-park.aspx)"
   - 환전 서비스: "환전하기(https://wise.com/kr/currency-converter/cad-to-krw-rate)"  
   - 교통 앱: "TransLink(https://www.translink.ca/)" + "Uber(https://www.uber.com/)"
   - 관광명소: 각 명소의 공식 홈페이지 링크
   - 교통수단: 공식 교통기관 사이트 링크
   - 예약 사이트: 공식 예약 서비스 링크
5. HTML에는 인라인 스타일을 적용하세요
6. **모든 텍스트는 검정색(#000000)을 기본으로 사용하세요** - 제목, 부제목, 소제목, 본문 모두 검정색
7. **오직 강조 부분만 색상 사용**: 중요한 키워드나 강조 텍스트에만 색상을 적용하세요
8. 완전한 HTML 구조로 작성하여 웹페이지에 바로 표시 가능하게 만드세요
9. 절대 흰색(#ffffff, #fff, white)이나 매우 밝은 색상은 사용하지 마세요
10. **섹션별 링크 금지**: 섹션 제목 뒤에 "자세히 보기", "바로가기" 등의 별도 링크 버튼을 만들지 마세요. 오직 인라인 링크만 사용
11. **절대 Google 검색 링크 금지**: 어떤 경우에도 google.com/search 형태의 링크를 만들지 마세요
12. **링크 생성 전면 금지**: 섹션별 링크, 외부 링크, 참조 링크 등 모든 <a> 태그 링크 생성을 하지 마세요

**🔥 추가 필수 요구사항 (절대 준수):**
13. **케이스별 추천표 반드시 포함**: 다양한 상황/목적에 따른 추천 항목을 표로 정리
14. **요약박스 필수**: 글의 마지막에 핵심 내용을 정리한 요약박스를 반드시 포함하세요
15. **이미지는 실제 img 태그로 생성**: 텍스트 설명이 아닌 실제 <img> 태그를 사용하세요
16. **다중 항목 주제의 경우**: 명시된 숫자만큼 정확히 모든 선택지/항목을 다뤄야 합니다"""

    def _get_tone_specific_guidelines(self, tone: str) -> str:
        """Get tone-specific content guidelines to avoid inappropriate content."""
        tone_lower = tone.lower() if tone else ""
        
        if tone_lower in ['analytical', '분석적', 'academic', '학술적']:
            return """- ❌ "실전활용팁", "꿀팁", "노하우" 같은 캐주얼한 표현 금지
- ✅ 객관적 분석, 데이터 기반 설명, 이론적 배경 중심
- ✅ "분석 결과", "연구에 따르면", "데이터 분석" 등의 표현 사용
- ✅ 중립적이고 정확한 정보 전달에 집중"""
        elif tone_lower in ['professional', '전문적', 'formal', '공식적']:
            return """- ❌ "꿀팁", "생활 노하우", "실전 비법" 같은 비격식적 표현 금지
- ✅ 공식적이고 신뢰성 있는 정보 제공
- ✅ "권장사항", "주요 고려사항", "전문적 접근방법" 등의 표현 사용
- ✅ 비즈니스 및 공식 문서 수준의 격식"""
        elif tone_lower in ['thoughtful', '사려깊은', 'contemplative', '성찰적']:
            return """- ❌ 성급한 조언이나 단정적 표현 금지
- ✅ 신중하고 균형잡힌 관점 제시
- ✅ "고려해볼 점", "다각도 검토", "신중한 접근" 등의 표현 사용
- ✅ 다양한 관점과 가능성을 제시"""
        elif tone_lower in ['explanatory', '설명적', 'educational', '교육적']:
            return """- ❌ "실전 팁", "비법" 같은 표현보다는 설명에 집중
- ✅ 단계별 설명과 이해하기 쉬운 구조
- ✅ "설명하자면", "이해를 돕기 위해", "구체적으로 살펴보면" 등 사용
- ✅ 교육적 가치와 이해도 향상에 집중"""
        else:  # casual, friendly, conversational 등
            return """- ✅ 적절한 수준의 활용 팁과 실용적 조언 포함 가능
- ✅ "유용한 정보", "참고사항", "활용 방법" 등의 표현 사용
- ✅ 독자에게 도움이 되는 실질적 내용 제공"""
    
    def _create_user_prompt(self, request: GenerationRequest) -> str:
        """Create user prompt for AI."""
        image_instructions = ""
        if request.include_images:
            image_instructions = "3. **섹션별 관련 이미지**: 각 주요 섹션 제목에 직접 관련된 구체적인 이미지 3-5개 포함 (예: '대한항공' 섹션 → 대한항공/항공기 이미지)\n"
        
        # Handle multiple options if requested
        num_options = getattr(request, 'num_options', 1)
        balance_word_count = getattr(request, 'balance_word_count', True)
        
        # Temporarily disable multiple options to fix content generation issue
        if num_options > 1:
            print(f"DEBUG: Multiple options requested ({num_options}) but temporarily using single option for stability")
            num_options = 1
        
        # Calculate target range and word distribution
        if num_options > 1 and balance_word_count:
            # Distribute total word count across options
            base_count_per_option = request.word_count // num_options
            remainder = request.word_count % num_options
            
            # Calculate margins for each option
            margin = max(100, int(base_count_per_option * 0.1))
            min_words = base_count_per_option - margin
            max_words = base_count_per_option + margin
            
            word_count_instruction = f"""1. **🚨 절대적 단어수 준수 (다중 선택지) 🚨**: 
   - **총 {num_options}개 선택지 생성**
   - **각 선택지별 목표**: {base_count_per_option}단어 (HTML 태그 제외)
   - **각 선택지별 허용 범위**: {min_words}-{max_words}단어 
   - **선택지별 글자수 균형**: 각 선택지가 비슷한 분량을 가져야 합니다
   
   ⚠️ 중요 작성 지침:
   - 전체 {request.word_count}단어를 {num_options}개 선택지로 균등 분배
   - 선택지 1: 약 {base_count_per_option + (1 if remainder > 0 else 0)}단어
   - 선택지 2: 약 {base_count_per_option + (1 if remainder > 1 else 0)}단어
   {f"- 선택지 3: 약 {base_count_per_option + (1 if remainder > 2 else 0)}단어" if num_options > 2 else ""}
   {f"- 선택지 4: 약 {base_count_per_option + (1 if remainder > 3 else 0)}단어" if num_options > 3 else ""}
   {f"- 선택지 5: 약 {base_count_per_option + (1 if remainder > 4 else 0)}단어" if num_options > 4 else ""}
   
   📝 각 선택지 작성 전략:
   - 각 선택지는 동일한 주제를 다른 관점/구조로 접근
   - 각 선택지마다 {base_count_per_option}단어 내외로 균등 분배
   - 선택지간 중복 내용 최소화, 각각 독특한 가치 제공"""
        else:
            # Single option - original logic
            margin = max(200, int(request.word_count * 0.1))
            min_words = request.word_count - margin
            max_words = request.word_count + margin
            
            word_count_instruction = f"""1. **🚨 절대적 단어수 준수 🚨**: HTML 태그를 완전히 제외한 순수 텍스트가 반드시 {min_words}-{max_words}단어 사이여야 합니다.
   
   ⚠️ 중요 계산 방식:
   - 목표 단어수: {request.word_count}단어
   - 허용 범위: {min_words}단어 ~ {max_words}단어 (±{margin}단어)
   - HTML 태그는 단어수에 포함되지 않습니다
   - <p>, <h1>, <div> 등 모든 태그 제외하고 순수 텍스트만 계산
   
   📝 작성 전략 (절대 준수):
   - 현재 {request.word_count}단어는 상당히 긴 분량입니다 - 반드시 이 분량을 채워야 합니다
   - 각 섹션을 매우 상세하고 길게 작성하세요 (섹션당 최소 150-200단어)
   - 구체적 예시, 상세한 설명, 실무 팁을 풍부하게 추가
   - 8-12개 정도의 상세한 섹션으로 구성 
   - 단어수가 부족하면 반드시 더 많은 내용 추가
   - 모든 문단은 최소 3-4문장 이상으로 구성
   - 나열형 설명보다는 서술형 상세 설명 위주로 작성
   - 반드시 {min_words}단어 이상 작성 - 이것은 절대 기준입니다!"""
            
        important_points = f"""{word_count_instruction}
2. HTML 버전과 마크다운 버전 모두 제공하세요
{image_instructions}
4. **인라인 텍스트 링크 필수**: 콘텐츠 내용 중에 구체적인 장소, 서비스, 앱 언급 시 반드시 "(https://...)" 형태로 링크 추가
   - 스탠리 파크 언급 시: "스탠리 파크(https://vancouver.ca/parks-recreation-culture/stanley-park.aspx)"
   - 환전 서비스: "환전하기(https://wise.com/kr/currency-converter/cad-to-krw-rate)"  
   - 교통 앱: "TransLink(https://www.translink.ca/)" + "Uber(https://www.uber.com/)"
   - 관광명소: 각 명소의 공식 홈페이지 링크
   - 교통수단: 공식 교통기관 사이트 링크
   - 예약 사이트: 공식 예약 서비스 링크
5. HTML에는 인라인 스타일을 적용하세요
6. **모든 텍스트는 검정색(#000000)을 기본으로 사용하세요** - 제목, 부제목, 소제목, 본문 모두 검정색
7. **오직 강조 부분만 색상 사용**: 중요한 키워드나 강조 텍스트에만 색상을 적용하세요
8. 완전한 HTML 구조로 작성하여 웹페이지에 바로 표시 가능하게 만드세요
9. 절대 흰색(#ffffff, #fff, white)이나 매우 밝은 색상은 사용하지 마세요
10. **섹션별 링크 금지**: 섹션 제목 뒤에 "자세히 보기", "바로가기" 등의 별도 링크 버튼을 만들지 마세요. 오직 인라인 링크만 사용
11. **절대 Google 검색 링크 금지**: 어떤 경우에도 google.com/search 형태의 링크를 만들지 마세요
12. **링크 생성 전면 금지**: 섹션별 링크, 외부 링크, 참조 링크 등 모든 <a> 태그 링크 생성을 하지 마세요"""

        # Detect comparison topic again for user prompt
        is_comparison_topic = any(keyword in request.topic.lower() for keyword in ['vs', 'versus', '대', '비교', '차이'])
        
        # Enhanced topic categorization system
        topic_lower = request.topic.lower()
        
        # Detect specific transportation/direction topics only
        is_transportation_topic = (
            any(keyword in topic_lower for keyword in ['가는법', '가는방법', '이동하는법', '교통수단']) and
            any(direction_keyword in topic_lower for direction_keyword in ['에서', '까지', '로 가는', '로 이동', 'how to get to', 'way to'])
        )
        
        # Detect food/cuisine topics
        is_food_topic = any(keyword in topic_lower for keyword in [
            '맛집', '음식', '요리', '레시피', '만드는법', '재료', '조리법', '음식점', '식당', '카페', 
            'food', 'restaurant', 'recipe', 'cooking', 'cuisine', 'dish'
        ])
        
        # Detect health/medicine topics
        is_health_topic = any(keyword in topic_lower for keyword in [
            '병원', '의료', '건강', '질병', '약', '치료', '증상', '아플때', '몸이',
            'health', 'medicine', 'medical', 'treatment', 'symptoms', 'doctor'
        ])
        
        # Detect weather topics
        is_weather_topic = any(keyword in topic_lower for keyword in [
            '날씨', '기온', '비', '눈', '바람', '습도', '태풍', '온도',
            'weather', 'temperature', 'rain', 'snow', 'wind', 'humidity'
        ])
        
        # Detect music/entertainment topics
        is_music_topic = any(keyword in topic_lower for keyword in [
            '음악', '노래', '가수', '앨범', '듣기좋은', '플레이리스트', '장르',
            'music', 'song', 'artist', 'album', 'playlist', 'genre'
        ])
        
        # Detect tourist attraction topics
        is_tourism_topic = any(keyword in topic_lower for keyword in [
            '관광', '명소', '여행지', '볼거리', '여행', '관광지', '휴양지', '데이트코스',
            'tourism', 'attraction', 'sightseeing', 'travel destination', 'tourist spot'
        ]) and not is_transportation_topic  # Exclude if it's about transportation
        
        # Detect TOP/ranking topic again for user prompt
        import re
        topic_lower = request.topic.lower()
        ranking_number_user = None
        is_ranking_topic_user = False
        
        # Check for TOP patterns for user prompt
        top_patterns = [
            r'top\s*(\d+)', r'톱\s*(\d+)', r'베스트\s*(\d+)', r'best\s*(\d+)', 
            r'추천\s*(\d+)', r'(\d+)가지', r'(\d+)개', r'(\d+)종류', 
            r'(\d+)위', r'(\d+)순위'
        ]
        
        for pattern in top_patterns:
            match = re.search(pattern, topic_lower)
            if match:
                ranking_number_user = int(match.group(1))
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
                data = json.loads(json_str)
                
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
                            nested_data = json.loads(nested_json)
                            # Use the html_content from the nested JSON
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