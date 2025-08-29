# AI Writer API 문서

## 개요

AI Writer는 RESTful API를 제공하여 외부 시스템과의 연동을 지원합니다. 모든 API는 JSON 형식으로 요청과 응답을 처리합니다.

## 기본 정보

- **Base URL**: `http://localhost:8000/api/v1`
- **Content-Type**: `application/json`
- **응답 형식**: JSON
- **API 문서**: `http://localhost:8000/docs` (Swagger UI)

## 인증

현재 버전에서는 API 키 인증을 사용하지 않습니다. 프로덕션 환경에서는 적절한 인증 메커니즘을 추가해야 합니다.

## 에러 응답 형식

```json
{
  "error_code": "ERROR_CODE",
  "message": "Human readable error message",
  "details": {
    "field": "error details"
  }
}
```

## API 엔드포인트

### 1. 헬스체크

#### GET /health/

시스템 상태를 확인합니다.

**응답**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "dev"
}
```

**상태 코드**
- `200`: 정상
- `503`: 시스템 오류

---

### 2. 콘텐츠 생성

#### POST /generation/generate

AI를 사용하여 새로운 콘텐츠를 생성합니다.

**요청**
```json
{
  "topic": "인공지능의 미래와 활용 방안",
  "tone": "professional",
  "word_count": 800,
  "include_images": true,
  "target_language": "ko"
}
```

**요청 필드**
- `topic` (string, required): 생성할 콘텐츠의 주제
- `tone` (string, optional): 톤앤매너 ("professional", "casual", "friendly", "academic", "conversational")
- `word_count` (integer, optional): 목표 단어 수 (300-3000, 기본값: 800)
- `include_images` (boolean, optional): 이미지 포함 여부 (기본값: true)
- `target_language` (string, optional): 대상 언어 (기본값: "ko")

**응답**
```json
{
  "job_id": "gen_12345678",
  "status": "started",
  "message": "Content generation started"
}
```

**상태 코드**
- `200`: 요청 성공
- `400`: 잘못된 요청
- `422`: 유효성 검사 실패

#### GET /generation/jobs/{job_id}

콘텐츠 생성 작업의 상태와 결과를 조회합니다.

**응답 (진행 중)**
```json
{
  "job_id": "gen_12345678",
  "status": "in_progress",
  "progress": 50,
  "message": "Generating content..."
}
```

**응답 (완료)**
```json
{
  "job_id": "gen_12345678",
  "status": "completed",
  "progress": 100,
  "result": {
    "bundle_id": "bundle_87654321",
    "title": "인공지능의 미래와 활용 방안",
    "content_preview": "인공지능(AI)은 현재 우리 삶의 모든 영역에서...",
    "word_count": 850,
    "images_count": 3,
    "seo_score": 85
  }
}
```

**응답 (실패)**
```json
{
  "job_id": "gen_12345678", 
  "status": "failed",
  "error_message": "AI service temporarily unavailable",
  "error_code": "AI_SERVICE_ERROR"
}
```

#### GET /generation/jobs

모든 생성 작업 목록을 조회합니다.

**응답**
```json
[
  "gen_12345678",
  "gen_87654321", 
  "gen_11223344"
]
```

---

### 3. 번들 관리

#### GET /bundles/

생성된 번들 목록을 조회합니다.

**쿼리 파라미터**
- `limit` (integer, optional): 최대 반환 개수 (1-100, 기본값: 50)
- `offset` (integer, optional): 시작 위치 (기본값: 0)

**응답**
```json
{
  "bundles": [
    "bundle_20240101_120000",
    "bundle_20240101_130000",
    "bundle_20240101_140000"
  ],
  "total": 150
}
```

#### GET /bundles/{bundle_id}

특정 번들의 상세 정보를 조회합니다.

**응답**
```json
{
  "bundle_id": "bundle_20240101_120000",
  "bundle": {
    "meta": {
      "title": "인공지능의 미래와 활용 방안",
      "slug": "ai-future-applications",
      "excerpt": "인공지능 기술의 현재와 미래 전망을 살펴봅니다.",
      "categories": ["기술", "AI"],
      "tags": ["인공지능", "미래기술", "자동화"],
      "labels": ["Technology", "AI"],
      "schedule": {
        "mode": "draft",
        "datetime": null
      },
      "featured_image": "images/ai-future.webp"
    },
    "content": "<h1>인공지능의 미래와 활용 방안</h1><p>...",
    "images": [
      {
        "path": "images/ai-future.webp",
        "alt": "미래 인공지능 기술을 상징하는 이미지",
        "caption": "AI 기술의 발전",
        "use_as_featured": true
      }
    ],
    "created_at": "2024-01-01T12:00:00Z",
    "word_count": 850,
    "quality_score": 85
  }
}
```

#### DELETE /bundles/{bundle_id}

번들을 삭제합니다.

**응답**
```json
{
  "message": "Bundle bundle_20240101_120000 deleted successfully"
}
```

**상태 코드**
- `200`: 삭제 성공
- `404`: 번들을 찾을 수 없음

---

### 4. 발행 관리

#### POST /publishing/publish

콘텐츠를 플랫폼에 발행합니다.

**요청**
```json
{
  "bundle_id": "bundle_20240101_120000",
  "platform": "wordpress",
  "mode": "schedule",
  "scheduled_datetime": "2024-01-02T09:00:00+09:00"
}
```

**요청 필드**
- `bundle_id` (string, required): 발행할 번들 ID
- `platform` (string, required): 플랫폼 ("wordpress" 또는 "blogger")
- `mode` (string, required): 발행 모드 ("draft", "publish", "schedule")
- `scheduled_datetime` (string, optional): 예약 시간 (ISO 형식, schedule 모드에서 필수)

**응답**
```json
{
  "job_id": "pub_12345678",
  "status": "started",
  "message": "Publishing to wordpress started"
}
```

#### GET /publishing/jobs/{job_id}

발행 작업의 상태와 결과를 조회합니다.

**응답 (진행 중)**
```json
{
  "job_id": "pub_12345678",
  "status": "in_progress",
  "platform": "wordpress",
  "bundle_id": "bundle_20240101_120000",
  "mode": "schedule",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:01:00Z",
  "scheduled_datetime": "2024-01-02T09:00:00+09:00"
}
```

**응답 (완료)**
```json
{
  "job_id": "pub_12345678",
  "status": "completed",
  "platform": "wordpress",
  "bundle_id": "bundle_20240101_120000",
  "mode": "schedule",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:05:00Z",
  "scheduled_datetime": "2024-01-02T09:00:00+09:00",
  "published_url": "https://your-site.com/ai-future-applications/",
  "metadata": {
    "post_id": "123",
    "platform_specific": {
      "wordpress_id": 123,
      "status": "future"
    }
  }
}
```

#### GET /publishing/jobs

모든 발행 작업 목록을 조회합니다.

**응답**
```json
[
  "pub_12345678",
  "pub_87654321",
  "pub_11223344"
]
```

#### POST /publishing/test-connection/{platform}

플랫폼 연결 상태를 테스트합니다.

**경로 파라미터**
- `platform`: "wordpress" 또는 "blogger"

**응답 (성공)**
```json
{
  "status": "success",
  "result": {
    "platform": "wordpress",
    "connected": true,
    "user_info": {
      "id": 1,
      "username": "admin",
      "capabilities": ["edit_posts", "upload_files"]
    }
  }
}
```

**응답 (실패)**
```json
{
  "status": "error",
  "error": "Authentication failed"
}
```

---

## 웹훅 (향후 지원 예정)

### POST /webhooks/generation/complete

콘텐츠 생성 완료 시 호출됩니다.

### POST /webhooks/publishing/complete  

발행 완료 시 호출됩니다.

---

## 사용 예시

### Python 클라이언트 예시

```python
import requests
import time

