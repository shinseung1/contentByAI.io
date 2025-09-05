"""Content generator using AI clients."""

import asyncio
import uuid
import json
import os
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path

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
                        images=processed_images
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
        
        return GenerationResponse(
            job_id=db_job.job_id,
            status=GenerationStatus(db_job.status),
            message=db_job.topic,  # Use topic as message for display
            progress=db_job.progress / 100.0 if db_job.progress else 0.0,
            content=content,
            error=db_job.error_message,
            created_at=db_job.created_at,
            completed_at=db_job.updated_at if db_job.status in ['completed', 'failed'] else None
        )
    
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
                "title": content.title,
                "html_content": content.content,
                "summary": content.summary,
                "tags": content.tags,
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
                    """Safely serialize objects to JSON, converting problematic types."""
                    if hasattr(obj, '__dict__'):
                        # If it's a custom object, convert to dict
                        if hasattr(obj, 'url') and hasattr(obj, 'alt'):  # ImageInfo-like
                            return {"url": str(obj.url), "alt": str(obj.alt), "caption": str(obj.caption)}
                        return obj.__dict__
                    elif isinstance(obj, (list, tuple)):
                        return [safe_json_serialize(item) for item in obj]
                    elif isinstance(obj, dict):
                        return {k: safe_json_serialize(v) for k, v in obj.items()}
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
                        "title": str(content.title),
                        "html_content": str(content.content),
                        "summary": str(content.summary) if content.summary else "",
                        "tags": list(content.tags) if content.tags else [],
                        "images": []  # Skip images entirely if serialization fails
                    }, ensure_ascii=False)
                job.html_content = content.content
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
        content = self._parse_ai_response(response.content, request)
        
        # Post-process HTML to remove white text, fix newlines, process inline links, and remove prohibited links
        if content.content:
            content.content = self._fix_white_text(content.content)
            content.content = self._fix_newline_display(content.content)
            content.content = self._process_inline_links(content.content)
            content.content = self._remove_prohibited_links_from_content(content.content)
            # Try news-specific links first for current affairs topics
            content.content = await self._add_news_specific_links(content.content, request.topic, provider, config)
            # Then add place-specific links if not a news topic
            content.content = await self._add_specific_place_links(content.content, request.topic, provider, config)
            # Final pass to remove any remaining Google/search links
            content.content = self._final_google_link_cleanup(content.content)
            # Skip AI-generated section links, use only inline links within content
            # content.content = await self._add_ai_generated_links(content.content, request.topic, provider, config)
        
        return content
    
    def _create_system_prompt(self, request: GenerationRequest) -> str:
        """Create system prompt for AI."""
        language_instruction = ""
        if request.target_language == "ko":
            language_instruction = "모든 응답은 한국어로 작성해주세요."
        elif request.target_language == "en":
            language_instruction = "Please respond in English."
        
        image_instructions = ""
        if request.include_images:
            image_instructions = """    "images": [
        {
            "url": "section_specific_image_1",
            "alt": "첫 번째 주요 섹션과 관련된 구체적인 이미지 설명",
            "caption": "첫 번째 섹션 제목에 맞는 이미지 캡션"
        },
        {
            "url": "section_specific_image_2",
            "alt": "두 번째 주요 섹션과 관련된 구체적인 이미지 설명", 
            "caption": "두 번째 섹션 제목에 맞는 이미지 캡션"
        },
        {
            "url": "section_specific_image_3",
            "alt": "세 번째 주요 섹션과 관련된 구체적인 이미지 설명",
            "caption": "세 번째 섹션 제목에 맞는 이미지 캡션"
        }
    ],"""
        else:
            image_instructions = """    "images": [],"""
        
        return f"""당신은 전문 가이드 작성자입니다. 
다음 **샘플 스타일을 정확히 따라서** 체계적이고 정보성 있는 완전한 가이드를 작성하세요:

**샘플 분석 및 적용 기준 (대한항공 스카이패스 가이드 구조)**:

1. **제목 스타일**: "○○○ 가이드 — 전체 통합본" 형태의 완전 정복 가이드
2. **섹션 구조**: 
   - ## 1. ○○○란? (개념 설명, 핵심 기능, 대상)
   - ## 2. ○○○ 등급/분류 (체계적 분류와 기준표)
   - ## 3. 제휴/연관 시스템 (관련 서비스나 파트너)
   - ## 4. 구체적 사용법 (단계별 가이드, 기준표)
   - ## 5. 실제 적용/공제/활용 (실무 정보, 수치 포함)
   - ## 6-7. 부가 서비스 (추가 혜택, 보너스 정보)
   - ## 8. 요약 및 팁 (핵심 포인트 + 실전 조언)

3. **내용 스타일**:
   - 각 섹션마다 구체적 기준표나 수치 정보 포함
   - "- 항목: 설명" 형태의 명확한 구조
   - 실무에 바로 적용 가능한 구체적 정보
   - 표 형태로 정리된 기준이나 요금 정보
   - 주의사항과 제한 조건 명시

4. **이미지 활용**: 각 섹션마다 해당 섹션 제목과 직접 관련된 구체적인 이미지 (예: "대한항공" 섹션 → 대한항공 관련 이미지)

작성 요구사항:
- 톤: {request.tone} (샘플처럼 신뢰성 있고 정확한 정보 전달 톤)
- 목표 단어 수: 정확히 {request.word_count}단어 (HTML 태그 제외하고 순수 텍스트 기준)
- 언어: {request.target_language}

{language_instruction}

### 필수 적용 사항

1. **제목**: "○○○ 완전 정복 가이드" 또는 "○○○ 가이드 — 전체 통합본" 형태
2. **구조**: 샘플과 같은 8개 내외의 번호별 섹션 구성
3. **정보 밀도**: 각 섹션에 구체적 수치, 기준, 표, 조건 등 실무 정보 포함
4. **표 활용**: 기준이나 요금, 등급 등은 반드시 표 형태로 정리
5. **실용성**: 독자가 바로 활용할 수 있는 단계별 가이드
6. **완성도**: 해당 주제에 대한 모든 필요 정보를 포함한 완전 가이드

**중요: 반드시 HTML 형식과 마크다운 형식 두 버전 모두 제공해주세요.**

응답 형식을 다음 JSON 구조로 제공해주세요:
{{
    "title": "○○○ 완전 정복 가이드 — 전체 통합본",
    "html_content": "샘플과 같은 완전한 가이드 형태의 HTML 콘텐츠 (표, 구체적 정보, 실무 활용법 포함)",
    "markdown_content": "샘플과 같은 체계적 구조의 마크다운 콘텐츠", 
    "summary": "2-3문장의 핵심 요약",
    "tags": ["실무", "가이드", "관련주제"],
{image_instructions}
}}

HTML 작성 규칙 (브런치 스타일):
- 제목: <h1 style="color: #000000; font-size: 2.4em; font-weight: 700; margin-bottom: 0.5em; line-height: 1.2;">메인 제목</h1>
- 인트로: <div style="color: #000000; font-size: 1.1em; line-height: 1.8; margin-bottom: 2em; border-left: 3px solid #3498db; padding-left: 20px;">인트로 내용</div>
- 부제목: <h2 style="color: #000000; font-size: 1.8em; font-weight: 600; margin-top: 2.5em; margin-bottom: 1em;">부제목</h2>
- 소제목: <h3 style="color: #000000; font-size: 1.4em; font-weight: 500; margin-top: 2em; margin-bottom: 0.8em;">소제목</h3>
- 본문: <p style="color: #000000; line-height: 1.8; font-size: 16px; margin-bottom: 1.5em;">본문 내용</p>
- 강조: <strong style="color: #e74c3c; font-weight: 600;">강조 텍스트</strong>
- 리스트: <ul style="color: #000000; margin: 1em 0; padding-left: 20px;"><li style="margin-bottom: 0.8em; line-height: 1.6;">항목</li></ul>
- 번호 리스트: <ol style="color: #000000; margin: 1em 0; padding-left: 20px;"><li style="margin-bottom: 0.8em; line-height: 1.6;">항목</li></ol>
- 표 형식: <table style="width: 100%; border-collapse: collapse; margin: 1.5em 0; border: 1px solid #ddd;"><thead><tr style="background: #f8f9fa;"><th style="border: 1px solid #ddd; padding: 12px; text-align: left; font-weight: 600; color: #000000;">제목</th></tr></thead><tbody><tr><td style="border: 1px solid #ddd; padding: 12px; color: #000000;">내용</td></tr></tbody></table>
- 인용/팁: <div style="background: #f8f9fa; border-left: 4px solid #3498db; padding: 1.5em; margin: 2em 0; border-radius: 4px;"><p style="color: #000000; margin: 0; font-style: italic;">💡 유용한 팁이나 중요 정보</p></div>
- 중요한 키워드: <span style="color: #2980b9; font-weight: 600;">키워드</span>
- 주의사항: <span style="color: #e67e22; font-weight: 600;">주의사항</span>
- 관련 링크: <div style="margin: 15px 0;"><a href="#" style="color: #3498db; text-decoration: none; font-weight: 600; font-size: 14px; padding: 8px 12px; border: 1px solid #3498db; border-radius: 6px; display: inline-block; background: transparent;">섹션명</a></div>

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
   
   📝 작성 전략:
   - 현재 {request.word_count}단어는 상당히 긴 분량입니다
   - 각 섹션을 매우 상세하고 길게 작성하세요
   - 구체적 예시, 상세한 설명, 실무 팁을 풍부하게 추가
   - 8-10개 정도의 상세한 섹션으로 구성
   - 단어수가 부족하면 반드시 더 많은 내용 추가"""
            
        important_points = f"""{word_count_instruction}
2. HTML 버전과 마크다운 버전 모두 제공하세요
{image_instructions}4. **인라인 텍스트 링크 필수**: 콘텐츠 내용 중에 구체적인 장소, 서비스, 앱 언급 시 반드시 "(https://...)" 형태로 링크 추가
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
   
   📝 작성 전략:
   - 현재 {request.word_count}단어는 상당히 긴 분량입니다
   - 각 섹션을 매우 상세하고 길게 작성하세요
   - 구체적 예시, 상세한 설명, 실무 팁을 풍부하게 추가
   - 8-10개 정도의 상세한 섹션으로 구성
   - 단어수가 부족하면 반드시 더 많은 내용 추가"""
            
        important_points = f"""{word_count_instruction}
2. HTML 버전과 마크다운 버전 모두 제공하세요
{image_instructions}4. **인라인 텍스트 링크 필수**: 콘텐츠 내용 중에 구체적인 장소, 서비스, 앱 언급 시 반드시 "(https://...)" 형태로 링크 추가
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

        return f"""주어진 주제에 대해 sample.md와 sample2.md 기준으로 **완전 정복 가이드**를 작성해주세요.

