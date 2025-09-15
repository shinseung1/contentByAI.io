# 데이터베이스 구성 정보

## 데이터베이스 기본 정보
- **타입**: SQLite
- **파일 위치**: `data/aiwriter.db`
- **인코딩**: UTF-8

## 테이블 구조

### 1. test_results (테스트 결과)
```sql
CREATE TABLE test_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,                 -- AI 제공자 (gemini, claude, openai, grok)
    prompt TEXT NOT NULL,                   -- 입력 프롬프트
    response TEXT,                          -- AI 응답
    success BOOLEAN NOT NULL DEFAULT 1,     -- 성공 여부
    error_message TEXT,                     -- 에러 메시지
    token_usage TEXT,                       -- 토큰 사용량 (JSON)
    response_time_ms INTEGER,               -- 응답 시간 (밀리초)
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### 2. users (사용자)
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,          -- 사용자명
    password_hash TEXT NOT NULL,            -- 비밀번호 해시 (salt:hash)
    email TEXT UNIQUE,                      -- 이메일
    role TEXT NOT NULL DEFAULT 'user',      -- 역할 (admin, user, validator)
    is_active BOOLEAN NOT NULL DEFAULT 1,   -- 활성 상태
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TEXT,                        -- 계정 만료일
    last_login TEXT,                        -- 마지막 로그인
    login_attempts INTEGER NOT NULL DEFAULT 0, -- 로그인 실패 횟수
    locked_until TEXT                       -- 계정 잠김 해제 시간
);
```

### 3. login_sessions (로그인 세션)
```sql
CREATE TABLE login_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,               -- 사용자 ID
    session_token TEXT UNIQUE NOT NULL,     -- 세션 토큰
    expires_at TEXT NOT NULL,               -- 세션 만료시간
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,                        -- IP 주소
    user_agent TEXT,                        -- User Agent
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
```

### 4. generation_jobs (콘텐츠 생성 작업)
```sql
CREATE TABLE generation_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT UNIQUE NOT NULL,            -- 작업 고유 ID
    provider TEXT NOT NULL,                 -- AI 제공자
    topic TEXT NOT NULL,                    -- 주제
    tone TEXT NOT NULL DEFAULT 'professional', -- 톤 (전문적, 친근함 등)
    word_count INTEGER NOT NULL DEFAULT 800, -- 단어 수
    include_images BOOLEAN NOT NULL DEFAULT 1, -- 이미지 포함 여부
    target_language TEXT NOT NULL DEFAULT 'ko', -- 대상 언어
    status TEXT NOT NULL DEFAULT 'pending', -- 상태 (pending, in_progress, completed, failed)
    progress INTEGER NOT NULL DEFAULT 0,    -- 진행률 (0-100)
    content TEXT,                           -- 생성된 콘텐츠
    html_content TEXT,                      -- HTML 콘텐츠
    markdown_content TEXT,                  -- 마크다운 콘텐츠
    error_message TEXT,                     -- 에러 메시지
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### 5. image_cache (이미지 캐시)
```sql
CREATE TABLE image_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url_hash TEXT UNIQUE NOT NULL,          -- URL 해시값
    original_url TEXT NOT NULL,             -- 원본 URL
    alt_text TEXT NOT NULL DEFAULT '',      -- 대체 텍스트
    caption TEXT NOT NULL DEFAULT '',       -- 캡션
    image_data BLOB NOT NULL,               -- 이미지 바이너리 데이터
    mime_type TEXT NOT NULL,                -- MIME 타입 (image/jpeg, image/png)
    file_size INTEGER NOT NULL DEFAULT 0,   -- 파일 크기
    width INTEGER,                          -- 이미지 너비
    height INTEGER,                         -- 이미지 높이
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_accessed TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER NOT NULL DEFAULT 0 -- 액세스 횟수
);
```

### 6. bundles (번들)
```sql
CREATE TABLE bundles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bundle_id TEXT UNIQUE NOT NULL,         -- 번들 고유 ID (UUID)
    title TEXT NOT NULL,                    -- 번들 제목
    description TEXT,                       -- 번들 설명
    status TEXT NOT NULL DEFAULT 'draft',   -- 상태 (draft, published, archived)
    post_count INTEGER NOT NULL DEFAULT 0,  -- 포스트 수
    total_views INTEGER NOT NULL DEFAULT 0, -- 총 조회수
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    published_at TEXT,                      -- 게시일
    metadata TEXT                           -- 추가 메타데이터 (JSON)
);
```

## 인덱스

```sql
-- 성능 최적화를 위한 인덱스들
CREATE INDEX idx_test_results_provider ON test_results(provider);
CREATE INDEX idx_test_results_created_at ON test_results(created_at DESC);
CREATE INDEX idx_generation_jobs_job_id ON generation_jobs(job_id);
CREATE INDEX idx_generation_jobs_status ON generation_jobs(status);
CREATE INDEX idx_image_cache_url_hash ON image_cache(url_hash);
```

## 기본 계정 정보

### 관리자 계정
- **사용자명**: `admin`
- **비밀번호**: `admin123!`
- **역할**: `admin`
- **유효기간**: 무제한

### 검증자 계정
- **사용자명**: `validator`
- **비밀번호**: `validator123`
- **역할**: `validator`
- **유효기간**: 1년

### 테스트 계정
- **사용자명**: `testuser`
- **비밀번호**: `test123`
- **역할**: `user`
- **유효기간**: 30일

## 주요 특징

### 보안 기능
- 비밀번호는 PBKDF2-HMAC-SHA256으로 해시화
- 로그인 실패 5회 시 30분간 계정 잠김
- 세션 토큰 기반 인증 (24시간 유효)
- 계정 만료일 설정 가능

### 이미지 캐시 관리
- URL 해시값으로 중복 방지
- 액세스 횟수 및 마지막 액세스 시간 추적
- 자동 정리 기능 (30일 이상 된 이미지, 크기 제한)

### 콘텐츠 생성 관리
- 작업 상태 추적 (pending → in_progress → completed/failed)
- 진행률 표시
- 다양한 형식 지원 (HTML, Markdown)

## 초기화 방법

```python
from database import DatabaseManager

