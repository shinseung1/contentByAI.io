# AI 기반 자동 포스팅 프로그램 요구사항 명세서 (WordPress + Google Blogger)

> **목표**  
> 티스토리는 제외합니다. **WordPress**와 **Google Blogger(블로그스팟)** 에 각각 **완전 자동**으로 글을 올리는 Python + React 기반 프로그램을 만듭니다.  
> 생성형 AI(예: Claude)는 *콘텐츠 생성·리라이트·SEO 메타 산출*에 집중하고, 본 프로그램은 *번들 표준화 → 품질검사 → 게시(예약/발행)* 를 담당합니다.

---

## 0) 범위 & 정의

- **대상 플랫폼**
  - **WordPress**: REST API(Posts/Media/Terms)로 글/이미지 업로드, 예약 발행.
  - **Google Blogger**: Blogger API v3로 초안 작성, 예약/발행.
- **제외**: 티스토리, 네이버 블로그.
- **포스트 번들(Post Bundle)**: 생성 모듈이 만든 **표준화된 산출물**(HTML + 메타 JSON + 이미지들). 퍼블리셔(WordPress/Blogger)가 동일 규격을 소비.

---

## 1) 상위 요구사항 (What & Why)

1. 키워드 입력만으로 **아웃라인 → 초안 → 리라이트/SEO → 이미지 → 품질검사 → 예약/발행**까지 자동화.
2. **플랫폼별 상이한 설정**(카테고리/태그/라벨/슬러그/대표이미지/예약 시각)을 지원.
3. **재현 가능한 로그 & 리플레이**: 모든 외부 호출/응답/프롬프트 해시를 JSONL로 보존.
4. **모듈형 구조**: 퍼블리셔(출력 채널)를 쉽게 추가/교체 가능.

---

## 2) 기술 스택

- **백엔드**: Python 3.11+, FastAPI, Pydantic Settings, APScheduler  
- **프런트엔드**: React 18 + Vite + Zustand(or Redux) + Ant Design(or MUI)  
- **데이터**: SQLite(메타/로그/매핑 캐시), 파일시스템(번들/이미지 캐시)  
- **CI/CD**: Docker + docker-compose (개발=운영 환경 일치)  
- **테스트**: Pytest + VCR.py(외부 API 호출 녹화/재현), mypy, ruff

---

## 3) 아키텍처

```
apps/
  api/            # FastAPI: REST + 대시보드 백엔드
  cli/            # 운영 CLI (draft/publish/schedule/replay)
packages/
  gen/            # (AI 호출 어댑터) 키워드→아웃라인→초안→SEO 메타
  media/          # 이미지 공급자(스톡/생성/보유소스) + 후처리(WebP/ALT)
  quality/        # 맞춤법/링크 404/유사도/워드카운트/금칙어 검사
  packager/       # 번들 생성(post.html, meta.json, images/)
  publisher/
    wp/           # WordPress REST 어댑터 (posts, media, terms)
    blogger/      # Blogger v3 어댑터 (insert/publish/update)
  core/           # 스케줄러, 백오프 재시도, 로깅(JSONL), 공통 에러
prompts/          # 프롬프트 버전 관리
runs/             # 실행 로그 스냅샷(.jsonl)
bundles/          # 생성된 포스트 번들 저장소
```

**파이프라인 단계**  
키워드 → 리서치 요약(출처) → 아웃라인 → 초안 → 리라이트/SEO → 이미지(선택) → 품질검사 → **번들 산출** → **게시(예약/발행)** → 로그/리플레이 저장

---

## 4) 환경 변수(.env)

