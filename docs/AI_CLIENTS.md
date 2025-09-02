# AI Clients 사용 가이드

이 문서는 Claude API, ChatGPT, Gemini, Grok API 클라이언트의 설정 및 사용법을 설명합니다.

## 프로젝트 구조

```
packages/
├── ai_clients/              # AI API 클라이언트 패키지
│   ├── __init__.py
│   ├── models.py           # 공통 모델 및 타입
│   ├── base.py            # 베이스 클라이언트 클래스
│   ├── claude_client.py    # Claude API 클라이언트
│   ├── openai_client.py    # OpenAI/ChatGPT API 클라이언트
│   ├── gemini_client.py    # Google Gemini API 클라이언트
│   ├── grok_client.py      # Grok API 클라이언트
│   └── ai_factory.py       # 클라이언트 팩토리
├── gen/                    # 콘텐츠 생성 패키지
│   ├── __init__.py
│   ├── models.py          # 생성 요청/응답 모델
│   └── content_generator.py  # 콘텐츠 생성기
└── core/                   # 핵심 패키지
    ├── config.py          # 설정 관리
    └── database.py        # 데이터베이스 연결
```

## 설치 및 설정

### 1. 프로젝트 설치

```bash
# Python 3.11+ 필요 (Python 3.13 지원)
pip install -e .
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 API 키들을 설정하세요:

```bash
cp .env.example .env
```

`.env` 파일에서 다음 값들을 설정하세요:

```env
# 필수: 사용할 AI API 키들
CLAUDE_API_KEY=your_claude_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
GROK_API_KEY=your_grok_api_key_here

# 선택사항: 모델 설정
CLAUDE_MODEL=claude-3-sonnet-20240229
OPENAI_MODEL=gpt-4o
GEMINI_MODEL=gemini-1.5-pro
GROK_MODEL=grok-beta

# 선택사항: 기본 설정
PRIMARY_AI_PROVIDER=claude
AI_FALLBACK_ENABLED=true
AI_MAX_TOKENS=4000
AI_TEMPERATURE=0.7
```

### 2. API 키 획득 방법

#### Claude API (Anthropic)
1. [Anthropic Console](https://console.anthropic.com/)에서 회원가입
2. API Keys 섹션에서 새로운 키 생성
3. `CLAUDE_API_KEY`에 설정

#### OpenAI API (ChatGPT)
1. [OpenAI Platform](https://platform.openai.com/)에서 회원가입
2. API Keys 섹션에서 새로운 키 생성
3. `OPENAI_API_KEY`에 설정

#### Google Gemini API
1. [Google AI Studio](https://aistudio.google.com/)에서 API 키 생성
2. `GEMINI_API_KEY`에 설정

#### Grok API (X.AI)
1. [X.AI Console](https://console.x.ai/)에서 회원가입
2. API 키 생성
3. `GROK_API_KEY`에 설정

## 기본 사용법

### 1. 단일 클라이언트 사용

```python
import asyncio
import os
from packages.ai_clients import (
    AIClientFactory,
    AIProvider,
    AIRequest,
    AIMessage,
    AIClientConfig
)

async def main():
    # 클라이언트 설정
    config = AIClientConfig(
        api_key=os.getenv("CLAUDE_API_KEY"),
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        temperature=0.7
    )
    
    # 클라이언트 생성
    client = AIClientFactory.create_client(AIProvider.CLAUDE, config)
    
    # 요청 생성
    request = AIRequest(
        messages=[
            AIMessage(role="system", content="You are a helpful assistant."),
            AIMessage(role="user", content="Hello, how are you?")
        ]
    )
    
    # 응답 받기
    async with client:
        response = await client.generate(request)
        print(f"Response: {response.content}")
        print(f"Tokens used: {response.tokens_used}")

