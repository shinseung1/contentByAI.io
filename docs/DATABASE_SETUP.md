# 데이터베이스 구성 가이드

## 개요
이 프로젝트는 SQLite 데이터베이스를 사용하여 AI 콘텐츠 생성, 사용자 관리, 워크플로우 템플릿 등을 관리합니다.

## 데이터베이스 파일 위치
```
data/aiwriter.db
```

## 자동 초기화
데이터베이스는 애플리케이션 실행 시 자동으로 초기화됩니다:

```bash
# 데이터베이스 수동 초기화 (선택사항)
python database.py

# 기초 데이터 생성 (추천)
python scripts/init_sample_data.py
```

### 기초 데이터 포함 내용
`init_sample_data.py` 스크립트를 실행하면 다음 샘플 데이터가 생성됩니다:

- **콘텐츠 생성 작업 5개**: 다양한 주제와 AI 제공자별 완성된 콘텐츠
  - 서울 여행 가이드 (여행 정보전달 템플릿)
  - 전기차 시장 분석 (시사 정보전달 템플릿)  
  - 5분 요가 루틴 (소셜 미디어 템플릿)
  - 부산 해운대 맛집 (여행 정보전달 템플릿)
  - AI 비교 분석 (시사 정보전달 템플릿)

- **테스트 결과 40개**: 각 AI 제공자별 10개씩 (성공률 90%)

## 테이블 구조

### 1. generation_jobs (콘텐츠 생성 작업)
| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | INTEGER PRIMARY KEY | 자동 증가 ID |
| job_id | TEXT UNIQUE | UUID 형태의 작업 ID |
| provider | TEXT | AI 제공자 (gemini, openai, claude, grok) |
| topic | TEXT | 생성할 주제 |
| tone | TEXT | 작성 톤 (professional, friendly, casual) |
| word_count | INTEGER | 목표 단어 수 (기본: 800) |
| include_images | BOOLEAN | 이미지 포함 여부 |
| target_language | TEXT | 대상 언어 (기본: ko) |
| status | TEXT | 상태 (pending, in_progress, completed, failed) |
| progress | INTEGER | 진행률 (0-100) |
| content | TEXT | 생성된 콘텐츠 (JSON 형태) |
| html_content | TEXT | HTML 형태 콘텐츠 |
| markdown_content | TEXT | 마크다운 형태 콘텐츠 |
| error_message | TEXT | 오류 메시지 |
| created_at | TEXT | 생성 시간 |
| updated_at | TEXT | 수정 시간 |

### 2. users (사용자)
| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | INTEGER PRIMARY KEY | 자동 증가 ID |
| username | TEXT UNIQUE | 사용자명 |
| password_hash | TEXT | 해시된 비밀번호 |
| email | TEXT UNIQUE | 이메일 |
| role | TEXT | 역할 (admin, user, validator) |
| is_active | BOOLEAN | 활성 상태 |
| created_at | TEXT | 생성 시간 |
| updated_at | TEXT | 수정 시간 |
| expires_at | TEXT | 계정 만료 시간 |
| last_login | TEXT | 마지막 로그인 |
| login_attempts | INTEGER | 로그인 시도 횟수 |
| locked_until | TEXT | 계정 잠김 해제 시간 |

### 3. login_sessions (로그인 세션)
| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | INTEGER PRIMARY KEY | 자동 증가 ID |
| user_id | INTEGER | 사용자 ID (외래키) |
| session_token | TEXT UNIQUE | 세션 토큰 |
| expires_at | TEXT | 세션 만료 시간 |
| created_at | TEXT | 생성 시간 |
| ip_address | TEXT | IP 주소 |
| user_agent | TEXT | 브라우저 정보 |

### 4. workflow_templates (워크플로우 템플릿)
| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | INTEGER PRIMARY KEY | 자동 증가 ID |
| name | TEXT | 템플릿 이름 |
| description | TEXT | 설명 |
| steps | TEXT | 워크플로우 단계 (JSON) |
| version | TEXT | 버전 (기본: v1.0) |
| status | TEXT | 상태 (active, inactive) |
| created_at | TEXT | 생성 시간 |
| updated_at | TEXT | 수정 시간 |
| created_by | INTEGER | 생성자 ID |

