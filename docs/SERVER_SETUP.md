# 파이썬 서버 실행 가이드

AI 콘텐츠 생성 시스템의 FastAPI 서버를 실행하는 방법을 안내합니다.

## 시스템 요구사항

- **Python**: 3.11+ (현재 테스트된 버전: 3.13.7)
- **운영체제**: Windows, macOS, Linux
- **포트**: 3000 (기본값, 변경 가능)

## 1. 프로젝트 설치

### 의존성 설치

```bash
# 프로젝트 디렉토리로 이동
cd CreateAutoContentByAi

# 패키지 설치 (편집 가능 모드)
pip install -e .
```

### 설치 확인

```bash
# Python 버전 확인
python --version
# 출력: Python 3.13.7

# 패키지 설치 확인
python -c "import fastapi; print('FastAPI 설치 완료!')"
```

## 2. 환경 변수 설정

### API 키 설정

```bash
# .env 파일 생성
cp .env.example .env
```

`.env` 파일에서 최소한 하나의 AI API 키를 설정:

```env
# OpenAI API (권장 - 가장 안정적)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o

# 기본 설정
PRIMARY_AI_PROVIDER=openai
AI_FALLBACK_ENABLED=true
AI_MAX_TOKENS=4000
AI_TEMPERATURE=0.7
```

## 3. 서버 실행

### 기본 실행 방법

```bash
# 개발 서버 시작 (자동 리로드 포함)
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 3000 --reload
```

### 실행 성공 확인

서버가 정상 시작되면 다음과 같은 메시지가 표시됩니다:

```
INFO:     Will watch for changes in these directories: ['C:\갠프\tstoryAi\CreateAutoContentByAi']
INFO:     Uvicorn running on http://127.0.0.1:3000 (Press CTRL+C to quit)
INFO:     Started reloader process [5352] using WatchFiles
INFO:     Started server process [31272]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 데이터베이스 초기화 확인

서버 시작 시 자동으로 SQLite 데이터베이스와 테이블이 생성됩니다:

```
INFO:     Application startup complete.
# 데이터베이스 파일 생성: data/aiwriter.db
# 테이블 생성: generation_jobs, publish_jobs
```

## 4. 서버 테스트

### 1. 헬스 체크

```bash
# 서버 상태 확인
curl "http://127.0.0.1:3000/api/v1/health/"

# 예상 응답:
# {"status":"healthy","version":"0.1.0","environment":"dev"}
```

### 2. API 문서 확인

**웹 브라우저에서 접속:**
- API 문서: http://127.0.0.1:3000/docs
- OpenAPI 스펙: http://127.0.0.1:3000/openapi.json

### 3. 콘텐츠 생성 테스트

```bash
# JSON 요청 파일 생성
cat > test_request.json << EOF
{
  "topic": "인공지능의 미래",
  "tone": "professional",
  "word_count": 500,
  "include_images": true,
  "target_language": "ko"
}
EOF

# 콘텐츠 생성 요청
curl -X POST "http://127.0.0.1:3000/api/v1/generation/generate" \
     -H "Content-Type: application/json" \
     -d @test_request.json

# 예상 응답:
# {"job_id":"abc-123","status":"started","message":"Content generation started"}
```

### 4. 작업 상태 확인

```bash
# job_id를 실제 응답 값으로 교체
curl "http://127.0.0.1:3000/api/v1/generation/jobs/{job_id}"

# 예상 응답 (진행 중):
# {"job_id":"abc-123","status":"in_progress","message":"Generating content...","progress":0.5}

# 예상 응답 (완료):
# {"job_id":"abc-123","status":"completed","message":"Content generation completed","content":{...}}
```

## 5. 다양한 실행 옵션

### 개발 환경

```bash
# 자동 리로드 + 디버그 로그
LOG_LEVEL=DEBUG python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 3000 --reload

# 특정 포트 사용
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8080 --reload
```

### 프로덕션 환경

```bash
# 프로덕션 모드 (리로드 없음)
python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 3000

# 워커 프로세스 사용
python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 3000 --workers 4
```

### Docker 실행

```bash
# Docker 개발 환경
docker-compose -f docker-compose.dev.yml up

