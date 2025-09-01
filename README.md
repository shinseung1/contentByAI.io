# AI Writer - Automatic Blog Posting System

🤖 AI 기반으로 WordPress와 Google Blogger에 자동으로 포스팅하는 시스템입니다.

## ✨ 주요 기능

- **🧠 AI 콘텐츠 생성**: 키워드만으로 완전한 블로그 포스트 자동 생성
- **🌐 멀티 플랫폼 지원**: WordPress, Google Blogger 동시 발행
- **🏗️ 모듈형 아키텍처**: SOLID 원칙 기반의 확장 가능한 구조
- **✅ 품질 검사**: 맞춤법, 링크, SEO 등 자동 품질 검증
- **⏰ 예약 발행**: 플랫폼별 스케줄링 기능
- **📊 Web Dashboard**: React 기반 관리 인터페이스
- **🔄 재시도 로직**: 지수 백오프를 통한 안정적 발행
- **📝 실행 로그**: 모든 작업을 추적 가능한 로그로 기록

## 🚀 빠른 시작

### Docker로 실행 (권장)

```bash
# 1. 저장소 클론
git clone <repository-url>
cd CreateAutoContentByAi

# 2. 환경변수 설정
cp .env.example .env
# .env 파일을 편집하여 API 키들을 설정

# 3. 실행
docker-compose up -d

# 4. 접속
# API: http://localhost:8000
# 웹: http://localhost:3000 (개발 환경)
```

### 🔑 기본 접속 정보

#### Admin 계정 정보
- **Admin ID**: `admin`
- **Admin Password**: `admin123!`

#### 테스트 접속 URL
- **API 서버**: http://localhost:3001 (Mac용)
- **API 문서**: http://localhost:3001/docs  
- **헬스체크**: http://localhost:3001/api/v1/health/
- **AI 제공자별 페이지**:
  - Gemini: http://localhost:3000/gemini
  - Claude: http://localhost:3000/claude  
  - OpenAI: http://localhost:3000/openai
  - Grok: http://localhost:3000/grok

### 로컬 개발 환경

```bash
# Python 환경 설정
pip install -e .

# 프론트엔드 설정  
cd web && npm install

# 개발 서버 실행
make dev
```

## 🏗️ 아키텍처

```
CreateAutoContentByAi/
├── apps/                    # 애플리케이션 계층
│   ├── api/                 # FastAPI 백엔드 서버
│   └── cli/                 # CLI 도구
├── packages/                # 핵심 비즈니스 로직
│   ├── core/                # 핵심 인프라 (설정, 로깅, 에러처리)
│   ├── gen/                 # AI 콘텐츠 생성
│   ├── media/               # 이미지 처리 및 관리
│   ├── quality/             # 콘텐츠 품질 검사
│   ├── packager/            # 포스트 번들 생성
│   └── publisher/           # 플랫폼별 발행 시스템
│       ├── wp/              # WordPress 어댑터
│       └── blogger/         # Blogger 어댑터
├── web/                     # React 프론트엔드
├── prompts/                 # AI 프롬프트
├── runs/                    # 실행 로그
└── bundles/                 # 생성된 번들
```

## 📚 문서

- **[📖 아키텍처 가이드](docs/ARCHITECTURE.md)**: 시스템 구조와 설계 원칙
- **[🛠️ 설치 및 실행 가이드](docs/SETUP.md)**: 상세한 설치 방법과 설정
- **[🔌 API 문서](docs/API.md)**: REST API 사용법과 예시

## 🎯 사용 사례

### CLI 사용법

```bash
# 콘텐츠 생성
aiw draft --topic "AI와 머신러닝의 미래" --tone professional --word-count 800

# WordPress에 발행
aiw wp:publish --bundle ./bundles/20240101_120000/ --mode publish

# Blogger에 예약 발행  
aiw blogger:publish --bundle ./bundles/20240101_120000/ --mode schedule --datetime "2024-01-02T09:00:00+09:00"

# 연결 테스트
aiw test --platform wordpress
aiw test --platform blogger

# 번들 미리보기
aiw bundle:preview ./bundles/20240101_120000/
```