**📋 표준 템플릿 구조** (sample.md 참고):
1. **메인 제목**: # [주제명] 가이드 — 전체 통합본  
2. **핵심 섹션들**: ## 1. [기본 개념], ## 2. [등급/분류], ## 3. [주요 특징], ## 4. [세부 내용], ## 5. [활용 방법]
3. **이미지 활용**: 각 섹션별 관련 이미지 ![설명](URL) 형식으로 포함
4. **구분선 사용**: --- 를 섹션 간 구분으로 활용  
5. **요약 및 결론**: ## 요약 및 팁, ## 결론으로 마무리
6. **상세 정리**: 브런치 스타일의 추가 정리 섹션 포함

**🔗 링크 규칙** (sample2.md 기준):
- ❌ **절대 금지**: "바로가기", "바로 가기", "Go", "Visit", "Click here" 등 모든 CTA
- ✅ **유일 허용**: "자세히 보기" 단 하나만  
- **사용법**: 메인 섹션 제목 옆에 아래 HTML/CSS 코드로 딱 1개만 배치:

```html
<!-- [주제명] 섹션 - 자세히 보기 버튼 -->  
<a class="see-more" href="#section-detail" aria-label="[주제명] 자세히 보기">자세히 보기</a>
<style>
.see-more {{
  display:inline-flex; align-items:center; gap:.5rem;
  padding:.5rem 1rem; border:1px solid #d0d7de; border-radius:999px;
  background:linear-gradient(180deg,#ffffff,#f3f4f6);
  font-weight:600; text-decoration:none; color:#111827;
  box-shadow:0 1px 2px rgba(0,0,0,.06);
  transition:transform .15s ease, box-shadow .15s ease;
}}
.see-more::after {{ content:"›"; font-size:1rem; line-height:1; }}  
.see-more:hover {{ transform:translateY(-1px); box-shadow:0 4px 12px rgba(0,0,0,.12); }}
</style>
```