```dotenv
APP_ENV=dev
TZ=Asia/Seoul

# WordPress
WP_BASE_URL=https://your-wp-site.com
WP_APP_USER=editor@your-wp-site.com
WP_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx  # Application Passwords

# Blogger (Google)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REFRESH_TOKEN=...             # offline access
BLOGGER_BLOG_ID=1234567890123456789  # 대상 블로그 ID

# 이미지 공급자
IMAGE_PROVIDER=stock|gen|custom
UNSPLASH_ACCESS_KEY=...
S3_BUCKET=...
S3_REGION=ap-northeast-2
S3_PUBLIC_BASE=https://cdn.example.com  # 퍼블릭 URL prefix
```

---

## 5) 포스트 번들 스키마(표준 계약)

### 5.1 `meta.json`
```json
{
  "title": "예시 제목",
  "slug": "yesi-jemok",                 // 선택: WP에 우선 적용
  "excerpt": "요약문(SEO Description)",
  "categories": ["security","forensics"], // WP 카테고리명 (퍼블리셔가 ID 매핑)
  "tags": ["incident-response","tips"],   // WP 태그명
  "labels": ["보안","포렌식"],            // Blogger 라벨
  "schedule": {
    "mode": "draft|publish|schedule",
    "datetime": "2025-09-01T09:00:00+09:00" // 앱 TZ (Asia/Seoul)
  },
  "featured_image": "images/hero.webp"     // 선택
}
```

### 5.2 `post.html`
- 완전한 본문 HTML(H1/H2/H3 구조, 내부 목차 가능)
- `<img>` 태그 src는 로컬 경로나 플레이스홀더일 수 있어도 됨 → 퍼블리셔가 업로드/치환

### 5.3 `images/…` (+ `images.json` 선택)
```json
[
  {
    "path": "images/hero.webp",
    "alt": "주제를 요약한 접근성 설명",
    "caption": "Photo by Alice on Example",
    "source_url": "https://example.com/img.jpg",
    "license": "CC BY 4.0",
    "attribution_required": true,
    "use_as_featured": true
  }
]
```

---

## 6) 퍼블리셔 동작 명세

### 6.1 WordPress 퍼블리셔
- **인증**: Application Passwords (Basic Auth)
- **미디어 업로드**: `/wp-json/wp/v2/media` 로 `featured_image` 업로드 → 응답 `id` 를 `featured_media`에 설정
- **카테고리/태그 매핑**
  - 이름→ID 캐시; 미존재 시 선생성 후 ID 사용
- **글 생성**: `/wp-json/wp/v2/posts`
  - `status`: `draft | publish | future`
  - `date`: 예약 시 사이트 타임존 기준(서버/사이트 TZ 일치 필요)
  - 페이로드 예:
    ```json
    {
      "title": "예시 제목",
      "content": "<h1>...</h1> ...",
      "status": "future",
      "date": "2025-09-01T09:00:00",
      "slug": "yesi-jemok",
      "categories": [12,34],
      "tags": [56,78],
      "featured_media": 1234
    }
    ```

### 6.2 Blogger 퍼블리셔
- **인증**: OAuth2(offline refresh token 보유), scope: `https://www.googleapis.com/auth/blogger`
- **초안 생성**: `posts.insert(blogId, isDraft=true, body={title, content, labels})`
- **예약/발행**: `posts.publish(blogId, postId, publishDate=RFC3339)`  
  - 권장: 내부에서 `Asia/Seoul` → **UTC RFC3339**로 변환 후 publish
- **이미지**: 전용 업로드 API가 제한적 → **S3/GCS/CDN 업로드 후 퍼블릭 URL**을 `post.html` 내 `<img src>`로 치환

---

## 7) 스케줄링 & 레이트 리밋

- **APScheduler**: 즉시 예약 등록(두 플랫폼에 각각 API 호출)
  - WP: `status=future` + `date(사이트 TZ)`
  - Blogger: `posts.publish(..., publishDate=UTC RFC3339)`
- **레이트 리밋/백오프**: 연속 게시 시 랜덤 지연 + 지수 백오프(Jitter)  
- **쿼터 대응**: Google API 403(쿼터 초과) 시 재시도 정책 적용