### API 사용 예시

```python
import requests

# 콘텐츠 생성 요청
response = requests.post("http://localhost:8000/api/v1/generation/generate", json={
    "topic": "인공지능의 미래",
    "tone": "professional",
    "word_count": 800,
    "include_images": True
})

job_id = response.json()["job_id"]

# 발행 요청
requests.post("http://localhost:8000/api/v1/publishing/publish", json={
    "bundle_id": "bundle_20240101_120000",
    "platform": "wordpress", 
    "mode": "publish"
})
```

## 🔧 개발 명령어

### Mac용 서버 실행

```bash
# Python 서버 시작 (권장)
python3 mac_server.py

# 또는 테스트 서버 시작
python3 test_server.py

# 디버깅 모드
python3 mac_debug.py
```

### 일반 개발 명령어

```bash
# 개발 환경 설정
make dev-setup

# 개발 서버 시작
make dev

# 코드 품질 검사
make lint
make test

# Docker 빌드 및 실행
make build
make up

# 로그 확인
make logs

# 백업 및 복구
make backup
make restore BACKUP_FILE=backup.tar.gz
```

## ⚙️ 주요 설정

### 환경변수 (.env)

```bash
# AI 서비스 (필수 - 하나 이상 설정)
PRIMARY_AI_PROVIDER=gemini
GEMINI_API_KEY=AIzaSyBGJh2xvxFxIWS34Eu07HyziD_lC25leLg  # (현재 활성)
CLAUDE_API_KEY=sk-ant-your-key
OPENAI_API_KEY=sk-your-openai-key
GROK_API_KEY=xai-your-grok-key

# WordPress (선택사항)
WP_BASE_URL=https://your-site.com
WP_APP_USER=your-username
WP_APP_PASSWORD=your-app-password

# Google Blogger (선택사항)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-secret
GOOGLE_REFRESH_TOKEN=your-token
BLOGGER_BLOG_ID=your-blog-id

# 데이터베이스
DATABASE_URL=sqlite:///data/aiwriter.db

# API 서버 설정
API_HOST=127.0.0.1
API_PORT=3001  # Mac용 포트
```

## 🔒 보안 고려사항

- ✅ Application Passwords 사용 (WordPress)
- ✅ OAuth2 Refresh Token 사용 (Blogger)
- ✅ 환경변수로 민감정보 관리
- ✅ HTTPS 강제 사용
- ✅ 로그에서 민감정보 마스킹
- ✅ 레이트 리미팅 적용

## 🎨 SOLID 원칙 적용

- **S**ingle Responsibility: 각 모듈은 단일 책임
- **O**pen/Closed: 새로운 플랫폼 추가 시 기존 코드 수정 없이 확장
- **L**iskov Substitution: 모든 Publisher는 동일한 인터페이스 준수
- **I**nterface Segregation: 클라이언트별 필요한 인터페이스만 제공
- **D**ependency Inversion: 추상화에 의존, 구현체에 의존하지 않음

## 📊 시스템 상태

### 지원되는 플랫폼
- ✅ WordPress (REST API)
- ✅ Google Blogger (API v3)
- 🔄 티스토리 (계획 중)

### 개발 상태
- ✅ 핵심 아키텍처
- ✅ Publisher 모듈
- ✅ 프론트엔드 기본 구조
- 🔄 AI 콘텐츠 생성 모듈
- 🔄 이미지 처리 모듈
- 🔄 품질 검사 모듈
- 🔄 CLI 인터페이스

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🐛 버그 신고 및 문의

버그를 발견하거나 기능 요청이 있으시면 [Issues](https://github.com/your-repo/issues)에 등록해주세요.

---

**Made with ❤️ using SOLID principles and modern web technologies**