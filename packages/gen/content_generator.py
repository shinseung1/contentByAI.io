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


class ContentGenerator:
    """Content generator using AI APIs."""
    
    def __init__(self, jobs_dir: str = "runs/generation_jobs"):
        self.jobs_dir = Path(jobs_dir)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
    
    def create_job_id(self) -> str:
        """Create a unique job ID."""
        return str(uuid.uuid4())
    
    def get_job_file_path(self, job_id: str) -> Path:
        """Get the file path for a job."""
        return self.jobs_dir / f"{job_id}.json"
    
    def save_job_status(self, job_id: str, response: GenerationResponse) -> None:
        """Save job status to file."""
        job_file = self.get_job_file_path(job_id)
        with open(job_file, 'w', encoding='utf-8') as f:
            json.dump(response.model_dump(), f, ensure_ascii=False, indent=2)
    
    def get_job_result(self, job_id: str) -> GenerationResponse:
        """Get job result from file."""
        job_file = self.get_job_file_path(job_id)
        if not job_file.exists():
            raise FileNotFoundError(f"Job {job_id} not found")
        
        with open(job_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return GenerationResponse(**data)
    
    def list_jobs(self) -> List[str]:
        """List all job IDs."""
        return [f.stem for f in self.jobs_dir.glob("*.json")]
    
    async def generate_content_async(self, job_id: str, request: GenerationRequest) -> None:
        """Generate content asynchronously."""
        # Update status to in_progress
        response = GenerationResponse(
            job_id=job_id,
            status=GenerationStatus.IN_PROGRESS,
            message="Generating content...",
            progress=0.0,
            created_at=datetime.now().isoformat()
        )
        self.save_job_status(job_id, response)
        
        try:
            # Get AI client configuration
            ai_config = self._get_ai_config()
            if not ai_config:
                raise ValueError("No AI configuration found")
            
            provider, config = ai_config
            
            # Generate content using AI
            content = await self._generate_with_ai(provider, config, request)
            
            # Update status to completed
            response.status = GenerationStatus.COMPLETED
            response.message = "Content generation completed"
            response.progress = 1.0
            response.content = content
            response.completed_at = datetime.now().isoformat()
            
        except Exception as e:
            # Update status to failed
            response.status = GenerationStatus.FAILED
            response.message = "Content generation failed"
            response.error = str(e)
            response.completed_at = datetime.now().isoformat()
        
        self.save_job_status(job_id, response)
    
    def _get_ai_config(self) -> Optional[tuple[AIProvider, AIClientConfig]]:
        """Get AI configuration from environment."""
        # Try Claude first
        if os.getenv("CLAUDE_API_KEY"):
            config = AIClientConfig(
                api_key=os.getenv("CLAUDE_API_KEY"),
                model=os.getenv("CLAUDE_MODEL", "claude-3-sonnet-20240229"),
                max_tokens=int(os.getenv("AI_MAX_TOKENS", "4000")),
                temperature=float(os.getenv("AI_TEMPERATURE", "0.7"))
            )
            return AIProvider.CLAUDE, config
        
        # Try OpenAI
        if os.getenv("OPENAI_API_KEY"):
            config = AIClientConfig(
                api_key=os.getenv("OPENAI_API_KEY"),
                model=os.getenv("OPENAI_MODEL", "gpt-4o"),
                max_tokens=int(os.getenv("AI_MAX_TOKENS", "4000")),
                temperature=float(os.getenv("AI_TEMPERATURE", "0.7"))
            )
            return AIProvider.OPENAI, config
        
        # Try Gemini
        if os.getenv("GEMINI_API_KEY"):
            config = AIClientConfig(
                api_key=os.getenv("GEMINI_API_KEY"),
                model=os.getenv("GEMINI_MODEL", "gemini-1.5-pro"),
                max_tokens=int(os.getenv("AI_MAX_TOKENS", "4000")),
                temperature=float(os.getenv("AI_TEMPERATURE", "0.7"))
            )
            return AIProvider.GEMINI, config
        
        # Try Grok
        if os.getenv("GROK_API_KEY"):
            config = AIClientConfig(
                api_key=os.getenv("GROK_API_KEY"),
                model=os.getenv("GROK_MODEL", "grok-beta"),
                max_tokens=int(os.getenv("AI_MAX_TOKENS", "4000")),
                temperature=float(os.getenv("AI_TEMPERATURE", "0.7"))
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
        return self._parse_ai_response(response.content, request)
    
    def _create_system_prompt(self, request: GenerationRequest) -> str:
        """Create system prompt for AI."""
        language_instruction = ""
        if request.target_language == "ko":
            language_instruction = "모든 응답은 한국어로 작성해주세요."
        elif request.target_language == "en":
            language_instruction = "Please respond in English."
        
        return f"""당신은 전문적인 콘텐츠 작성자입니다. 주어진 주제에 대해 고품질의 블로그 글을 작성해야 합니다.

작성 요구사항:
- 톤: {request.tone}
- 목표 단어 수: 약 {request.word_count}단어
- 언어: {request.target_language}

{language_instruction}

응답 형식을 다음 JSON 구조로 제공해주세요:
{{
    "title": "매력적이고 SEO 친화적인 제목",
    "content": "본문 내용 (마크다운 형식)",
    "summary": "2-3문장의 요약",
    "tags": ["관련", "태그", "목록"]
}}

콘텐츠는 다음 요소를 포함해야 합니다:
- 매력적인 도입부
- 구조화된 본문 (제목, 부제목 사용)
- 실용적인 정보와 인사이트
- 자연스러운 결론"""
    
    def _create_user_prompt(self, request: GenerationRequest) -> str:
        """Create user prompt for AI."""
        return f"다음 주제에 대해 {request.tone} 톤으로 약 {request.word_count}단어의 블로그 글을 작성해주세요:\n\n주제: {request.topic}"
    
    def _parse_ai_response(self, ai_content: str, request: GenerationRequest) -> GeneratedContent:
        """Parse AI response into GeneratedContent."""
        try:
            # Try to extract JSON from the response
            start_idx = ai_content.find('{')
            end_idx = ai_content.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = ai_content[start_idx:end_idx]
                data = json.loads(json_str)
                
                return GeneratedContent(
                    title=data.get("title", f"Content about {request.topic}"),
                    content=data.get("content", ai_content),
                    summary=data.get("summary"),
                    tags=data.get("tags", []),
                    images=[]  # Images would be generated separately
                )
            else:
                # Fallback: treat entire response as content
                return GeneratedContent(
                    title=f"Content about {request.topic}",
                    content=ai_content,
                    summary=None,
                    tags=[],
                    images=[]
                )
                
        except json.JSONDecodeError:
            # Fallback: treat entire response as content
            return GeneratedContent(
                title=f"Content about {request.topic}",
                content=ai_content,
                summary=None,
                tags=[],
                images=[]
            )