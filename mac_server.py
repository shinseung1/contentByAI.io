#!/usr/bin/env python3
"""
Mac용 서버 - 포트 8080 사용
"""

import uvicorn
import os

if __name__ == "__main__":
    print("🍎 Mac에서 AI Writer API 서버 시작")
    print("=" * 50)
    
    # 환경 확인
    from dotenv import load_dotenv
    load_dotenv()
    
    # API 모듈 임포트
    from api_test_endpoint import app
    
    print("📍 접속 URL:")
    print("   - API 서버: http://localhost:3001")  
    print("   - API 문서: http://localhost:3001/docs")
    print("   - 헬스체크: http://localhost:3001/api/v1/health/")
    print("   - Safari/Chrome에서 위 URL들을 열어보세요!")
    print()
    print("🛑 서버 중지: Ctrl+C")
    print("=" * 50)
    
    # 포트 3001로 서버 시작
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=3001,       # 3001 포트 사용
        log_level="info",
        reload=False
    )