#!/usr/bin/env python3
"""
웹에서 사용할 수 있는 API 테스트 엔드포인트 (실제 데이터 연동)
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import asyncio
import httpx
from dotenv import load_dotenv
import uvicorn
import time
import uuid
import secrets
from datetime import datetime, timedelta
from database import db, TestResult, GenerationJob, User, LoginSession

# .env 파일 로드
load_dotenv()

app = FastAPI(title="AI Writer API Tester", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 인증 설정
security = HTTPBearer()

# 요청/응답 모델
class TestRequest(BaseModel):
    provider: str
    prompt: Optional[str] = "안녕하세요! 간단한 인사말로 답해주세요."

class TestResponse(BaseModel):
    success: bool
    provider: str
    content: Optional[str] = None
    tokenUsage: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str

class GenerationRequest(BaseModel):
    provider: str
    topic: str
    tone: Optional[str] = "professional"
    wordCount: Optional[int] = 800
    includeImages: Optional[bool] = True
    targetLanguage: Optional[str] = "ko"

class GenerationResponse(BaseModel):
    jobId: str
    status: str
    message: str

class JobStatusResponse(BaseModel):
    jobId: str
    status: str
    progress: Optional[int] = 0
    result: Optional[Dict[str, Any]] = None
    errorMessage: Optional[str] = None
    errorCode: Optional[str] = None

class ProviderStatsResponse(BaseModel):
    totalTests: int
    successfulTests: int
    failedTests: int
    successRate: float
    avgResponseTime: float
    lastTestAt: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str

# 인증 관련 모델
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None

class AuthValidateResponse(BaseModel):
    valid: bool
    user: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

# API 키 설정
AI_CONFIGS = {
    "gemini": {
        "api_key": os.getenv("GEMINI_API_KEY"),
        "model": os.getenv("GEMINI_MODEL", "gemini-1.5-pro"),
        "url_template": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    },
    "claude": {
        "api_key": os.getenv("CLAUDE_API_KEY"),
        "model": os.getenv("CLAUDE_MODEL", "claude-3-sonnet-20240229"),
        "url": "https://api.anthropic.com/v1/messages"
    },
    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
        "url": "https://api.openai.com/v1/chat/completions"
    },
    "grok": {
        "api_key": os.getenv("GROK_API_KEY"),
        "model": os.getenv("GROK_MODEL", "grok-beta"),
        "url": "https://api.x.ai/v1/chat/completions"
    }
}

# 인증 함수들
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """현재 인증된 사용자 반환"""
    token = credentials.credentials
    session = db.get_session_by_token(token)
    
    if not session:
        raise HTTPException(
            status_code=401, 
            detail="Invalid or expired session token"
        )
    
    # 세션 만료 확인
    if session.expires_at < datetime.now().isoformat():
        db.delete_session(token)
        raise HTTPException(
            status_code=401, 
            detail="Session has expired"
        )
    
    user = db.get_user_by_username(session.username)
    if not user:
        raise HTTPException(
            status_code=401, 
            detail="User not found"
        )
    
    return user

def generate_session_token() -> str:
    """세션 토큰 생성"""
    return secrets.token_urlsafe(32)

def convert_text_to_html(content: str, job, image_urls: list) -> str:
    """텍스트 콘텐츠를 HTML로 변환"""
    import re
    
    # HTML 템플릿 시작
    html = f"""<!DOCTYPE html>
