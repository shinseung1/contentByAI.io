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
                images = await self.image_service.get_related_images(request.topic, 5)
                content.images = images
            
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
                "markdown_content": content.markdown_content,
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
                        "markdown_content": str(content.markdown_content) if content.markdown_content else "",
                        "summary": str(content.summary) if content.summary else "",
                        "tags": list(content.tags) if content.tags else [],
                        "images": []  # Skip images entirely if serialization fails
                    }, ensure_ascii=False)
                job.html_content = content.content
                job.markdown_content = content.markdown_content
                job.updated_at = datetime.now().isoformat()
                self.db.save_generation_job(job)
            
        except Exception as e:
            # Update status to failed
            import traceback
            error_msg = str(e)
            full_trace = traceback.format_exc()
            
            # Log to file and console for debugging
            try:
                import os
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
                print(f"Error logged to: {log_path}")
                print(f"GENERATION ERROR: {error_msg}")
                print(full_trace)
            except Exception as log_error:
                print(f"Failed to write error log: {log_error}")
                print(f"Original error: {error_msg}")
                print(full_trace)
            
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
        
        # Post-process HTML to remove white text and add links
        if content.content:
            content.content = self._fix_white_text(content.content)
            content.content = self._add_section_links(content.content)
        
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
            "url": "https://picsum.photos/800/450?random=1",
            "alt": "관련 이미지 설명",
            "caption": "이미지 캡션 설명"
        },
        {
            "url": "https://picsum.photos/800/450?random=2",
            "alt": "관련 이미지 설명 2",
            "caption": "이미지 캡션 설명 2"
        }
    ],"""
        else:
            image_instructions = """    "images": [],"""
        
        return f"""당신은 전문 블로그 작가입니다. 
브런치 스타일의 블로그 글을 작성하세요. 스타일은 https://brunch.co.kr/@hotelscomkr/617 와 유사하게 **깔끔하고, 정보성 있고, 섹션이 나누어진 형태**여야 합니다.

작성 요구사항:
- 톤: {request.tone} (친절하고 신뢰감 있는 정보 전달자 톤)
- 목표 단어 수: 정확히 {request.word_count}단어 (HTML 태그 제외하고 순수 텍스트 기준)
- 언어: {request.target_language}

{language_instruction}

### 지시사항

1. **제목**: 매력적이고 SEO 친화적인 제목 생성
2. **인트로**: 2~3문단으로 흥미를 끌고 전체 내용을 요약하는 도입부 작성
3. **섹션 구분**: 소제목(H2, H3)을 활용해 내용을 체계적으로 나누기
   - 예: 개요 / 방법론 / 상세 설명 / 유의사항 / 실용 팁 등
4. **본문**: 각 섹션은 2~4문단으로 작성하며, 불릿포인트/번호목록도 적극 활용
5. **이미지 포함**: 각 섹션마다 적절한 이미지를 반드시 포함 (최소 3-5개의 이미지 URL 제공)
6. **마무리**: 독자가 행동하도록 유도하는 결론 작성
7. **톤앤매너**: 친절하고 신뢰감 있는 정보 전달자 톤
8. **관련페이지링크**: 정보 전달 시 관련 페이지를 링크하며, 링크에는 대제목 혹은 소제목 + "바로가기" 라는 텍스트 혹은 이미지를 통한 링크를 활용함

**중요: 반드시 HTML 형식과 마크다운 형식 두 버전 모두 제공해주세요.**

