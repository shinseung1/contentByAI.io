# AI Writer 설치 및 실행 가이드

## 시스템 요구사항

### 필수 요구사항
- **Python**: 3.11 이상
- **Node.js**: 18 이상
- **Docker**: 20.10 이상
- **Docker Compose**: 2.0 이상

### 권장 사양
- **RAM**: 최소 4GB, 권장 8GB
- **디스크**: 최소 10GB 여유공간
- **OS**: Windows 10/11, macOS 10.15+, Ubuntu 20.04+

## 설치 방법

### 방법 1: Docker를 사용한 설치 (권장)

#### 1. 저장소 클론
```bash
git clone <repository-url>
cd CreateAutoContentByAi
```

#### 2. 환경변수 설정
```bash
cp .env.example .env
```

`.env` 파일을 편집하여 필요한 설정을 입력하세요:

```bash
# 애플리케이션 설정
APP_ENV=production
TZ=Asia/Seoul

# WordPress 설정 (선택)
WP_BASE_URL=https://your-wordpress-site.com
WP_APP_USER=your-username
WP_APP_PASSWORD=your-app-password

# Google Blogger 설정 (선택)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret  
GOOGLE_REFRESH_TOKEN=your-refresh-token
BLOGGER_BLOG_ID=your-blog-id

# AI 서비스 설정 (필수)
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key
# 또는
# AI_PROVIDER=openai
# OPENAI_API_KEY=your-openai-api-key
```

#### 3. 애플리케이션 실행
```bash
# 프로덕션 환경
docker-compose up -d

# 개발 환경
make dev
# 또는
docker-compose -f docker-compose.dev.yml up
```

#### 4. 접속 확인
- **API**: http://localhost:8000
- **웹 대시보드**: http://localhost:3000 (개발 환경)
- **API 문서**: http://localhost:8000/docs

### 방법 2: 로컬 개발 환경 설치

#### 1. Python 환경 설정
```bash
# Python 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 가상환경 활성화 (macOS/Linux)
source venv/bin/activate

# 의존성 설치
pip install -e .
```

#### 2. 프론트엔드 설정
```bash
cd web
npm install
```

#### 3. 데이터베이스 초기화
```bash
# 데이터 디렉토리 생성
mkdir -p data logs runs bundles

# 데이터베이스 테이블 생성 (애플리케이션 첫 실행시 자동)
```

#### 4. 개발 서버 실행

**터미널 1: 백엔드 서버**
```bash
make api-dev
# 또는
uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
```

**터미널 2: 프론트엔드 서버**
```bash
make web-dev
# 또는
cd web && npm run dev
```

## 플랫폼별 설정

### WordPress 설정

#### 1. Application Passwords 생성
1. WordPress 관리자 페이지 → 사용자 → 프로필
2. "Application Passwords" 섹션에서 새 패스워드 생성
3. 생성된 패스워드를 `.env` 파일의 `WP_APP_PASSWORD`에 설정

#### 2. 권한 확인
사용자에게 다음 권한이 필요합니다:
- `edit_posts`: 게시물 작성
- `upload_files`: 파일 업로드
- `manage_categories`: 카테고리 관리

#### 3. REST API 활성화 확인
```bash
curl https://your-site.com/wp-json/wp/v2/posts
```

### Google Blogger 설정

