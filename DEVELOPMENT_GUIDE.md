# 개발 가이드 및 컨벤션

## 📚 프로젝트 개요

AI Writer는 AI 기반 자동 블로그 포스팅 시스템으로, SOLID 원칙을 따르는 모듈형 아키텍처를 채택했습니다.

### 기술 스택
- **Backend**: Python 3.11+, FastAPI, SQLite
- **Frontend**: React 18, TypeScript, Ant Design, Vite
- **AI Services**: Gemini, Claude, OpenAI, Grok
- **Publishing**: WordPress REST API, Google Blogger API v3
- **Container**: Docker, Docker Compose

## 🏗️ 아키텍처 패턴

### 디렉토리 구조 규칙
```
├── apps/                    # 애플리케이션 계층 (외부 인터페이스)
├── packages/                # 비즈니스 로직 (재사용 가능한 모듈)
├── web/                     # 프론트엔드 (사용자 인터페이스)
├── docs/                    # 문서화
├── data/                    # 런타임 데이터
├── runs/                    # 실행 로그
└── bundles/                 # 생성된 콘텐츠
```

### 모듈 의존성 규칙
- `apps/` → `packages/` (O)
- `packages/` → `apps/` (X)
- `packages/` 간 순환 의존성 금지
- 외부 라이브러리는 `packages/core/`에서 래핑

## 🐍 Python 코딩 컨벤션

### 코드 스타일
- **포맷터**: Ruff (Black 호환)
- **린터**: Ruff + MyPy
- **라인 길이**: 88자
- **인코딩**: UTF-8

### 네이밍 컨벤션
```python
# 클래스: PascalCase
class ContentGenerator:
    pass

# 함수/변수: snake_case
def generate_content():
    user_input = "example"

# 상수: UPPER_CASE
MAX_RETRY_COUNT = 5

# 비공개: _prefix
def _internal_function():
    pass

# 매직 메서드: __dunder__
def __init__(self):
    pass
```

### 타입 힌트
```python
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

# 함수 시그니처
def process_content(
    topic: str,
    word_count: int = 800,
    options: Optional[Dict[str, Any]] = None
) -> ContentBundle:
    """콘텐츠를 처리하여 번들을 생성합니다."""
    pass

# Pydantic 모델
class GenerationRequest(BaseModel):
    topic: str
    tone: str = "professional"
    word_count: int = 800
    include_images: bool = True
```

### 예외 처리
```python
# 커스텀 예외 사용
from packages.core.exceptions import RetryableError, FatalError

def api_call():
    try:
        response = client.request()
    except httpx.ConnectError as e:
        raise RetryableError(f"Connection failed: {e}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code >= 500:
            raise RetryableError(f"Server error: {e}")
        else:
            raise FatalError(f"Client error: {e}")
```

### 로깅
```python
import logging

logger = logging.getLogger(__name__)

def process_data():
    logger.info("Processing started")
    try:
        result = heavy_computation()
        logger.info(f"Processing completed: {len(result)} items")
        return result
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        raise
```

## ⚛️ React/TypeScript 컨벤션

### 컴포넌트 구조
```typescript
// 컴포넌트 파일: PascalCase.tsx
// Props 인터페이스 정의
interface ContentGeneratorProps {
  topic: string;
  onGenerate: (content: Content) => void;
  isLoading?: boolean;
}

// 컴포넌트 정의
export const ContentGenerator: React.FC<ContentGeneratorProps> = ({
  topic,
  onGenerate,
  isLoading = false,
}) => {
  // hooks 먼저
  const [formData, setFormData] = useState<FormData>({});
  
  // event handlers
  const handleSubmit = useCallback((data: FormData) => {
    // implementation
  }, []);

  // render
  return (
    <div className="content-generator">
      {/* JSX */}
    </div>
  );
};
```

### 상태 관리 (Zustand)
```typescript
// stores/useContentStore.ts
interface ContentState {
  contents: Content[];
  isLoading: boolean;
  generateContent: (request: GenerationRequest) => Promise<void>;
}

export const useContentStore = create<ContentState>((set, get) => ({
  contents: [],
  isLoading: false,
  
  generateContent: async (request) => {
    set({ isLoading: true });
    try {
      const content = await apiService.generateContent(request);
      set((state) => ({ 
        contents: [...state.contents, content],
        isLoading: false 
      }));
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },
}));
```

### API 서비스
```typescript
// services/apiService.ts
class ApiService {
  private baseURL = '/api/v1';

  async generateContent(request: GenerationRequest): Promise<Content> {
    const response = await fetch(`${this.baseURL}/generation/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Generation failed: ${response.statusText}`);
    }

    return response.json();
  }
}

export const apiService = new ApiService();
```