<html lang="{job.target_language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{job.topic}</title>
    <meta name="description" content="{content[:150]}...">
    <meta name="author" content="Noaats AI">
    <style>
        body {{ margin: 0; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; line-height: 1.6; color: #333; }}
        article {{ max-width: 800px; margin: 0 auto; }}
        h1 {{ font-size: 2.2em; font-weight: 700; color: #1a1a1a; margin-bottom: 0.5em; }}
        h2 {{ font-size: 1.6em; font-weight: 600; color: #2c3e50; margin: 1.5em 0 0.8em; }}
        h3 {{ font-size: 1.3em; font-weight: 500; color: #34495e; margin: 1.2em 0 0.6em; }}
        p {{ margin-bottom: 1.2em; line-height: 1.7; font-size: 15px; color: #333; }}
        ul, ol {{ margin-bottom: 1.2em; padding-left: 1.5em; }}
        li {{ margin-bottom: 0.5em; }}
        figure {{ margin: 2em 0; text-align: center; }}
        img {{ max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
        figcaption {{ margin-top: 0.8em; font-style: italic; color: #666; font-size: 14px; }}
        strong {{ font-weight: 600; }}
        em {{ font-style: italic; }}
    </style>
</head>
<body>
<article>"""
    
    # 제목 추가
    html += f"<h1>{job.topic}</h1>\n"
    
    # 이미지 카운터
    img_counter = 0
    
    # 텍스트를 HTML로 변환
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 마크다운 헤딩을 HTML로 변환
        if line.startswith('## '):
            title = line.replace('## ', '')
            html += f"<h2>{title}</h2>\n"
            # 이미지 추가
            if job.include_images and img_counter < len(image_urls):
                html += f'''<figure>
    <img src="{image_urls[img_counter]}" alt="{title} 관련 이미지" width="1200" height="675">
    <figcaption>{title} 관련 이미지</figcaption>
</figure>\n'''
                img_counter += 1
        elif line.startswith('### '):
            html += f"<h3>{line.replace('### ', '')}</h3>\n"
        elif line.startswith('# '):
            html += f"<h1>{line.replace('# ', '')}</h1>\n"
        elif line.startswith('- ') or line.startswith('* '):
            # 리스트 처리 (간단하게)
            html += f"<p>• {line[2:]}</p>\n"
        elif line.startswith('**') and line.endswith('**'):
            # 굵은 글씨
            html += f"<p><strong>{line[2:-2]}</strong></p>\n"
        else:
            # 일반 문단
            if line:
                html += f"<p>{line}</p>\n"
    
    html += """</article>
</body>
</html>"""
    
    return html

async def test_gemini_api(prompt: str) -> Dict[str, Any]:
    """Gemini API 테스트"""
    config = AI_CONFIGS["gemini"]
    if not config["api_key"]:
        raise HTTPException(status_code=400, detail="Gemini API 키가 설정되지 않았습니다")
    
    url = config["url_template"].format(
        model=config["model"],
        api_key=config["api_key"]
    )
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1000,
        }
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            
            if "candidates" in result and len(result["candidates"]) > 0:
                content = result["candidates"][0]["content"]["parts"][0]["text"]
                token_usage = result.get("usageMetadata", {})
                
                return {
                    "success": True,
                    "content": content,
                    "tokenUsage": token_usage
                }
            else:
                raise HTTPException(status_code=500, detail="응답에 콘텐츠가 없습니다")
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            raise HTTPException(status_code=response.status_code, detail=f"API 호출 실패: {error_data}")

async def test_claude_api(prompt: str) -> Dict[str, Any]:
    """Claude API 테스트"""
    config = AI_CONFIGS["claude"]
    if not config["api_key"]:
        raise HTTPException(status_code=400, detail="Claude API 키가 설정되지 않았습니다")
    
    headers = {
        "x-api-key": config["api_key"],
        "content-type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    payload = {
        "model": config["model"],
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(config["url"], json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            content = result["content"][0]["text"]
            
            return {
                "success": True,
                "content": content,
                "tokenUsage": {
                    "promptTokenCount": result["usage"]["input_tokens"],
                    "candidatesTokenCount": result["usage"]["output_tokens"],
                    "totalTokenCount": result["usage"]["input_tokens"] + result["usage"]["output_tokens"]
                }
            }
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            raise HTTPException(status_code=response.status_code, detail=f"API 호출 실패: {error_data}")

async def test_openai_api(prompt: str) -> Dict[str, Any]:
    """OpenAI API 테스트"""
    config = AI_CONFIGS["openai"]
    if not config["api_key"]:
        raise HTTPException(status_code=400, detail="OpenAI API 키가 설정되지 않았습니다")
    
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": config["model"],
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(config["url"], json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            return {
                "success": True,
                "content": content,
                "tokenUsage": {
                    "promptTokenCount": result["usage"]["prompt_tokens"],
                    "candidatesTokenCount": result["usage"]["completion_tokens"],
                    "totalTokenCount": result["usage"]["total_tokens"]
                }
            }
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            raise HTTPException(status_code=response.status_code, detail=f"API 호출 실패: {error_data}")

async def test_grok_api(prompt: str) -> Dict[str, Any]:
    """Grok API 테스트"""
    config = AI_CONFIGS["grok"]
    if not config["api_key"]:
        raise HTTPException(status_code=400, detail="Grok API 키가 설정되지 않았습니다")
    
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": config["model"],
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(config["url"], json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            return {
                "success": True,
                "content": content,
                "tokenUsage": {
                    "promptTokenCount": result["usage"]["prompt_tokens"],
                    "candidatesTokenCount": result["usage"]["completion_tokens"],
                    "totalTokenCount": result["usage"]["total_tokens"]
                }
            }
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            raise HTTPException(status_code=response.status_code, detail=f"API 호출 실패: {error_data}")

# API 엔드포인트
@app.get("/api/v1/health/", response_model=HealthResponse)
async def health_check():
    """시스템 상태 확인"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        environment=os.getenv("APP_ENV", "development")
    )

# 인증 API 엔드포인트
@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """로그인"""
    try:
        # 사용자 인증
        is_valid, user, error_message = db.verify_user_password(request.username, request.password)
        
        if not is_valid:
            return LoginResponse(
                success=False,
                message=error_message
            )
        
        # 세션 토큰 생성
        token = generate_session_token()
        expires_at = datetime.now() + timedelta(hours=24)
        
        # 세션 저장
        session_token = db.create_session(
            user_id=user.id,
            ip_address=None,
            user_agent=None
        )
        
        if not session_token:
            raise HTTPException(
                status_code=500,
                detail="Failed to create session"
            )
        
        # 로그인 시도 횟수 초기화
        db.reset_failed_attempts(user.username)
        
        return LoginResponse(
            success=True,
            message="로그인 성공",
            token=session_token,
            user={
                "username": user.username,
                "role": user.role,
                "isActive": user.is_active,
                "expiresAt": user.expires_at
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.post("/api/v1/auth/logout")
async def logout(current_user: User = Depends(get_current_user), credentials: HTTPAuthorizationCredentials = Depends(security)):
    """로그아웃"""
    try:
        token = credentials.credentials
        db.delete_session(token)
        return {"success": True, "message": "로그아웃 되었습니다"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")

@app.get("/api/v1/auth/validate", response_model=AuthValidateResponse)
async def validate_token(current_user: User = Depends(get_current_user)):
    """토큰 유효성 검증"""
    try:
        return AuthValidateResponse(
            valid=True,
            user={
                "username": current_user.username,
                "role": current_user.role,
                "isActive": current_user.is_active,
                "expiresAt": current_user.expires_at
            }
        )
    except HTTPException:
        return AuthValidateResponse(
            valid=False,
            message="Invalid or expired token"
        )

@app.post("/api/v1/test/ai", response_model=TestResponse)
async def test_ai_api(request: TestRequest, current_user: User = Depends(get_current_user)):
    """AI API 테스트 (데이터베이스 저장) - 인증 필요"""
    start_time = time.time()
    timestamp = datetime.now().isoformat()
    
    try:
        if request.provider == "gemini":
            result = await test_gemini_api(request.prompt)
        elif request.provider == "claude":
            result = await test_claude_api(request.prompt)
        elif request.provider == "openai":
            result = await test_openai_api(request.prompt)
        elif request.provider == "grok":
            result = await test_grok_api(request.prompt)
        else:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 제공자: {request.provider}")
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # 데이터베이스에 결과 저장
        test_result = TestResult(
            provider=request.provider,
            prompt=request.prompt,
            response=result["content"],
            success=True,
            token_usage=result.get("tokenUsage"),
            response_time_ms=response_time_ms,
            created_at=timestamp
        )
        db.save_test_result(test_result)
        
        return TestResponse(
            success=True,
            provider=request.provider,
            content=result["content"],
            tokenUsage=result.get("tokenUsage"),
            timestamp=timestamp
        )
        
    except HTTPException as he:
        # 실패 결과도 데이터베이스에 저장
        response_time_ms = int((time.time() - start_time) * 1000)
        test_result = TestResult(
            provider=request.provider,
            prompt=request.prompt,
            response="",
            success=False,
            error_message=str(he.detail),
            response_time_ms=response_time_ms,
            created_at=timestamp
        )
        db.save_test_result(test_result)
        raise
    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        test_result = TestResult(
            provider=request.provider,
            prompt=request.prompt,
            response="",
            success=False,
            error_message=str(e),
            response_time_ms=response_time_ms,
            created_at=timestamp
        )
        db.save_test_result(test_result)
        
        return TestResponse(
            success=False,
            provider=request.provider,
            error=str(e),
            timestamp=timestamp
        )

# 새로운 API 엔드포인트들
@app.get("/api/v1/test-results/{provider}")
async def get_test_results(provider: str, limit: int = 50):
    """제공자별 테스트 결과 조회"""
    try:
        results = db.get_test_results(provider, limit)
        return [
            {
                "id": r.id,
                "provider": r.provider,
                "prompt": r.prompt,
                "response": r.response,
                "success": r.success,
                "errorMessage": r.error_message,
                "tokenUsage": r.token_usage,
                "responseTimeMs": r.response_time_ms,
                "createdAt": r.created_at
            }
            for r in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/provider-stats/{provider}", response_model=ProviderStatsResponse)
async def get_provider_stats(provider: str):
    """제공자별 통계 조회"""
    try:
        stats = db.get_provider_stats(provider)
        return ProviderStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/generation/generate", response_model=GenerationResponse)
async def generate_content(request: GenerationRequest, background_tasks: BackgroundTasks):
    """콘텐츠 생성 작업 시작"""
    job_id = f"gen_{uuid.uuid4().hex[:12]}"
    timestamp = datetime.now().isoformat()
    
    # 생성 작업을 데이터베이스에 저장
    generation_job = GenerationJob(
        job_id=job_id,
        provider=request.provider,
        topic=request.topic,
        tone=request.tone,
        word_count=request.wordCount,
        include_images=request.includeImages,
        target_language=request.targetLanguage,
        status="pending",
        progress=0,
        created_at=timestamp
    )
    
    try:
        db.save_generation_job(generation_job)
        
        # 백그라운드에서 실제 생성 작업 실행
        background_tasks.add_task(execute_generation_job, job_id)
        
        return GenerationResponse(
            jobId=job_id,
            status="started",
            message="Content generation started"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start generation: {str(e)}")

@app.get("/api/v1/generation/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, current_user: User = Depends(get_current_user)):
    """작업 상태 조회"""
    try:
        job = db.get_generation_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        response = JobStatusResponse(
            jobId=job.job_id,
            status=job.status,
            progress=job.progress
        )
        
        if job.status == "completed" and job.content:
            response.result = {
                "bundleId": f"bundle_{job.job_id}",
                "title": job.topic,
                "contentPreview": job.content[:200] + "..." if len(job.content) > 200 else job.content,
                "wordCount": len(job.content.split()) if job.content else 0,
                "imagesCount": 0,
                "seoScore": 85
            }
        elif job.status == "failed":
            response.errorMessage = job.error_message
            response.errorCode = "GENERATION_FAILED"
            
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/generation/jobs")
async def get_generation_jobs(provider: Optional[str] = None, limit: int = 50, current_user: User = Depends(get_current_user)):
    """콘텐츠 생성 작업 목록 조회"""
    try:
        jobs = db.get_generation_jobs(provider, limit=limit)
        return [
            {
                "jobId": j.job_id,
                "provider": j.provider,
                "topic": j.topic,
                "tone": j.tone,
                "wordCount": j.word_count,
                "status": j.status,
                "progress": j.progress,
                "content": j.content,
                "errorMessage": j.error_message,
                "createdAt": j.created_at
            }
            for j in jobs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def execute_generation_job(job_id: str):
    """백그라운드에서 실행되는 실제 콘텐츠 생성 작업"""
    try:
        job = db.get_generation_job(job_id)
        if not job:
            return
        
        # 작업 상태를 진행중으로 업데이트
        db.update_generation_job_status(job_id, "in_progress", 10)
        
        # AI API 호출하여 콘텐츠 생성 (creation guide 적용)
        include_images = "yes" if job.include_images else "no"
        
        # 무료 이미지 URL 목록 (Unsplash API 사용)
        image_base_urls = [
            "https://images.unsplash.com/photo-1556075798-4825dfaaf498?w=1200&h=675&fit=crop",  # 항공
            "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=1200&h=675&fit=crop", # 여행
            "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=1200&h=675&fit=crop", # 기술/AI
            "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1200&h=675&fit=crop", # 비즈니스
            "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=1200&h=675&fit=crop", # 팀워크
        ]
        
        prompt = f"""너는 블로그용 HTML 본문 생성기다. 아래 규칙을 정확히 지켜 순수 HTML만 출력하라. (코드펜스/추가 설명/주석 금지)

GLOBAL RULES:
1. HTML만 출력한다(마크다운/설명 금지).
2. 출력 언어는 {job.target_language}, 문체는 {job.tone}.
3. 글자수는 본문 텍스트(눈에 보이는 글자) 기준으로 {job.word_count}자 ±10% 범위를 맞춘다.
4. 제목은 <h1> 1개만 사용(문서 최상단).
5. 제목 바로 뒤에 목차를 넣는다. 구조는 정확히:
   <div class="table-of-contents">
     <h3>목차</h3>
     <ul>
       <li><a href="#섹션-id">섹션 제목</a></li>
     </ul>
   </div>
6. 본문은 h2(대제목)와 필요 시 h3(소제목)로 구분하고, 모든 h2/h3에 영문 소문자-하이픈 슬러그 형태의 id를 부여한다.
7. 이미지 포함 설정이 "{include_images}"면, 각 h2/h3 바로 아래에 아래 플레이스홀더 1개를 넣는다:
   <div class="image-placeholder" data-image-prompt="이 섹션을 시각화하는 상세 설명" data-image-search="검색 키워드">[여기에 주제와 관련된 이미지 삽입]</div>
8. 각 h2 섹션의 끝에는 다음 CTA 버튼을 중앙 정렬로 넣는다:
   <div class="cta-wrapper"><a class="cta-button" href="#" target="_blank" rel="noopener">더 알아보기</a></div>
9. 표/비교는 <table><thead><tr><th>… 형태로 작성한다. 단계 절차는 <ol><li> 사용.
10. 과도한 확정 표현은 피하고, 확인 어려운 수치는 일반화한다.
11. 출력은 아래 구조만 사용한다:
    <h1> → <div class="table-of-contents">…</div> → h2/h3 + 본문 + (이미지플레이스홀더 선택적) → 섹션 말미 CTA → … → 결론(간단 요약 2~3문장)

TASK: 
아래 파라미터를 반영하여, "{job.topic}"에 대한 HTML 본문을 생성하라.
- LANG: {job.target_language}
- TONE: {job.tone}
- CHAR_LIMIT: {job.word_count}
- INCLUDE_IMAGES: {include_images}

OUTPUT: 오직 HTML 본문만 출력한다. (코드펜스 없음)"""
        
        db.update_generation_job_status(job_id, "in_progress", 50)
        
        if job.provider == "gemini":
            result = await test_gemini_api(prompt)
        elif job.provider == "claude":
            result = await test_claude_api(prompt)
        elif job.provider == "openai":
            result = await test_openai_api(prompt)
        elif job.provider == "grok":
            result = await test_grok_api(prompt)
        else:
            raise Exception(f"지원하지 않는 제공자: {job.provider}")
        
        db.update_generation_job_status(job_id, "in_progress", 90)
        
        # AI가 이미 HTML을 생성했으므로 직접 사용
        html_content = result["content"]
        
        # HTML이 아닌 경우에만 변환 (백업용)
        if not html_content.strip().startswith('<') or not html_content.strip().endswith('>'):
            html_content = convert_text_to_html(result["content"], job, image_base_urls)
        
        # 생성 완료
        db.update_generation_job_status(
            job_id, 
            "completed", 
            100, 
            content=html_content
        )
        
    except Exception as e:
        db.update_generation_job_status(
            job_id, 
            "failed", 
            0, 
            error_message=str(e)
        )

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {"message": "AI Writer API Tester with Real Data", "docs_url": "/docs"}

if __name__ == "__main__":
    print("🚀 AI Writer API 테스트 서버 시작")
    print(f"📍 API 문서: http://127.0.0.1:3000/docs")
    print(f"🔗 프론트엔드: http://127.0.0.1:3001")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=3000,
        reload=True
    )