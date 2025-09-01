# AI Writer 파이썬 서버 설정 및 실행 가이드

## 📋 시스템 요구사항

- **Python**: 3.9 이상 (권장: 3.11+)
- **운영체제**: macOS, Linux, Windows
- **메모리**: 최소 2GB RAM
- **디스크**: 최소 1GB 여유 공간

## 🛠️ 설치 및 설정

### 1. 의존성 설치

프로젝트 루트 디렉토리에서 다음 명령어를 실행하세요:

```bash
# requirements.txt를 사용한 일괄 설치
pip3 install -r requirements.txt

# 또는 개별 설치
pip3 install fastapi uvicorn httpx pydantic python-dotenv
```

### 2. 환경 변수 설정

`.env` 파일이 올바르게 설정되어 있는지 확인하세요:

```bash
# .env 파일 확인
cat .env

# 필수 설정 항목들:
# - GEMINI_API_KEY (테스트 완료)
# - CLAUDE_API_KEY (선택사항)
# - OPENAI_API_KEY (선택사항) 
# - GROK_API_KEY (선택사항)
```

### 3. 데이터베이스 초기화

```bash
# SQLite 데이터베이스 및 테이블 생성
python3 database.py
```

예상 출력:
```
🗄️  데이터베이스 초기화 중...
✅ 데이터베이스 초기화 완료!
📊 저장된 테스트 결과: 2개
📈 gemini: 1회 테스트, 100.0% 성공률
```

## 🚀 서버 실행 방법

### 방법 1: 직접 실행 (개발/테스트용)

```bash
# 기본 실행
python3 api_test_endpoint.py

# 출력 예시:
# 🚀 AI Writer API 테스트 서버 시작
# 📍 API 문서: http://127.0.0.1:8000/docs
# 🔗 프론트엔드: http://127.0.0.1:3000
```

### 방법 2: uvicorn 직접 실행 (권장)

```bash
# 개발 모드 (자동 재시작)
uvicorn api_test_endpoint:app --reload --host 127.0.0.1 --port 8000

# 프로덕션 모드
uvicorn api_test_endpoint:app --host 0.0.0.0 --port 8000 --workers 4
```

### 방법 3: 백그라운드 실행

```bash
# 백그라운드에서 실행
nohup python3 api_test_endpoint.py > server.log 2>&1 &

# 프로세스 확인
ps aux | grep api_test_endpoint

# 로그 확인
tail -f server.log
```

## 🔍 서버 상태 확인

### 1. 헬스체크

```bash
# 서버 상태 확인
curl http://127.0.0.1:8000/api/v1/health/

# 예상 응답:
# {
#   "status": "healthy",
#   "version": "1.0.0", 
#   "environment": "development"
# }
```

### 2. API 문서 접속

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## 🧪 API 테스트

### 1. Gemini API 테스트

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/test/ai" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "gemini",
    "prompt": "안녕하세요! 간단한 인사말로 답해주세요."
  }'
```

### 2. 콘텐츠 생성 테스트

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/generation/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "gemini",
    "topic": "인공지능의 미래",
    "tone": "professional",
    "wordCount": 800
  }'
```

### 3. 테스트 결과 조회

```bash
# Gemini 테스트 결과 조회
curl "http://127.0.0.1:8000/api/v1/test-results/gemini?limit=10"

# Gemini 통계 조회  
curl "http://127.0.0.1:8000/api/v1/provider-stats/gemini"
```

## 📊 사용 가능한 API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|------------|---------|------|
| `/api/v1/health/` | GET | 서버 상태 확인 |
| `/api/v1/test/ai` | POST | AI API 테스트 |
| `/api/v1/test-results/{provider}` | GET | 테스트 결과 조회 |
| `/api/v1/provider-stats/{provider}` | GET | 제공자별 통계 |
| `/api/v1/generation/generate` | POST | 콘텐츠 생성 시작 |
| `/api/v1/generation/jobs/{job_id}` | GET | 작업 상태 조회 |
| `/api/v1/generation/jobs` | GET | 생성 작업 목록 |

## 🔧 문제 해결

### 1. 포트 충돌

```bash
# 8000번 포트 사용 중인 프로세스 확인
lsof -i :8000

# 프로세스 종료
kill -9 <PID>

# 다른 포트로 실행
uvicorn api_test_endpoint:app --port 8001
```

### 2. 의존성 오류

```bash
# pip 업그레이드
python3 -m pip install --upgrade pip

# 의존성 재설치
pip3 install -r requirements.txt --force-reinstall
```

### 3. 데이터베이스 오류

```bash
# 데이터베이스 파일 삭제 후 재생성
rm -f data/aiwriter.db
python3 database.py
```

### 4. API 키 오류

```bash
# 환경 변수 확인
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f'GEMINI_API_KEY: {os.getenv(\"GEMINI_API_KEY\", \"NOT_SET\")[:20]}...')"
```

## 🌐 웹 프론트엔드 연동

서버가 실행된 후 React 프론트엔드에서 접속:

```bash
# 웹 디렉토리로 이동
cd web

# 의존성 설치 (처음만)
npm install

# 개발 서버 시작
npm run dev

# 브라우저에서 접속
# - 메인 대시보드: http://localhost:3000
# - Gemini 페이지: http://localhost:3000/gemini
# - Claude 페이지: http://localhost:3000/claude
# - OpenAI 페이지: http://localhost:3000/openai
# - Grok 페이지: http://localhost:3000/grok
```

## 📝 로그 및 모니터링

### 로그 파일 위치

- **애플리케이션 로그**: `logs/`
- **실행 로그**: `runs/`
- **데이터베이스**: `data/aiwriter.db`

### 로그 확인

```bash
# 최근 로그 확인
tail -f logs/*.log

# 실행 기록 확인
ls -la runs/

# 데이터베이스 직접 확인
sqlite3 data/aiwriter.db "SELECT * FROM test_results LIMIT 5;"
```

## ⚙️ 서버 설정 옵션

### 환경 변수

```bash
# 개발/프로덕션 환경 설정
APP_ENV=development  # 또는 production

# 서버 호스트/포트
API_HOST=127.0.0.1
API_PORT=8000

# CORS 설정
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# 로그 레벨
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

## 🔒 보안 고려사항

1. **API 키 보안**: `.env` 파일을 git에 커밋하지 마세요
2. **방화벽**: 프로덕션에서는 필요한 포트만 열어두세요
3. **HTTPS**: 프로덕션에서는 리버스 프록시(nginx)를 사용하세요

---

## 🎉 성공적인 설치 확인

모든 설정이 완료되면 다음이 정상 작동해야 합니다:

✅ **서버 시작**: `python3 api_test_endpoint.py`  
✅ **헬스체크**: http://127.0.0.1:8000/api/v1/health/  
✅ **API 문서**: http://127.0.0.1:8000/docs  
✅ **Gemini 테스트**: API를 통한 실제 응답  
✅ **데이터베이스**: 테스트 결과 저장 및 조회  

문제가 발생하면 위의 문제 해결 섹션을 참고하거나 로그를 확인해주세요! 🚀