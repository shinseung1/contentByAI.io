#!/usr/bin/env python3
"""
Mac용 테스트 서버 - 기본 기능만
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

# FastAPI 앱 생성
app = FastAPI(title="AI Writer Test Server", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "AI Writer 테스트 서버", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "environment": "test"}

@app.get("/api/v1/health/")
async def health_v1():
    return {"status": "healthy", "version": "1.0.0", "environment": "development"}

@app.post("/api/v1/test/ai")
async def test_ai():
    return {
        "success": True,
        "message": "테스트 서버 응답",
        "provider": "test",
        "content": "안녕하세요! 테스트 서버가 정상 작동 중입니다.",
        "timestamp": "2024-01-01T12:00:00Z"
    }

if __name__ == "__main__":
    print("🧪 AI Writer 테스트 서버 시작")
    print("=" * 50)
    print("📍 접속 URL:")
    print("   - 메인: http://localhost:3001")
    print("   - 헬스체크: http://localhost:3001/health")
    print("   - API 헬스체크: http://localhost:3001/api/v1/health/")
    print("   - API 문서: http://localhost:3001/docs")
    print()
    print("🛑 서버 중지: Ctrl+C")
    print("=" * 50)
    
    try:
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=3001,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ 서버 시작 오류: {e}")
        print("다른 포트를 시도합니다...")
        
        # 3002 포트로 재시도
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=3002,
            log_level="info"
        )