---

## 8) 에러 처리 & 리플레이

- **에러 분류**
  - `RetryableError`: 5xx/네트워크/쿼터 초과
  - `FatalError`: 4xx 인증/권한/요청 형식 오류
- **재시도 정책**: 1s→2s→4s→8s→16s (+Jitter), 최대 5회
- **부분 롤백**
  - WP: 미디어 업로드 성공 후 글 실패 → 고아 미디어 정리
  - Blogger: 초안 생성 실패 → 로그 기록만
- **리플레이**
  - `runs/{timestamp}.jsonl` 저장(입력/프롬프트 해시/요청/응답/결과)
  - `aiw replay --run <file>` 로 재실행 가능

---

## 9) 품질검사(quality)

- **맞춤법/문장부호/반복어**
- **링크 404 검사**(본문 내 a[href] 전수 확인)
- **유사도(표절 근사)**: pHash/text simhash or embedding 유사도
- **워드카운트 규칙**: 본문 최소/최대, H2/H3 균형
- **금칙어/민감어 필터**
- **SEO 체크**: H1=1개, 메타 설명 길이, 키워드 밀도 대략

결과는 대시보드 체크리스트 + `bundle/report.json` 저장

---

## 10) React 대시보드(선택)

- **페이지**
  - 대시보드: 최근 실행/예약 현황 카드
  - 번들 미리보기: `post.html` 렌더, 이미지/ALT/캡션 표시
  - 품질 리포트: 체크리스트(Pass/Fail) + 상세 사유
  - 스케줄 캘린더: 플랫폼별 예약 현황
  - 로그 뷰어: `runs/*.jsonl` 라인 뷰 & 검색
- **액션**
  - 수동 재시도/취소
  - 번들 생성 트리거(키워드/톤/길이/이미지 정책)
- **상태 표시**
  - 인증 만료/권한 에러/쿼터 경보
- **상태관리**: Zustand(or Redux), SWR(or React Query)로 API 연동

---

## 11) CLI 명령(최소)

```bash
# 키워드로 번들 생성 (초안 + 이미지 + 메타)
aiw draft --topic "키워드..."

# 번들 미리보기 (터미널/브라우저)
aiw bundle:preview ./bundles/2025-09-01-sample/

# 워드프레스 예약/발행
aiw wp:publish --bundle ./bundles/... \
  --mode schedule --datetime "2025-09-01T09:00:00+09:00"

# 블로거 예약/발행 (UTC RFC3339)
aiw blogger:publish --bundle ./bundles/... \
  --datetime "2025-09-01T00:00:00Z"

# 리플레이(실패 재현)
aiw replay --run runs/2025-09-01T00-00-00Z.jsonl
```

---

## 12) 보안 & 컴플라이언스

- 비밀값은 **.env + OS 비밀 저장소** 사용, 저장소 커밋 금지.
- 외부 이미지/텍스트 **저작권/라이선스 준수**, 인물/상표권 주의.
- HTTPS 기본, 대시보드의 CORS/CSRF 최소 허용 원칙.
- **공식 API만 사용**(WP REST, Blogger v3). 봇 방지 우회/비공개 엔드포인트 호출 금지.

---

## 13) 테스트(AC 기준의 예)

- **계약 테스트**
  - 번들 스키마 100% 일치(필수 필드/타입/값 범위)
  - 퍼블리셔 입력 스키마 검증
- **통합/E2E**
  - 샘플 키워드로 번들 생성 → WP 예약 1건, Blogger 예약 1건 **성공**
  - WP: `draft/publish/future` 3모드 모두 확인, `featured_media` 연결
  - Blogger: `insert(isDraft=true)` 후 `publish(publishDate)` 정상 동작
- **회귀 방지**
  - 번들 diff(HTML/메타/이미지 해시) 비교, 링크 404 리그레션 감시
