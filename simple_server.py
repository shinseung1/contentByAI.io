#!/usr/bin/env python3
"""
Mac용 간단한 서버 시작 스크립트
"""

import os
import sys
import uvicorn

# 현재 디렉토리 확인
print(f"📍 현재 위치: {os.getcwd()}")

# 필요한 파일들 확인
required_files = ['.env', 'api_test_endpoint.py', 'database.py']
missing_files = []

for file in required_files:
    if os.path.exists(file):
        print(f"✅ {file} 확인됨")
    else:
        print(f"❌ {file} 없음")
        missing_files.append(file)

if missing_files:
    print(f"❌ 누락된 파일들: {missing_files}")
    sys.exit(1)

# 환경 변수 로드 테스트
try:
    from dotenv import load_dotenv
    load_dotenv()
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        print(f"✅ GEMINI_API_KEY: {gemini_key[:20]}...")
    else:
        print("⚠️  GEMINI_API_KEY가 설정되지 않음")
        
except Exception as e:
    print(f"❌ 환경 변수 로드 실패: {e}")

# 데이터베이스 초기화
try:
    print("🗄️  데이터베이스 초기화 중...")
    from database import db
    print("✅ 데이터베이스 초기화 완료")
except Exception as e:
    print(f"❌ 데이터베이스 초기화 실패: {e}")

# 서버 시작
try:
    print("🚀 서버 시작 중...")
    print("📍 접속 URL:")
    print("   - API 서버: http://127.0.0.1:8000")
    print("   - API 문서: http://127.0.0.1:8000/docs")
    print("   - 헬스체크: http://127.0.0.1:8000/api/v1/health/")
    print()
    print("🛑 서버 중지: Ctrl+C")
    print("=" * 50)
    
    # API 모듈 import
    from api_test_endpoint import app
    
    # uvicorn으로 서버 시작
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=3000,
        log_level="info",
        access_log=True
    )
    
except KeyboardInterrupt:
    print("\n🛑 서버가 중지되었습니다.")
except Exception as e:
    print(f"❌ 서버 시작 실패: {e}")
    print("\n디버깅 정보:")
    print(f"Python 경로: {sys.executable}")
    print(f"Python 버전: {sys.version}")
    import traceback
    traceback.print_exc()