응답 형식을 다음 JSON 구조로 제공해주세요:
{{
    "title": "매력적이고 SEO 친화적인 제목",
    "html_content": "완전한 HTML 형식 본문 내용 (스타일 포함) - 반드시 각 섹션마다 <a href='#' style='color: #3498db; text-decoration: none; font-weight: 600; border: 1px solid #3498db; padding: 8px 16px; border-radius: 4px; display: inline-block; margin: 10px 0;'>섹션명 바로가기</a> 형태의 링크 포함",
    "markdown_content": "마크다운 형식 본문 내용 - 반드시 [섹션명 바로가기](#) 형태의 링크 포함", 
    "summary": "2-3문장의 요약",
    "tags": ["관련", "태그", "목록"],
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
- 인용/팁: <div style="background: #f8f9fa; border-left: 4px solid #3498db; padding: 1.5em; margin: 2em 0; border-radius: 4px;"><p style="color: #000000; margin: 0; font-style: italic;">💡 유용한 팁이나 중요 정보</p></div>
- 중요한 키워드: <span style="color: #2980b9; font-weight: 600;">키워드</span>
- 주의사항: <span style="color: #e67e22; font-weight: 600;">주의사항</span>
- 관련 링크: <a href="#" style="color: #3498db; text-decoration: none; font-weight: 600; border: 1px solid #3498db; padding: 8px 16px; border-radius: 4px; display: inline-block; margin: 10px 0;">소제목 바로가기</a>

**중요: 절대 흰색(#ffffff, #fff, white) 또는 매우 밝은 색상을 사용하지 마세요.**

마크다운 작성 규칙 (브런치 스타일):
- 제목: # 메인 제목
- 인트로를 위한 구분: > 인트로 내용 (인용문으로 표현)
- 부제목: ## 부제목  
- 소제목: ### 소제목
- 본문: 일반 텍스트 (줄바꿈 두 번으로 문단 구분)
- 강조: **강조 텍스트**
- 리스트: - 항목 또는 1. 번호 항목
- 팁/정보: > 💡 **유용한 팁**: 팁 내용
- 관련 링크: [소제목 바로가기](#) (버튼 형태로 표현)

**목표 단어 수({request.word_count}단어)에 정확히 맞춰 작성하되, 브런치 스타일의 깔끔하고 체계적인 구조를 유지하세요.**

**⚠️ 필수사항: 각 섹션마다 관련페이지로 이동할 수 있는 "바로가기" 링크를 반드시 포함해야 합니다!**"""
    
    def _create_user_prompt(self, request: GenerationRequest) -> str:
        """Create user prompt for AI."""
        image_instructions = ""
        if request.include_images:
            image_instructions = "3. 관련 이미지 3-5개를 찾아서 포함하세요 (Unsplash 또는 무료 이미지 사이트)\n"
        
        important_points = f"""1. HTML 태그 제외하고 순수 텍스트가 정확히 {request.word_count}단어가 되도록 작성하세요
2. HTML 버전과 마크다운 버전 모두 제공하세요
{image_instructions}4. HTML에는 인라인 스타일을 적용하세요
5. 제목은 빨간색(#e74c3c), 부제목은 파란색(#3498db), 소제목은 녹색(#27ae60)으로 
6. 본문은 진한 회색(#000000), 강조는 주황색(#e67e22)으로 색칠하세요
7. 완전한 HTML 구조로 작성하여 웹페이지에 바로 표시 가능하게 만드세요
8. 절대 흰색(#ffffff, #fff, white)이나 매우 밝은 색상은 사용하지 마세요
9. **반드시 관련페이지링크를 포함하세요**: 각 섹션에 "소제목 바로가기" 형태의 링크 버튼을 추가해야 합니다"""

        return f"""주어진 주제에 대해 브런치 스타일의 전문 블로그 글을 작성해주세요.

**블로그 제목**: {request.topic}

**작성 지침:**
{important_points}

**브런치 스타일 구성:**
1. **매력적인 제목** - 주제를 바탕으로 클릭하고 싶은 제목 생성
2. **흥미로운 인트로** (2~3문단) - 독자의 호기심을 자극하고 전체 내용을 미리보기
3. **체계적인 섹션 구분:**
   - 주제 개요/배경
   - 핵심 내용 (방법론, 단계별 설명 등)
   - 실전 활용법 또는 팁
   - 주의사항 또는 한계점
   - 결론 및 행동 유도
4. **시각적 요소** - 각 섹션에 어울리는 이미지 제안
5. **독자 친화적 요소** - 불릿포인트, 번호 목록, 강조 텍스트 활용
6. **관련페이지링크** - 각 섹션마다 관련 정보로 이동할 수 있는 "바로가기" 링크 버튼 포함

**톤 & 스타일:**
- {request.tone} 톤을 기본으로 하되, 친근하고 신뢰감 있는 어조 유지
- 전문성과 접근성의 균형
- 독자가 실제로 활용할 수 있는 구체적인 정보 제공

**목표 단어 수**: 정확히 {request.word_count}단어 (HTML 태그 제외, 순수 텍스트 기준)
브런치 스타일의 깔끔하고 체계적인 구조를 유지하면서 목표 단어 수를 정확히 맞춰주세요."""
    
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
        """Fix white or very light colored text in HTML content."""
        import re
        
        if not html_content:
            return html_content
        
        # Patterns to find white or very light colors
        white_patterns = [
            r'color:\s*#fff\b',
            r'color:\s*#ffffff\b', 
            r'color:\s*white\b',
            r'color:\s*#f[9-f]{5}\b',  # Very light colors like #fffff, #ffffe etc
            r'color:\s*#[ef][ef][ef][ef][ef][ef]\b',  # Very light hex colors
            r'color:\s*rgb\(\s*25[0-5],\s*25[0-5],\s*25[0-5]\s*\)',  # RGB white/near-white
        ]
        
        # Default replacement color (black)
        replacement_color = '#000000'
        
        # Replace all white/light colors
        fixed_html = html_content
        for pattern in white_patterns:
            fixed_html = re.sub(pattern, f'color: {replacement_color}', fixed_html, flags=re.IGNORECASE)
        
        return fixed_html
    
    def _add_section_links(self, html_content: str) -> str:
        """Add section navigation links after each H2 or H3 heading."""
        import re
        
        if not html_content:
            return html_content
        
        print("DEBUG: Starting _add_section_links")
        
        # Link button template
        link_template = '<a href="#" style="color: #3498db; text-decoration: none; font-weight: 600; border: 1px solid #3498db; padding: 8px 16px; border-radius: 4px; display: inline-block; margin: 10px 0;">{} 바로가기</a>'
        
        # Find all H2 and H3 headings and add links after them
        def add_link_after_heading(match):
            full_heading = match.group(0)
            print(f"DEBUG: Found heading: {full_heading[:50]}...")
            # Extract heading text (remove HTML tags)
            heading_text = re.sub(r'<[^>]+>', '', full_heading).strip()
            # Truncate if too long
            if len(heading_text) > 20:
                heading_text = heading_text[:17] + "..."
            
            print(f"DEBUG: Extracted text: '{heading_text}'")
            
            # Create link button
            link_button = link_template.format(heading_text)
            print(f"DEBUG: Created link button")
            
            return full_heading + '\n' + link_button
        
        # Pattern to match H2 and H3 headings
        heading_pattern = r'<h[23][^>]*>.*?</h[23]>'
        
        # Count matches before processing
        matches = re.findall(heading_pattern, html_content, flags=re.IGNORECASE | re.DOTALL)
        print(f"DEBUG: Found {len(matches)} heading matches")
        
        # Add links after each heading
        enhanced_html = re.sub(heading_pattern, add_link_after_heading, html_content, flags=re.IGNORECASE | re.DOTALL)
        
        # Count links added
        links_added = enhanced_html.count('바로가기')
        print(f"DEBUG: Added {links_added} links")
        
        return enhanced_html