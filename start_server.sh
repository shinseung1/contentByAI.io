#!/bin/bash

echo "🚀 AI Writer API 서버 시작 중..."

# 현재 디렉토리 확인
echo "📍 현재 위치: $(pwd)"

# Python 버전 확인
echo "🐍 Python 버전: $(python3 --version)"

# 필요한 파일들 확인
echo "📁 파일 확인:"
ls -la api_test_endpoint.py database.py .env

# 의존성 확인
echo "📦 의존성 확인:"
python3 -c "import fastapi, uvicorn, httpx; print('✅ 모든 의존성 확인됨')" || echo "❌ 의존성 설치 필요"

# 데이터베이스 초기화
echo "🗄️  데이터베이스 초기화..."
python3 database.py

# 서버 시작
echo "🌐 서버 시작 (Ctrl+C로 중지)..."
python3 -c "
import uvicorn
from api_test_endpoint import app

print('📍 접속 URL:')
print('   - API 서버: http://127.0.0.1:8000')
print('   - API 문서: http://127.0.0.1:8000/docs')
print('   - 헬스체크: http://127.0.0.1:8000/api/v1/health/')
print()

uvicorn.run(app, host='127.0.0.1', port=8000, log_level='info')
"