# 데이터베이스 초기화
db = DatabaseManager()

# 기본 계정들이 자동으로 생성됨
```

## 기본 데이터 INSERT 쿼리

### 기본 사용자 생성
```sql
-- 관리자 계정 (비밀번호: admin123!)
INSERT INTO users (username, password_hash, email, role, is_active, created_at, updated_at, expires_at) 
VALUES (
    'admin', 
    'salt_value:hashed_password_value',  -- 실제로는 PBKDF2로 해시된 값
    'admin@aiwriter.com', 
    'admin', 
    1, 
    datetime('now'), 
    datetime('now'), 
    NULL
);

-- 검증자 계정 (비밀번호: validator123)
INSERT INTO users (username, password_hash, email, role, is_active, created_at, updated_at, expires_at) 
VALUES (
    'validator', 
    'salt_value:hashed_password_value',  -- 실제로는 PBKDF2로 해시된 값
    'validator@aiwriter.com', 
    'validator', 
    1, 
    datetime('now'), 
    datetime('now'), 
    datetime('now', '+365 days')
);

-- 일반 사용자 계정 (비밀번호: test123)
INSERT INTO users (username, password_hash, email, role, is_active, created_at, updated_at, expires_at) 
VALUES (
    'testuser', 
    'salt_value:hashed_password_value',  -- 실제로는 PBKDF2로 해시된 값
    'test@aiwriter.com', 
    'user', 
    1, 
    datetime('now'), 
    datetime('now'), 
    datetime('now', '+30 days')
);
```

### 샘플 테스트 결과
```sql
-- Gemini 테스트 결과
INSERT INTO test_results (provider, prompt, response, success, token_usage, response_time_ms, created_at)
VALUES (
    'gemini',
    '안녕하세요! 간단한 인사말로 답해주세요.',
    '안녕하세요! 좋은 하루 되세요!',
    1,
    '{"promptTokenCount": 10, "candidatesTokenCount": 8, "totalTokenCount": 18}',
    1250,
    datetime('now')
);

-- Claude 테스트 결과
INSERT INTO test_results (provider, prompt, response, success, token_usage, response_time_ms, created_at)
VALUES (
    'claude',
    'AI의 미래에 대해 설명해주세요.',
    'AI는 앞으로 더욱 발전하여 다양한 분야에서 인간의 삶을 향상시킬 것입니다...',
    1,
    '{"input_tokens": 15, "output_tokens": 50, "total_tokens": 65}',
    2100,
    datetime('now')
);

-- OpenAI 테스트 결과
INSERT INTO test_results (provider, prompt, response, success, token_usage, response_time_ms, created_at)
VALUES (
    'openai',
    '창의적인 글쓰기 예시를 보여주세요.',
    '별빛이 내리는 밤, 작은 마을에서 특별한 이야기가 시작됩니다...',
    1,
    '{"prompt_tokens": 12, "completion_tokens": 45, "total_tokens": 57}',
    1800,
    datetime('now')
);
```

### 샘플 콘텐츠 생성 작업
```sql
-- 진행 중인 작업
INSERT INTO generation_jobs (
    job_id, provider, topic, tone, word_count, include_images, 
    target_language, status, progress, created_at, updated_at
) VALUES (
    'job_12345678',
    'gemini',
    '인공지능의 미래와 전망',
    'professional',
    1000,
    1,
    'ko',
    'in_progress',
    75,
    datetime('now'),
    datetime('now')
);

