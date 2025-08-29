# AI Clients 사용 가이드

이 문서는 Claude API, ChatGPT, Gemini, Grok API 클라이언트의 설정 및 사용법을 설명합니다.

## 설치 및 설정

### 1. 환경 변수 설정

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

## 문제 해결

### 일반적인 오류

1. **API 키 오류**: 환경 변수가 올바르게 설정되었는지 확인
2. **네트워크 오류**: 인터넷 연결과 방화벽 설정 확인
3. **모델 오류**: 지정한 모델이 해당 제공업체에서 지원되는지 확인
4. **토큰 한도 초과**: `max_tokens` 값을 조정하세요

### 디버깅

```python
# 원본 API 응답 확인
response = await client.generate(request)
print(response.raw_response)  # 디버깅용 원본 응답
```

## 라이선스

이 AI 클라이언트는 프로젝트의 라이선스를 따릅니다.