# 실행
asyncio.run(main())
```

### 2. 멀티 클라이언트 사용 (폴백 지원)

```python
import asyncio
import os
from packages.ai_clients import (
    AIClientFactory,
    MultiAIClient,
    AIProvider,
    AIRequest,
    AIMessage,
    AIClientConfig
)

async def main():
    # 여러 클라이언트 설정
    clients = {}
    
    # Claude 클라이언트
    if os.getenv("CLAUDE_API_KEY"):
        claude_config = AIClientConfig(
            api_key=os.getenv("CLAUDE_API_KEY"),
            model="claude-3-sonnet-20240229"
        )
        clients[AIProvider.CLAUDE] = AIClientFactory.create_client(
            AIProvider.CLAUDE, claude_config
        )
    
    # OpenAI 클라이언트
    if os.getenv("OPENAI_API_KEY"):
        openai_config = AIClientConfig(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o"
        )
        clients[AIProvider.OPENAI] = AIClientFactory.create_client(
            AIProvider.OPENAI, openai_config
        )
    
    # 멀티 클라이언트 생성
    multi_client = MultiAIClient(clients)
    multi_client.set_primary_provider(AIProvider.CLAUDE)
    
    # 요청 생성
    request = AIRequest(
        messages=[
            AIMessage(role="user", content="Explain AI in simple terms.")
        ]
    )
    
    # 폴백과 함께 응답 받기
    try:
        response = await multi_client.generate(request, fallback=True)
        print(f"Provider: {response.provider}")
        print(f"Response: {response.content}")
    except Exception as e:
        print(f"All providers failed: {e}")

asyncio.run(main())
```

### 3. 간단한 팩토리 사용법

```python
import asyncio
import os
from packages.ai_clients import AIClientFactory, AIProvider

async def main():
    # 간단한 클라이언트 생성
    client = AIClientFactory.create_from_settings(
        provider=AIProvider.OPENAI,
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        max_tokens=500,
        temperature=0.5
    )
    
    # 사용법은 동일
    async with client:
        response = await client.generate(request)
        print(response.content)

asyncio.run(main())
```

## API 서버 실행

### 개발 서버 시작

```bash
# FastAPI 서버 실행
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 3000 --reload

# 서버가 시작되면 다음 URL에서 확인 가능:
# - API 문서: http://127.0.0.1:3000/docs
# - API 스펙: http://127.0.0.1:3000/openapi.json
```

### 콘텐츠 생성 API 사용

```bash
# 콘텐츠 생성 요청 (JSON)
curl -X POST "http://127.0.0.1:3000/api/v1/generation/generate" \
     -H "Content-Type: application/json" \
     -d '{
       "topic": "인공지능의 미래",
       "tone": "professional", 
       "word_count": 800,
       "include_images": true,
       "target_language": "ko"
     }'

# 생성 작업 상태 확인
curl "http://127.0.0.1:3000/api/v1/generation/jobs/{job_id}"
```

## 예제 실행

### 기본 예제 실행

```bash
# 환경 변수 로드 후 예제 실행
python examples/ai_client_usage.py
```

### 개별 예제 실행

```bash
# Python 인터프리터에서
python -c "
import asyncio
from examples.ai_client_usage import example_single_client
asyncio.run(example_single_client())
"
```

## API 응답 형식

모든 AI 클라이언트는 동일한 `AIResponse` 객체를 반환합니다:

```python
class AIResponse:
    content: str              # AI가 생성한 텍스트
    model: str               # 사용된 모델명
    tokens_used: int         # 사용된 토큰 수 (옵션)
    finish_reason: str       # 완료 이유 (옵션)
    provider: AIProvider     # 사용된 AI 제공업체
    raw_response: dict       # 원본 API 응답 (옵션)