-- 완료된 작업
INSERT INTO generation_jobs (
    job_id, provider, topic, tone, word_count, include_images, 
    target_language, status, progress, content, html_content, created_at, updated_at
) VALUES (
    'job_87654321',
    'claude',
    '건강한 라이프스타일 가이드',
    'friendly',
    800,
    1,
    'ko',
    'completed',
    100,
    '건강한 라이프스타일을 위한 완전한 가이드입니다...',
    '<h1>건강한 라이프스타일 가이드</h1><p>건강한 라이프스타일을 위한 완전한 가이드입니다...</p>',
    datetime('now', '-1 hour'),
    datetime('now')
);
```

### 샘플 번들
```sql
-- 기술 관련 번들
INSERT INTO bundles (
    bundle_id, title, description, status, post_count, 
    total_views, metadata, created_at, updated_at
) VALUES (
    'bundle_tech_2024',
    '2024 기술 트렌드',
    'AI, 블록체인, 메타버스 등 2024년 주요 기술 트렌드를 다루는 글 모음',
    'published',
    5,
    1250,
    '{"category": "technology", "tags": ["AI", "blockchain", "metaverse"], "featured": true}',
    datetime('now', '-7 days'),
    datetime('now', '-1 day')
);

-- 라이프스타일 번들
INSERT INTO bundles (
    bundle_id, title, description, status, post_count, 
    total_views, metadata, created_at, updated_at
) VALUES (
    'bundle_lifestyle_health',
    '건강한 생활 가이드',
    '운동, 영양, 정신건강 등 건강한 라이프스타일을 위한 종합 가이드',
    'draft',
    3,
    0,
    '{"category": "lifestyle", "tags": ["health", "fitness", "nutrition"], "featured": false}',
    datetime('now', '-3 days'),
    datetime('now')
);
```

### 이미지 캐시 샘플 (바이너리 데이터는 실제 환경에서 삽입)
```sql
-- 기본 이미지 캐시 구조 (실제 image_data는 바이너리로 삽입해야 함)
INSERT INTO image_cache (
    url_hash, original_url, alt_text, caption, 
    mime_type, file_size, width, height, created_at, last_accessed, access_count
) VALUES (
    'hash_example_123',
    'https://example.com/sample-image.jpg',
    '샘플 이미지',
    '이것은 샘플 이미지입니다',
    'image/jpeg',
    45678,
    800,
    600,
    datetime('now', '-2 days'),
    datetime('now', '-1 hour'),
    15
);
```

## 빠른 초기화 스크립트

```sql
-- 모든 테이블 생성 및 기본 데이터 삽입을 위한 완전한 스크립트
PRAGMA encoding = 'UTF-8';

-- 테이블 생성은 위의 테이블 구조 참조

-- 기본 사용자 3명 생성 (Python 코드로 실행 권장 - 비밀번호 해싱 때문)
-- 위의 사용자 INSERT 쿼리들 실행

-- 샘플 테스트 결과 삽입
-- 위의 test_results INSERT 쿼리들 실행

-- 기본 번들 생성
-- 위의 bundles INSERT 쿼리들 실행

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_test_results_provider ON test_results(provider);
CREATE INDEX IF NOT EXISTS idx_test_results_created_at ON test_results(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_generation_jobs_job_id ON generation_jobs(job_id);
CREATE INDEX IF NOT EXISTS idx_generation_jobs_status ON generation_jobs(status);
CREATE INDEX IF NOT EXISTS idx_image_cache_url_hash ON image_cache(url_hash);
```

## 주요 메서드

### 사용자 관리
- `create_user()`: 사용자 생성
- `verify_user_password()`: 비밀번호 검증
- `create_session()`: 세션 생성
- `validate_session()`: 세션 검증

### 콘텐츠 생성
- `save_generation_job()`: 생성 작업 저장
- `get_generation_job()`: 작업 조회
- `update_generation_job_status()`: 상태 업데이트

### 이미지 캐시
- `save_image_cache()`: 이미지 캐시 저장
- `get_image_cache()`: 캐시 조회
- `cleanup_old_images()`: 오래된 이미지 정리

### 번들 관리
- `create_bundle()`: 번들 생성
- `get_bundle()`: 번들 조회
- `update_bundle()`: 번들 업데이트
- `delete_bundle()`: 번들 삭제