# 기본 설정
BASE_URL = "http://localhost:8000/api/v1"

def generate_content(topic):
    """콘텐츠 생성 요청"""
    response = requests.post(f"{BASE_URL}/generation/generate", json={
        "topic": topic,
        "tone": "professional",
        "word_count": 800,
        "include_images": True
    })
    return response.json()

def wait_for_completion(job_id, timeout=300):
    """작업 완료까지 대기"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = requests.get(f"{BASE_URL}/generation/jobs/{job_id}")
        result = response.json()
        
        if result["status"] == "completed":
            return result
        elif result["status"] == "failed":
            raise Exception(f"Generation failed: {result.get('error_message')}")
        
        time.sleep(5)
    
    raise TimeoutError("Generation timeout")

def publish_content(bundle_id, platform="wordpress"):
    """콘텐츠 발행"""
    response = requests.post(f"{BASE_URL}/publishing/publish", json={
        "bundle_id": bundle_id,
        "platform": platform,
        "mode": "publish"
    })
    return response.json()

# 사용 예시
if __name__ == "__main__":
    # 1. 콘텐츠 생성
    gen_result = generate_content("인공지능의 미래")
    job_id = gen_result["job_id"]
    print(f"Generation started: {job_id}")
    
    # 2. 생성 완료 대기
    completed = wait_for_completion(job_id)
    bundle_id = completed["result"]["bundle_id"]
    print(f"Generation completed: {bundle_id}")
    
    # 3. 콘텐츠 발행
    pub_result = publish_content(bundle_id)
    print(f"Publishing started: {pub_result['job_id']}")
```

### cURL 예시

```bash
# 콘텐츠 생성
curl -X POST "http://localhost:8000/api/v1/generation/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "인공지능의 미래",
    "tone": "professional", 
    "word_count": 800
  }'

# 작업 상태 확인
curl "http://localhost:8000/api/v1/generation/jobs/gen_12345678"

# 번들 조회
curl "http://localhost:8000/api/v1/bundles/bundle_20240101_120000"

# 발행 요청
curl -X POST "http://localhost:8000/api/v1/publishing/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "bundle_id": "bundle_20240101_120000",
    "platform": "wordpress",
    "mode": "publish"
  }'

# 연결 테스트
curl -X POST "http://localhost:8000/api/v1/publishing/test-connection/wordpress"
```

## 에러 코드

| 코드 | 설명 | HTTP 상태 |
|------|------|-----------|
| `VALIDATION_ERROR` | 요청 데이터 유효성 검사 실패 | 422 |
| `BUNDLE_NOT_FOUND` | 요청한 번들을 찾을 수 없음 | 404 |
| `JOB_NOT_FOUND` | 요청한 작업을 찾을 수 없음 | 404 |
| `AI_SERVICE_ERROR` | AI 서비스 오류 | 503 |
| `PLATFORM_AUTH_ERROR` | 플랫폼 인증 실패 | 401 |
| `PLATFORM_API_ERROR` | 플랫폼 API 오류 | 502 |
| `GENERATION_FAILED` | 콘텐츠 생성 실패 | 500 |
| `PUBLISHING_FAILED` | 발행 실패 | 500 |

## 레이트 리미팅

- **콘텐츠 생성**: 시간당 최대 100건
- **발행 요청**: 분당 최대 10건
- **기타 요청**: 분당 최대 1000건

레이트 리밋 초과 시 `429 Too Many Requests` 응답이 반환됩니다.

## API 버전 관리

- 현재 버전: `v1`
- 하위 호환성: 메이저 버전 내에서 보장
- 새 버전 출시 시 기존 버전은 최소 6개월간 유지

더 자세한 정보는 [Swagger UI](http://localhost:8000/docs)에서 확인하실 수 있습니다.