## 🧪 테스트 작성 가이드

### Python 테스트
```python
# tests/test_publisher.py
import pytest
from unittest.mock import Mock, patch
from packages.publisher.wp.publisher import WordPressPublisher

class TestWordPressPublisher:
    @pytest.fixture
    def publisher(self):
        config = Mock()
        config.wp_base_url = "https://test.com"
        return WordPressPublisher(config)

    @pytest.mark.asyncio
    async def test_publish_success(self, publisher):
        """성공적인 발행 테스트"""
        with patch.object(publisher.client, 'create_post') as mock_create:
            mock_create.return_value = {"id": 123}
            
            result = await publisher.publish_immediately(mock_bundle)
            
            assert result.success is True
            assert result.post_id == 123
            mock_create.assert_called_once()

    @pytest.mark.integration
    async def test_real_api_call(self, publisher):
        """실제 API 호출 테스트 (통합 테스트)"""
        # 실제 API 환경에서만 실행
        pass
```

### React 테스트 (향후 추가 예정)
```typescript
// 컴포넌트 테스트 예시
import { render, screen, fireEvent } from '@testing-library/react';
import { ContentGenerator } from './ContentGenerator';

describe('ContentGenerator', () => {
  it('should generate content when form is submitted', async () => {
    const mockOnGenerate = jest.fn();
    
    render(
      <ContentGenerator 
        topic="test topic" 
        onGenerate={mockOnGenerate} 
      />
    );

    const submitButton = screen.getByRole('button', { name: /generate/i });
    fireEvent.click(submitButton);

    expect(mockOnGenerate).toHaveBeenCalled();
  });
});
```

## 📝 문서화 규칙

### Python Docstring
```python
def generate_content(
    topic: str, 
    word_count: int = 800,
    tone: str = "professional"
) -> ContentBundle:
    """AI를 사용하여 블로그 콘텐츠를 생성합니다.

    Args:
        topic: 생성할 콘텐츠의 주제
        word_count: 목표 단어 수 (기본값: 800)
        tone: 글의 톤 (professional, casual, friendly 등)

    Returns:
        ContentBundle: 생성된 콘텐츠 번들

    Raises:
        ContentGenerationError: AI 서비스 호출 실패 시
        ValidationError: 입력 데이터 검증 실패 시

    Example:
        >>> bundle = await generate_content("AI의 미래", 1000)
        >>> print(bundle.title)
        "인공지능이 바꿀 미래 사회"
    """
```

### 주석 작성 규칙
```python
# 좋은 주석 - 왜(Why)를 설명
# 지수 백오프를 사용하여 API 서버 부하를 분산
await asyncio.sleep(2 ** attempt)

# 나쁜 주석 - 무엇(What)을 중복 설명
# count를 1 증가시킴
count += 1
```

## 🔄 Git 워크플로우

### 커밋 메시지 컨벤션
```
type(scope): subject

body (선택사항)

footer (선택사항)
```

#### 타입
- `feat`: 새로운 기능
- `fix`: 버그 수정
- `refactor`: 리팩토링
- `docs`: 문서 변경
- `test`: 테스트 추가/수정
- `chore`: 빌드/배포 관련

#### 예시
```
feat(publisher): add Blogger API integration

- Implement BloggerPublisher class
- Add OAuth2 authentication
- Support scheduled publishing

Closes #123
```

### 브랜치 네이밍
```
feature/blogger-integration
fix/wordpress-auth-error
refactor/publisher-interface
docs/api-documentation
```

## 🚀 배포 및 릴리스

### 환경별 설정
```python
# config.py
class Settings(BaseSettings):
    app_env: str = "development"
    debug: bool = False
    
    @computed_field
    @property
    def is_development(self) -> bool:
        return self.app_env == "development"
```

### Docker 빌드
```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드
COPY . .

# 권한 설정
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 3000
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "3000"]
```

## 🔒 보안 가이드라인

### 민감정보 처리
```python
# 로그에서 민감정보 마스킹
def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    sensitive_keys = ["password", "token", "key", "secret"]
    return {
        k: "***" if any(s in k.lower() for s in sensitive_keys) else v
        for k, v in data.items()
    }

logger.info(f"Request data: {mask_sensitive_data(request_data)}")
```

### 입력 검증
```python
from pydantic import BaseModel, validator

class GenerationRequest(BaseModel):
    topic: str
    word_count: int = 800

    @validator('topic')
    def topic_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Topic cannot be empty')
        return v.strip()

    @validator('word_count')
    def word_count_must_be_reasonable(cls, v):
        if not 100 <= v <= 5000:
            raise ValueError('Word count must be between 100 and 5000')
        return v
```