### 5. image_cache (이미지 캐시)
| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | INTEGER PRIMARY KEY | 자동 증가 ID |
| url_hash | TEXT UNIQUE | URL 해시값 |
| original_url | TEXT | 원본 URL |
| alt_text | TEXT | 대체 텍스트 |
| caption | TEXT | 캡션 |
| image_data | BLOB | 이미지 바이너리 데이터 |
| mime_type | TEXT | MIME 타입 |
| file_size | INTEGER | 파일 크기 |
| width | INTEGER | 이미지 너비 |
| height | INTEGER | 이미지 높이 |
| created_at | TEXT | 생성 시간 |
| last_accessed | TEXT | 마지막 접근 시간 |
| access_count | INTEGER | 접근 횟수 |

### 6. scheduled_posts (예약 포스팅)
| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | INTEGER PRIMARY KEY | 자동 증가 ID |
| schedule_id | TEXT UNIQUE | UUID 형태의 예약 ID |
| title | TEXT | 포스트 제목 |
| topic | TEXT | 사용자 지정 주제 (선택사항) |
| topic_source | TEXT | 주제 소스 (user, trend) |
| schedule_time | TEXT | 예약 실행 시간 (ISO datetime) |
| status | TEXT | 상태 (pending, completed, failed, paused) |
| provider | TEXT | AI 제공자 (gemini, openai, claude, grok) |
| workflow_template_id | INTEGER | 워크플로우 템플릿 ID (외래키) |
| repeat_config | TEXT | 반복 설정 (JSON) |
| generated_job_id | TEXT | 생성된 콘텐츠 작업 ID |
| error_message | TEXT | 오류 메시지 |
| created_at | TEXT | 생성 시간 |
| updated_at | TEXT | 수정 시간 |
| last_executed_at | TEXT | 마지막 실행 시간 |

### 7. bundles (콘텐츠 번들)
| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | INTEGER PRIMARY KEY | 자동 증가 ID |
| bundle_id | TEXT UNIQUE | UUID 형태의 번들 ID |
| title | TEXT | 번들 제목 |
| description | TEXT | 설명 |
| status | TEXT | 상태 (draft, published, archived) |
| post_count | INTEGER | 포스트 개수 |
| total_views | INTEGER | 총 조회수 |
| created_at | TEXT | 생성 시간 |
| updated_at | TEXT | 수정 시간 |
| published_at | TEXT | 발행 시간 |
| metadata | TEXT | 메타데이터 (JSON) |

### 8. test_results (테스트 결과)
| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | INTEGER PRIMARY KEY | 자동 증가 ID |
| provider | TEXT | AI 제공자 |
| prompt | TEXT | 입력 프롬프트 |
| response | TEXT | 응답 |
| success | BOOLEAN | 성공 여부 |
| error_message | TEXT | 오류 메시지 |
| token_usage | TEXT | 토큰 사용량 (JSON) |
| response_time_ms | INTEGER | 응답 시간 (밀리초) |
| created_at | TEXT | 생성 시간 |

## 기본 계정 정보
초기화 시 생성되는 기본 계정:

| 사용자명 | 비밀번호 | 역할 | 만료일 |
|----------|----------|------|--------|
| admin | admin123! | admin | 무제한 |
| validator | validator123 | validator | 1년 |
| testuser | test123 | user | 30일 |

## 기본 워크플로우 템플릿
초기화 시 생성되는 기본 템플릿:

1. **여행 정보전달** (활성)
   - 여행 가이드 및 정보 콘텐츠 전문 생성
   - 실용적인 여행 정보와 팁 중심

2. **시사 정보전달** (활성)
   - 시사 이슈 및 뉴스 정보 객관적 전달
   - 균형잡힌 시각과 다양한 관점 제시

3. **소셜 미디어 포스트** (활성)
   - SNS용 짧고 매력적인 포스트 생성
   - 상호작용 유도 중심

4. **기본 블로그 포스트** (비활성)
   - 일반적인 블로그 포스트 생성
   - 기본 템플릿으로 비활성화 상태

## 데이터베이스 연결
```python
from database import DatabaseManager

# 데이터베이스 연결
db = DatabaseManager()

# 또는 사용자 정의 경로
db = DatabaseManager("custom/path/database.db")
```