**가이드 주제**: {request.topic}

**작성 지침:**
{important_points}

**샘플 기준 완전 가이드 구성 (필수):**
1. **완전 정복 제목** - "○○○ 완전 정복 가이드 — 전체 통합본" 형태
2. **체계적 섹션 구성** (8개 내외):
   - ## 1. ○○○란? → 개념, 정의, 기본 정보
   - ## 2. 분류/등급/유형 → 체계적 분류와 상세 기준
   - ## 3. 관련 시스템/제휴 → 연관 서비스나 파트너 정보
   - ## 4. 구체적 방법/절차 → 단계별 상세 가이드
   - ## 5. 실제 적용/활용 → 실무 정보, 수치, 기준표
   - ## 6-7. 부가 혜택/서비스 → 추가 정보, 보너스 활용법
   - ## 8. 요약 및 실전 팁 → 핵심 정리 + 활용 조언

3. **정보 밀도와 실용성:**
   - 각 섹션에 구체적 수치, 기준표, 조건 포함
   - 표 형태로 정리된 정보 (요금, 등급, 기준 등)
   - 실무에 바로 적용 가능한 단계별 설명
   - 주의사항, 제한 조건, 예외 상황 명시

4. **전문성과 완성도:**
   - 해당 분야의 모든 필요 정보를 포함한 완전 가이드
   - 신뢰할 수 있는 정확한 정보와 수치
   - 독자가 다른 자료를 찾을 필요 없는 완전성