```

## 오류 처리

```python
async def robust_ai_call():
    try:
        async with client:
            response = await client.generate(request)
            return response
    except httpx.HTTPError as e:
        print(f"HTTP error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    return None
```

## 설정 옵션

### AIClientConfig 매개변수

- `api_key`: API 키 (필수)
- `model`: 사용할 모델명 (필수)
- `base_url`: API 기본 URL (선택사항)
- `max_tokens`: 최대 토큰 수 (기본값: 4000)
- `temperature`: 창의성 수준 (기본값: 0.7)
- `timeout`: 요청 타임아웃 (기본값: 30초)

### 지원하는 AI 제공업체

```python
from packages.ai_clients import AIClientFactory

# 지원하는 제공업체 목록 확인
providers = AIClientFactory.get_supported_providers()
print(providers)  # ['claude', 'openai', 'gemini', 'grok']
```

## 모범 사례

1. **환경 변수 사용**: API 키를 코드에 하드코딩하지 마세요
2. **비동기 컨텍스트 매니저 사용**: `async with client:` 패턴 사용
3. **오류 처리**: 네트워크 오류와 API 한도 초과에 대비하세요
4. **폴백 설정**: 중요한 애플리케이션에서는 여러 제공업체 설정
5. **토큰 모니터링**: 비용 관리를 위해 토큰 사용량 추적

## 데이터베이스

### 자동 생성되는 테이블

서버 시작 시 자동으로 다음 테이블들이 생성됩니다:

- `generation_jobs`: 콘텐츠 생성 작업 추적
- `publish_jobs`: 퍼블리싱 작업 추적

### 데이터베이스 위치

```bash
# SQLite 데이터베이스 파일
data/aiwriter.db
```

## 지원하는 AI 모델

### Claude (Anthropic)
- claude-3-sonnet-20240229 (기본)
- claude-3-haiku-20240307
- claude-3-opus-20240229

### OpenAI
- gpt-4o (기본)
- gpt-4o-mini
- gpt-3.5-turbo

### Google Gemini
- gemini-1.5-pro (기본)
- gemini-1.5-flash

### Grok (X.AI)
- grok-beta (기본)

## API 엔드포인트

### 콘텐츠 생성
- `POST /api/v1/generation/generate` - 콘텐츠 생성 요청
- `GET /api/v1/generation/jobs/{job_id}` - 작업 상태 조회
- `GET /api/v1/generation/jobs` - 모든 작업 목록

### 번들 관리
- `GET /api/v1/bundles/` - 번들 목록
- `GET /api/v1/bundles/{bundle_id}` - 번들 상세 정보
- `DELETE /api/v1/bundles/{bundle_id}` - 번들 삭제

### 퍼블리싱
- `POST /api/v1/publishing/publish` - 콘텐츠 발행
- `GET /api/v1/publishing/jobs/{job_id}` - 발행 상태 조회
- `POST /api/v1/publishing/test-connection/{platform}` - 플랫폼 연결 테스트

## 문제 해결

### 일반적인 오류

1. **API 키 오류**: 환경 변수가 올바르게 설정되었는지 확인
2. **네트워크 오류**: 인터넷 연결과 방화벽 설정 확인
3. **모델 오류**: 지정한 모델이 해당 제공업체에서 지원되는지 확인
4. **토큰 한도 초과**: `max_tokens` 값을 조정하세요
5. **데이터베이스 오류**: `data/` 디렉토리 생성 확인
6. **포트 충돌**: 다른 포트 사용 (3000, 8080 등)

### Python 버전 호환성

- **지원 버전**: Python 3.11, 3.12, 3.13
- **권장 버전**: Python 3.13 (최신 성능 최적화)

### 의존성 설치 문제

```bash
# 의존성 재설치
pip install -e . --force-reinstall

# 개발 의존성 포함
pip install -e ".[dev]"
```

### 디버깅

```python
# 원본 API 응답 확인
response = await client.generate(request)
print(response.raw_response)  # 디버깅용 원본 응답

# 로그 레벨 조정 (.env 파일)
LOG_LEVEL=DEBUG
```

## 라이선스

이 AI 클라이언트는 프로젝트의 라이선스를 따릅니다.