# Docker 프로덕션 환경  
docker-compose up
```

## 6. 문제 해결

### 일반적인 오류

#### 1. 포트 이미 사용 중

```bash
# 다른 포트 사용
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8080
```

#### 2. API 키 오류

```bash
# 환경 변수 확인
python -c "import os; print('OPENAI_API_KEY:', os.getenv('OPENAI_API_KEY')[:10] + '...' if os.getenv('OPENAI_API_KEY') else 'Not set')"
```

#### 3. 의존성 오류

```bash
# 의존성 재설치
pip install -e . --force-reinstall

# 특정 패키지 재설치
pip install --upgrade fastapi uvicorn
```

#### 4. 데이터베이스 오류

```bash
# data 디렉토리 확인/생성
mkdir -p data
ls -la data/

# 데이터베이스 파일 권한 확인
ls -la data/aiwriter.db
```

### 디버깅 방법

#### 1. 로그 레벨 조정

```bash
# .env 파일에 추가
LOG_LEVEL=DEBUG

# 또는 환경변수로 실행
LOG_LEVEL=DEBUG python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 3000
```

#### 2. 상세 로그 확인

```bash
# uvicorn 로그 레벨 조정
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 3000 --log-level debug
```

#### 3. 모듈 import 테스트

```bash
# 개별 모듈 테스트
python -c "from apps.api.main import app; print('Import 성공!')"
python -c "from packages.ai_clients import AIClientFactory; print('AI Client 성공!')"
python -c "from packages.gen import ContentGenerator; print('Generator 성공!')"
```

## 7. 성능 최적화

### 개발 환경

```bash
# 빠른 재시작을 위한 설정
python -m uvicorn apps.api.main:app \
  --host 127.0.0.1 \
  --port 3000 \
  --reload \
  --reload-dir apps \
  --reload-dir packages
```

### 프로덕션 환경

```bash
# Gunicorn 사용 (Linux/macOS)
pip install gunicorn
gunicorn apps.api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:3000

# Windows에서는 uvicorn 사용
python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 3000 --workers 1
```

## 8. 환경별 설정

### 개발 환경 (.env)

```env
APP_ENV=dev
LOG_LEVEL=DEBUG
API_HOST=127.0.0.1
API_PORT=3000
DATABASE_URL=sqlite:///./data/aiwriter.db
```

### 프로덕션 환경

```env
APP_ENV=prod
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=80
DATABASE_URL=postgresql://user:pass@localhost/aiwriter
```

## 9. 모니터링

### 서버 상태 확인

```bash
# 헬스 체크
curl "http://127.0.0.1:3000/api/v1/health/"

# 작업 목록 확인
curl "http://127.0.0.1:3000/api/v1/generation/jobs"

# 번들 목록 확인
curl "http://127.0.0.1:3000/api/v1/bundles/"
```

### 로그 모니터링

```bash
# 실시간 로그 확인 (Linux/macOS)
tail -f logs/app.log

# Windows PowerShell
Get-Content logs/app.log -Wait
```

## 10. 종료 방법

### 개발 서버 종료

```bash
# Ctrl+C 또는
# Windows: Ctrl+Break
```

### 백그라운드 프로세스 종료

```bash
# 프로세스 ID 확인
ps aux | grep uvicorn

# 프로세스 종료
kill <process_id>

# Windows
tasklist | findstr python
taskkill /PID <process_id> /F
```

## 11. 테스트 실행

### 단위 테스트

```bash
# 모든 테스트 실행
python -m pytest

# 특정 테스트 실행
python -m pytest tests/test_ai_clients.py -v

# 커버리지 포함
python -m pytest --cov=packages tests/
```

### API 테스트

```bash
# Swagger UI에서 테스트
# http://127.0.0.1:3000/docs 접속 후 "Try it out" 사용

# curl로 전체 API 테스트
bash scripts/test_api.sh  # (스크립트 파일이 있다면)
```

## 요약

1. **설치**: `pip install -e .`
2. **설정**: `.env` 파일에 API 키 설정
3. **실행**: `python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 3000 --reload`
4. **확인**: http://127.0.0.1:3000/docs 접속
5. **테스트**: API 엔드포인트로 요청 전송

**🎉 서버가 정상 실행되면 AI 콘텐츠 생성 시스템을 사용할 수 있습니다!**