**톤 & 스타일:**
- {request.tone} 톤 + 샘플처럼 신뢰성 있고 정확한 정보 전달
- 전문성과 실용성의 완벽한 결합
- 독자가 전문가 수준의 지식을 얻을 수 있는 깊이

**톤별 내용 조절 필수사항:**
{self._get_tone_specific_guidelines(request.tone)}

**🚨🚨🚨 절대적 단어수 준수 필수 🚨🚨🚨**: 
- **범위**: {min_words}-{max_words}단어 (HTML 태그 완전 제외)
- **목표**: 정확히 {request.word_count}단어 달성
- **계산법**: 모든 HTML 태그 제거 후 순수 텍스트만 카운트
- **전략**: {request.word_count}단어는 매우 긴 분량이므로 각 섹션을 극도로 상세하게 작성
- **필수**: 8-10개의 긴 섹션으로 구성하여 충분한 분량 확보
- **부족시**: 더 많은 섹션, 상세한 예시, 실무 정보 대폭 추가"""
    
    def _parse_ai_response(self, ai_content: str, request: GenerationRequest) -> GeneratedContent:
        """Parse AI response into GeneratedContent."""
        try:
            # Try to extract JSON from the response
            start_idx = ai_content.find('{')
            end_idx = ai_content.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = ai_content[start_idx:end_idx]
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
                
                return GeneratedContent(
                    title=data.get("title", f"Content about {request.topic}"),
                    content=data.get("html_content", data.get("content", ai_content)),
                    markdown_content=data.get("markdown_content"),
                    summary=data.get("summary"),
                    tags=data.get("tags", []),
                    images=processed_images
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
        
        # Patterns to find colors that should be replaced with black
        # Keep only emphasis colors (#e74c3c, #2980b9, #e67e22, #3498db) and replace everything else with black
        color_patterns = [
            r'color:\s*#fff\b',
            r'color:\s*#ffffff\b', 
            r'color:\s*white\b',
            r'color:\s*#f[9-f]{5}\b',  # Very light colors
            r'color:\s*#[ef][ef][ef][ef][ef][ef]\b',  # Very light hex colors
            r'color:\s*rgb\(\s*25[0-5],\s*25[0-5],\s*25[0-5]\s*\)',  # RGB white/near-white
            r'color:\s*#2c3e50\b',  # Replace gray with black
            r'color:\s*#27ae60\b',  # Replace green with black (for headings)
            r'color:\s*#[a-fA-F0-9]{6}\b(?!.*(?:#e74c3c|#2980b9|#e67e22|#3498db|#000000))',  # Replace any hex color except emphasis colors and black
        ]
        
        # Default replacement color (black)
        replacement_color = '#000000'
        
        # Replace problematic colors
        fixed_html = html_content
        for pattern in color_patterns:
            fixed_html = re.sub(pattern, f'color: {replacement_color}', fixed_html, flags=re.IGNORECASE)
        
        # Ensure all text without explicit color is black
        # Add default black color to elements that don't have color specified
        if 'color:' not in fixed_html:
            # Wrap content with default black color
            fixed_html = f'<div style="color: #000000;">{fixed_html}</div>'
        
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
            return f'<a href="{url}" target="_blank" rel="noopener noreferrer" style="color: #3498db; text-decoration: none; font-weight: 500;">{text}</a>'
        
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
    
    def _final_google_link_cleanup(self, html_content: str) -> str:
        """Final pass to remove any remaining Google search links and meaningless links."""
        import re
        
        # ULTRA AGGRESSIVE GOOGLE LINK REMOVAL
        # Step 1: Remove ALL links first, then selectively add back allowed ones
        
        # Extract all links to analyze them
        link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>'
        links = re.findall(link_pattern, html_content, re.IGNORECASE | re.DOTALL)
        
        # Define allowed domains/patterns
        allowed_patterns = [
            r'https?://.*\.gov\.kr',     # Korean government sites
            r'https?://.*\.go\.kr',      # Korean official sites  
            r'https?://.*\.or\.kr',      # Korean organizations
            r'https?://.*\.ac\.kr',      # Korean academic sites
            r'https?://news\.naver\.com', # Naver news
            r'https?://news\.daum\.net',  # Daum news
            r'https?://www\.chosun\.com', # Chosun Ilbo
            r'https?://www\.donga\.com',  # Dong-A Ilbo
            r'https?://www\.joongang\.co\.kr', # JoongAng Ilbo
            r'https?://news\.kbs\.co\.kr', # KBS News
            r'https?://imnews\.imbc\.com', # MBC News
            r'https?://news\.sbs\.co\.kr', # SBS News
            r'https?://www\.ytn\.co\.kr',  # YTN
            r'https?://www\.yna\.co\.kr',  # Yonhap News
            r'https?://www\.whitehouse\.gov', # White House
            r'https?://ustr\.gov',        # US Trade Representative
            r'https?://.*\.state\.gov',   # US State Department
        ]
        
        # Prohibited patterns (ABSOLUTE BLOCK)
        prohibited_patterns = [
            r'.*google\.com.*',
            r'.*search.*',
            r'.*q=.*',
            r'.*%EC%.*',  # URL encoded Korean
            r'.*%ED%.*',  # URL encoded Korean  
            r'.*%EA%.*',  # URL encoded Korean
            r'.*query=.*',
            r'.*searchterm=.*',
            r'.*keyword=.*',
            r'^#$',       # Empty hash links
            r'^$',        # Completely empty links
        ]
        
        # Step 1: Remove ALL existing links
        html_content = re.sub(r'<a[^>]*>.*?</a>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
        html_content = re.sub(r'<div[^>]*>\s*</div>', '', html_content, flags=re.IGNORECASE)  # Remove empty divs
        
        print(f"DEBUG: Removed all links, remaining content length: {len(html_content)}")
        
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
<div style="margin: 20px 0 15px 0; padding: 12px; background: #f8f9fa; border-left: 4px solid #3498db; border-radius: 4px;">
    <p style="color: #000000; margin: 0 0 8px 0; font-weight: 600; font-size: 14px;">📰 관련 정보</p>
    <a href="{url}" target="_blank" rel="noopener noreferrer" 
       style="color: #3498db; text-decoration: none; font-weight: 500; font-size: 14px; 
              border: 1px solid #3498db; padding: 6px 12px; border-radius: 4px; 
              display: inline-block; background: transparent; transition: all 0.3s ease;">
        {display_text}
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
                return f'<a href="{place_url}" target="_blank" rel="noopener noreferrer" style="color: #3498db; text-decoration: none; font-weight: 500;">{match.group(0)}</a>'
            
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
        
        # Simplified link template with just section name + 바로가기
        link_template = '''<div style="margin: 15px 0; text-align: left;">
            <a href="{}" target="_blank" rel="noopener noreferrer" 
               style="color: #3498db; 
                      text-decoration: none; 
                      font-weight: 600; 
                      font-size: 14px;
                      padding: 8px 12px; 
                      border: 1px solid #3498db;
                      border-radius: 6px; 
                      display: inline-block;
                      background: transparent;
                      transition: all 0.2s ease;">
                {}
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