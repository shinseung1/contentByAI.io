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
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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
        session = LoginSession(
            token=token,
            username=user.username,
            expires_at=expires_at.isoformat(),
            created_at=datetime.now().isoformat()
        )
        
        success = db.create_session(session)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to create session"
            )
        
        # 로그인 시도 횟수 초기화
        db.reset_failed_attempts(user.username)
        
        return LoginResponse(
            success=True,
            message="로그인 성공",
            token=token,
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
async def get_job_status(job_id: str):
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
async def get_generation_jobs(provider: Optional[str] = None, limit: int = 50):
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
        
        # AI API 호출하여 콘텐츠 생성
        prompt = f"""다음 주제에 대해 {job.tone} 톤으로 약 {job.word_count}자 분량의 한국어 콘텐츠를 생성해주세요:

주제: {job.topic}

요구사항:
- 톤앤매너: {job.tone}
- 목표 분량: {job.word_count}자
- 언어: {job.target_language}
- 구조화된 내용으로 작성
- SEO 최적화를 고려한 내용 포함
"""
        
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
        
        # 생성 완료
        db.update_generation_job_status(
            job_id, 
            "completed", 
            100, 
            content=result["content"]
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
    print(f"📍 API 문서: http://127.0.0.1:8000/docs")
    print(f"🔗 프론트엔드: http://127.0.0.1:3000")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=True
    )