#### 1. Google Cloud Console 설정
1. [Google Cloud Console](https://console.cloud.google.com) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. "API 및 서비스" → "라이브러리"에서 Blogger API 활성화
4. "사용자 인증 정보" → "OAuth 2.0 클라이언트 ID" 생성

#### 2. OAuth2 토큰 획득
```python
# 임시 스크립트 실행하여 refresh_token 획득
from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_config(
    {
        "web": {
            "client_id": "your-client-id",
            "client_secret": "your-client-secret",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    },
    scopes=['https://www.googleapis.com/auth/blogger']
)

credentials = flow.run_local_server(port=0)
print(f"Refresh Token: {credentials.refresh_token}")
```

#### 3. 블로그 ID 확인
```bash
curl "https://www.googleapis.com/blogger/v3/blogs/byurl?url=YOUR_BLOG_URL&key=YOUR_API_KEY"
```

## CLI 사용법

### 기본 명령어

```bash
# 도움말
aiw --help

# 콘텐츠 생성
aiw draft --topic "인공지능의 미래" --tone professional --word-count 800

# WordPress에 발행
aiw wp:publish --bundle ./bundles/20240101_120000/ --mode publish

# Blogger에 예약 발행
aiw blogger:publish --bundle ./bundles/20240101_120000/ --mode schedule --datetime "2024-01-01T09:00:00+09:00"

# 번들 미리보기
aiw bundle:preview ./bundles/20240101_120000/

# 실행 로그 리플레이
aiw replay --run runs/20240101T000000Z.jsonl

# 연결 테스트
aiw test --platform wordpress
aiw test --platform blogger
```

### 배치 작업

```bash
# 여러 주제로 일괄 생성
aiw batch:generate topics.txt --output ./bundles/batch/

# 예약 발행 (매일 오전 9시)
aiw scheduler:add --bundle ./bundles/sample/ --platforms wordpress,blogger --time "09:00" --days mon,tue,wed,thu,fri
```

## 개발 워크플로우

### 개발 환경 시작

```bash
# 전체 개발 환경
make dev-setup  # 초기 설정
make dev        # 개발 서버 시작

# 개별 서비스
make api-dev    # API 서버만
make web-dev    # 프론트엔드만
```

### 코드 품질 검사

```bash
# 린팅
make lint
# 또는
ruff check .
mypy .

# 포맷팅
make format
# 또는
ruff format .

# 테스트
make test
# 또는
pytest
```

### 빌드 및 배포

```bash
# Docker 이미지 빌드
make build

# 프로덕션 배포
make up

# 로그 확인
make logs

# 서비스 중지
make down

# 전체 정리
make clean
```

## 문제 해결

### 자주 발생하는 문제

#### 1. 포트 충돌
```bash
# 사용 중인 포트 확인
netstat -an | grep :8000
netstat -an | grep :3000

# Docker 컨테이너 정리
docker-compose down
docker system prune
```

#### 2. 권한 오류 (Linux/macOS)
```bash
# Docker 권한 설정
sudo usermod -aG docker $USER
newgrp docker

# 파일 권한 수정
sudo chown -R $USER:$USER .
chmod +x scripts/*.sh
```

#### 3. Python 패키지 의존성 문제
```bash
# 가상환경 재생성
rm -rf venv
python -m venv venv
source venv/bin/activate  # 또는 venv\Scripts\activate
pip install --upgrade pip
pip install -e .
```

#### 4. Node.js 패키지 문제
```bash
# 노드 모듈 재설치
cd web
rm -rf node_modules package-lock.json
npm install
```

### API 연결 문제

#### WordPress 연결 오류
```bash
# REST API 접근 테스트
curl -u "username:app-password" https://your-site.com/wp-json/wp/v2/users/me

# SSL 인증서 문제 시
curl -k https://your-site.com/wp-json/wp/v2/posts
```

#### Blogger 인증 오류
```bash
# OAuth 토큰 갱신
aiw auth:refresh --platform blogger

# API 호출 테스트
curl "https://www.googleapis.com/blogger/v3/blogs/BLOG_ID?key=API_KEY"
```

### 로그 확인

#### 애플리케이션 로그
```bash
# 실시간 로그 확인
tail -f logs/aiwriter.log

# 특정 레벨 로그만
grep "ERROR" logs/aiwriter.log

# Docker 컨테이너 로그
docker-compose logs -f app
```

#### 실행 로그 분석
```bash
# 최근 실행 로그
ls -la runs/

# 특정 실행 로그 확인
cat runs/20240101T000000Z.jsonl | jq .

# 실패한 작업 필터링
cat runs/*.jsonl | jq 'select(.status=="failed")'
```

## 운영 가이드

### 백업

```bash
# 데이터 백업
make backup

# 수동 백업
tar -czf backup-$(date +%Y%m%d_%H%M%S).tar.gz data/ bundles/ runs/
```

### 복구

```bash
# 백업에서 복구
make restore BACKUP_FILE=backup-20240101_120000.tar.gz
```

### 모니터링

```bash
# 헬스체크
make health
# 또는
curl http://localhost:8000/api/v1/health/

# 시스템 리소스 확인
docker stats

# 디스크 사용량 확인
du -sh data/ logs/ runs/ bundles/
```

### 스케일링

#### 수평 확장
```yaml
# docker-compose.yml 수정
services:
  app:
    deploy:
      replicas: 3
```

#### 수직 확장
```yaml
# 리소스 제한 설정
services:
  app:
    mem_limit: 2g
    cpus: '1.0'
```

이 가이드를 따라하시면 AI Writer 시스템을 성공적으로 설치하고 운영할 수 있습니다. 추가 질문이 있으시면 [이슈](https://github.com/your-repo/issues)를 생성해주세요.