## 📊 성능 최적화

### 데이터베이스 최적화
```python
# 인덱스 생성
CREATE INDEX idx_bundles_created_at ON bundles(created_at);
CREATE INDEX idx_bundles_status ON bundles(status);

# 쿼리 최적화
async def get_recent_bundles(limit: int = 10):
    query = """
    SELECT * FROM bundles 
    WHERE status = 'completed'
    ORDER BY created_at DESC 
    LIMIT ?
    """
    return await database.fetch_all(query, [limit])
```

### API 최적화
```python
# 비동기 처리
@router.post("/generate")
async def generate_content(
    request: GenerationRequest,
    background_tasks: BackgroundTasks
):
    job_id = generate_uuid()
    
    # 백그라운드에서 실행
    background_tasks.add_task(
        process_generation_job,
        job_id,
        request
    )
    
    return {"job_id": job_id, "status": "queued"}
```

## 🧪 테스트 전략

### 테스트 피라미드
1. **Unit Tests (70%)**: 개별 함수/클래스
2. **Integration Tests (20%)**: 모듈 간 연동
3. **E2E Tests (10%)**: 전체 워크플로우

### 테스트 마킹
```python
# pytest.ini
[tool:pytest]
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
    api: API tests
```

### 모킹 가이드
```python
# 외부 API 모킹
@patch('packages.publisher.wp.client.WordPressClient')
def test_wordpress_publishing(mock_client):
    mock_client.return_value.create_post.return_value = {"id": 123}
    # 테스트 로직
```

## 🔧 개발 도구 및 자동화

### Pre-commit 훅
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: ruff-check
        name: ruff check
        entry: ruff check
        language: system
        types: [python]
      
      - id: mypy
        name: mypy
        entry: mypy
        language: system
        types: [python]
```

### VSCode 작업 설정
```json
// .vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Run Tests",
      "type": "shell",
      "command": "pytest",
      "group": "test",
      "problemMatcher": []
    },
    {
      "label": "Format Code",
      "type": "shell",
      "command": "ruff format .",
      "group": "build"
    }
  ]
}
```

## 📈 모니터링 및 디버깅

### 로깅 전략
```python
# 구조화된 로깅
logger.info(
    "Content generation completed",
    extra={
        "job_id": job_id,
        "topic": topic,
        "word_count": len(content),
        "duration_ms": duration,
        "ai_provider": provider
    }
)
```

### 성능 측정
```python
import time
from functools import wraps

def measure_time(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start
            logger.info(f"{func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start
            logger.error(f"{func.__name__} failed after {duration:.2f}s: {e}")
            raise
    return wrapper
```

## 🔄 CI/CD 가이드라인

### GitHub Actions 예시
```yaml
# .github/workflows/test.yml
name: Test and Lint

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -e .[dev]
      
      - name: Run tests
        run: |
          pytest --cov=packages
      
      - name: Run linting
        run: |
          ruff check .
          mypy .
```

## 🔧 자주 사용하는 개발 명령어

### Python 개발
```bash
# 가상환경 활성화 (개발 시작 시)
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# 개발 서버 실행
python mac_server.py

# 테스트 실행
pytest -v

# 코드 품질 검사
ruff check .
mypy .

# 포맷팅
ruff format .
```

### 프론트엔드 개발
```bash
cd web

# 개발 서버 시작
npm run dev

# 빌드 테스트
npm run build

# 린팅
npm run lint

# 타입 체크
npx tsc --noEmit
```

### Docker 개발
```bash
# 개발환경 시작
make dev

# 로그 확인
make logs

# 컨테이너 재빌드
docker-compose -f docker-compose.dev.yml up --build
```

## 📋 체크리스트

### 새 기능 개발 시
- [ ] 관련 테스트 작성
- [ ] 타입 힌트 추가
- [ ] Docstring 작성
- [ ] 로깅 추가
- [ ] 에러 처리 구현
- [ ] API 문서 업데이트

### PR 제출 전
- [ ] 모든 테스트 통과 (`make test`)
- [ ] 린팅 통과 (`make lint`)
- [ ] 코드 포맷팅 적용 (`make format`)
- [ ] 기능 동작 확인
- [ ] 문서 업데이트

### 배포 전
- [ ] 프로덕션 빌드 테스트
- [ ] 환경변수 설정 확인
- [ ] 데이터베이스 마이그레이션
- [ ] 백업 생성
- [ ] 롤백 계획 수립

이 가이드를 따라 일관성 있고 고품질의 코드를 작성해주세요.