## 주요 기능

### 콘텐츠 생성 작업 관리
```python
# 작업 저장
job = GenerationJob(
    job_id="unique-uuid",
    provider="gemini",
    topic="AI의 미래",
    status="pending"
)
db.save_generation_job(job)

# 작업 조회
job = db.get_generation_job("unique-uuid")
jobs = db.get_generation_jobs(provider="gemini", status="completed")
```

### 사용자 관리
```python
# 사용자 생성
user_id = db.create_user("username", "password", "email@example.com")

# 로그인 검증
success, user, message = db.verify_user_password("username", "password")

# 세션 관리
token = db.create_session(user_id)
user = db.validate_session(token)
```

### 워크플로우 템플릿 관리
```python
# 활성 템플릿 조회
templates = db.get_active_workflow_templates()

# 특정 템플릿 조회
template = db.get_workflow_template_by_id(1)
```

### 예약 포스팅 관리
```python
# 예약 포스트 생성
scheduled_post = ScheduledPost(
    schedule_id="unique-uuid",
    title="제목",
    topic="주제",
    topic_source="user",  # user 또는 trend
    schedule_time="2025-10-18T09:30:00+09:00",
    provider="gemini",
    workflow_template_id=2
)
db.create_scheduled_post(scheduled_post)

# 예약 포스트 조회
post = db.get_scheduled_post("schedule-uuid")
posts = db.list_scheduled_posts(status="pending", limit=10)

# 실행 대기 중인 포스트 조회 (스케줄러용)
pending_posts = db.get_pending_scheduled_posts(datetime.now().isoformat())

# 예약 포스트 수정
post.status = "paused"
db.update_scheduled_post(post)

# 예약 포스트 삭제
db.delete_scheduled_post("schedule-uuid")
```

### 번들 관리
```python
# 번들 생성
bundle_id = db.create_bundle("bundle-uuid", "번들 제목", "설명")

# 번들 조회
bundle = db.get_bundle("bundle-uuid")
bundles = db.list_bundles(limit=20, offset=0)

# 번들 업데이트
db.update_bundle("bundle-uuid", title="새 제목", status="published")

# 번들 삭제
db.delete_bundle("bundle-uuid")
```

## 백업 및 복원
```bash
# 백업
cp data/aiwriter.db data/aiwriter_backup_$(date +%Y%m%d).db

# 복원
cp data/aiwriter_backup_20241012.db data/aiwriter.db
```

## 문제 해결

### 데이터베이스 파일 없음
데이터베이스 파일이 없으면 자동으로 생성됩니다. `data/` 폴더가 없는 경우 자동으로 생성됩니다.

### 권한 문제
```bash
# 폴더 권한 확인
ls -la data/
chmod 755 data/
chmod 644 data/aiwriter.db
```

### 인코딩 문제
데이터베이스는 UTF-8 인코딩을 사용합니다. 모든 텍스트는 자동으로 UTF-8로 처리됩니다.

### 마이그레이션
새로운 컬럼이나 테이블이 추가된 경우, `database.py`를 실행하면 자동으로 누락된 테이블과 인덱스가 생성됩니다:

```bash
python database.py
```

## AI가 이해해야 할 주요 정보

1. **데이터베이스 자동 초기화**: 애플리케이션 시작 시 자동으로 모든 테이블과 기본 데이터가 생성됩니다.

2. **콘텐츠 구조**: `generation_jobs.content` 필드는 JSON 형태로 저장되며, 다음 구조를 가집니다:
   ```json
   {
     "title": "제목",
     "html_content": "HTML 콘텐츠",
     "summary": "요약",
     "tags": ["태그1", "태그2"]
   }
   ```

3. **워크플로우 템플릿**: `workflow_templates.steps` 필드는 JSON 형태로 저장되며, 프롬프트 생성에 사용됩니다.

4. **인덱스 최적화**: 자주 조회되는 필드들에 대해 인덱스가 설정되어 있어 검색 성능이 최적화되어 있습니다.

5. **보안**: 비밀번호는 PBKDF2를 사용하여 안전하게 해시화되어 저장됩니다.