- **관측 가능성**
  - 모든 실행은 `runs/*.jsonl`에 **요청/응답/프롬프트 해시** 포함

---

## 14) 구현 우선순위(로드맵)

1) **Blogger 퍼블리셔**: `insert → publish(예약)`  
2) **WP 퍼블리셔**: Media 업로드 → Post 생성(예약/발행)  
3) **번들/품질검사**: 표준화·체크리스트 → 실패 로그 구조  
4) **CLI & 대시보드**: 운영 UX(미리보기/재시도/캘린더)  
5) **이미지 공급자 확장**: 스톡 API/생성형/보유소스 전략  
6) **카테고리/태그 동기화 캐시**(WP) + 라벨 자동 제안(Blogger)

---

## 15) 수락 기준(AC)

- **WP**: `/wp-json/wp/v2/media` 업로드 후 `featured_media` 연결, `/wp-json/wp/v2/posts` 로  
  - `draft/publish/future` 모드 모두 동작,  
  - 카테고리/태그 **이름→ID 매핑 자동**,  
  - 예약 시각 **사이트 타임존 기준** 정확 적용.
- **Blogger**: `posts.insert(isDraft=true)` 초안 생성, `posts.publish(publishDate)`로 **예약 발행** 성공(UTC RFC3339).  
- 한 번의 실행으로 **두 플랫폼 각각 10건 이상** 연속 예약 등록 성공(레이트 리밋/백오프 적용).  
- 실패 시 **지수 백오프 재시도(최대 5회)** 후 명확한 에러 로그 남김, `aiw replay` 로 재현 가능.  
- 모든 실행은 `runs/*.jsonl`에 기록(요청/응답/프롬프트 해시/환경 요약).

---

## 16) 참고용 의사코드

### 16.1 WordPress 클라이언트
```python
import base64, requests
from datetime import datetime

class WPClient:
    def __init__(self, base_url, user, app_password):
        token = base64.b64encode(f"{user}:{app_password}".encode()).decode()
        self.h = {"Authorization": f"Basic {token}"}
        self.base = base_url.rstrip("/")

    def upload_media(self, path, filename):
        url = f"{self.base}/wp-json/wp/v2/media"
        with open(path, "rb") as f:
            r = requests.post(url, headers={**self.h, "Content-Disposition": f'attachment; filename="{filename}"'}, data=f)
        r.raise_for_status()
        return r.json()["id"]

    def ensure_term_ids(self, taxonomy, names):
        # 이름→ID 캐시/조회/생성 로직 (카테고리/태그)
        ...

    def create_post(self, title, html, status, date, slug, cat_ids, tag_ids, featured_id=None):
        url = f"{self.base}/wp-json/wp/v2/posts"
        payload = {
            "title": title, "content": html, "status": status, "slug": slug,
            "date": date, "categories": cat_ids, "tags": tag_ids
        }
        if featured_id: payload["featured_media"] = featured_id
        r = requests.post(url, headers=self.h, json=payload)
        r.raise_for_status()
        return r.json()["id"]
```

### 16.2 Blogger 클라이언트
```python
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

class BloggerClient:
    def __init__(self, client_id, client_secret, refresh_token):
        self.creds = Credentials(None, refresh_token=refresh_token,
                                 token_uri="https://oauth2.googleapis.com/token",
                                 client_id=client_id, client_secret=client_secret,
                                 scopes=["https://www.googleapis.com/auth/blogger"])
        self.svc = build("blogger", "v3", credentials=self.creds, cache_discovery=False)

    def insert_draft(self, blog_id, title, html, labels):
        body = {"title": title, "content": html, "labels": labels}
        return self.svc.posts().insert(blogId=blog_id, isDraft=True, body=body).execute()["id"]

    def publish(self, blog_id, post_id, publish_rfc3339):
        return self.svc.posts().publish(blogId=blog_id, postId=post_id, publishDate=publish_rfc3339).execute()
```
