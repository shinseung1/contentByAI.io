# 개발환경 설정 가이드

## 📋 시스템 요구사항

### 필수 소프트웨어
- **Python**: 3.11+ (권장: 3.12)
- **Node.js**: 18+ (권장: 20 LTS)
- **Git**: 최신 버전
- **IDE**: VSCode, PyCharm, 또는 IntelliJ IDEA

### 권장 도구
- **Docker Desktop**: 컨테이너 실행 환경
- **Postman/Thunder Client**: API 테스트
- **Python Extension Pack** (VSCode용)
- **Prettier/ESLint Extension** (VSCode용)

## 🚀 로컬 개발환경 구축

### 1. 저장소 클론
```bash
git clone https://github.com/your-org/CreateAutoContentByAi.git
cd CreateAutoContentByAi
```

### 2. Python 가상환경 설정
```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 개발 의존성 포함 설치
pip install -e .[dev]
```

### 3. 프론트엔드 설정
```bash
cd web
npm install
cd ..
```

### 4. 환경변수 설정
```bash
# 환경변수 파일 복사
cp .env.example .env
```

`.env` 파일 편집:
```bash
# 개발환경 설정
APP_ENV=development
API_HOST=127.0.0.1
API_PORT=3001
TZ=Asia/Seoul
LOG_LEVEL=DEBUG

# 필수: AI 서비스 (하나 이상 설정)
PRIMARY_AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key

# 선택사항: 추가 AI 서비스
CLAUDE_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key
GROK_API_KEY=your_grok_api_key

# 테스트용 플랫폼 설정 (선택사항)
WP_BASE_URL=https://your-test-site.com
WP_APP_USER=test_user
WP_APP_PASSWORD=test_app_password

GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REFRESH_TOKEN=your_refresh_token
BLOGGER_BLOG_ID=your_blog_id

# 데이터베이스
DATABASE_URL=sqlite:///data/aiwriter.db
```

### 5. 개발 서버 실행

#### 방법 1: Make 명령어 사용 (권장)
```bash
# 전체 개발환경 시작
make dev

# 또는 개별 서비스 시작
# 터미널 1: API 서버
make api-dev

# 터미널 2: 웹 개발 서버
make web-dev
```

#### 방법 2: 직접 실행
```bash
# 터미널 1: Python API 서버
python mac_server.py
# 또는
uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 3001

# 터미널 2: React 개발 서버
cd web
npm run dev
```

### 6. 접속 확인
- **API 서버**: http://localhost:3001
- **웹 대시보드**: http://localhost:3001 (Vite 프록시)
- **API 문서**: http://localhost:3001/docs
- **헬스체크**: http://localhost:3001/api/v1/health/

## 🔧 개발 도구 설정

### VSCode 설정 (.vscode/settings.json)
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "typescript.preferences.includePackageJsonAutoImports": "on",
  "eslint.format.enable": true
}
```

### 권장 VSCode 확장
```bash
# Python 개발
ms-python.python
ms-python.mypy-type-checker
charliermarsh.ruff

# TypeScript/React 개발
bradlc.vscode-tailwindcss
ms-vscode.vscode-typescript-next
esbenp.prettier-vscode
ms-vscode.eslint

# 일반 개발
ms-vscode.thunder-client
eamodio.gitlens
```

## 🧪 테스트 환경

### Python 테스트 실행
```bash
# 전체 테스트
pytest

# 커버리지 포함
pytest --cov=packages --cov-report=html

# 특정 테스트 파일
pytest tests/test_publisher.py

# 마킹된 테스트만
pytest -m integration
```

### 프론트엔드 테스트
```bash
cd web

# 린트 검사
npm run lint

# 타입 체크
npx tsc --noEmit

# 빌드 테스트
npm run build
```

## 🔍 코드 품질 도구

### Python 린팅/포맷팅
```bash
# Ruff 린팅
ruff check .

# Ruff 포맷팅  
ruff format .

# MyPy 타입 체크
mypy .

# 전체 검사
make lint
```

### 프론트엔드 린팅/포맷팅
```bash
cd web

# ESLint
npm run lint

# Prettier (package.json에 설정 추가 필요)
npx prettier --write src/
```

## 🐛 디버깅 설정

### Python 디버깅
```bash
# 디버깅 모드로 서버 실행
python mac_debug.py

# 또는 환경변수 설정
DEBUG=True python mac_server.py
```

### VSCode 디버그 설정 (.vscode/launch.json)
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: API Server",
      "type": "python",
      "request": "launch",
      "program": "mac_server.py",
      "console": "integratedTerminal",
      "env": {
        "PYTHONPATH": "${workspaceFolder}",
        "DEBUG": "True"
      }
    },
    {
      "name": "Python: Test",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["${workspaceFolder}/tests"],
      "console": "integratedTerminal"
    }
  ]
}
```

## 📊 로컬 데이터베이스

### SQLite 데이터베이스 관리
```bash
# 데이터베이스 파일 확인

#cmd
ls -la data/aiwriter.db
#powershell
Get-ChildItem -Force data/aiwriter.db


# SQLite CLI 접근
sqlite3 data/aiwriter.db

# 테이블 구조 확인
.schema

# 데이터 조회 예시
SELECT * FROM bundles ORDER BY created_at DESC LIMIT 10;
```

## 🎯 개발 워크플로우

### 새 기능 개발 프로세스
1. **브랜치 생성**: `git checkout -b feature/새기능명`
2. **개발환경 시작**: `make dev`
3. **코드 작성**: TDD 방식 권장
4. **테스트 실행**: `make test`
5. **코드 품질 검사**: `make lint`
6. **커밋**: 의미있는 커밋 메시지 작성
7. **PR 생성**: 코드 리뷰 요청

### 브랜치 전략
- `main`: 프로덕션 릴리스
- `dev_v1`: 개발 브랜치 (현재 작업 브랜치)
- `feature/*`: 기능 개발
- `hotfix/*`: 긴급 수정

## 🔗 유용한 개발 명령어

### 프로젝트 관리
```bash
# 개발환경 초기 설정
make dev-setup

# 전체 테스트 및 린트
make test && make lint

# 코드 포맷팅
make format

# 백업 생성
make backup

# 서비스 상태 확인
make health
```

### 디버깅 및 로그
```bash
# 실시간 로그 확인
tail -f logs/aiwriter.log

# API 요청 테스트
curl http://localhost:3001/api/v1/health/

# 생성된 번들 확인
ls -la bundles/

# 실행 로그 확인
ls -la runs/
```

## 🔧 트러블슈팅

### 자주 발생하는 문제

#### 1. 포트 충돌
```bash
# 포트 사용 프로세스 확인
netstat -ano | findstr :3001  # Windows
lsof -i :3001                 # macOS/Linux

# 프로세스 종료 후 재시작
```

#### 2. Python 의존성 문제
```bash
# 가상환경 재생성
deactivate
rm -rf venv
python -m venv venv
# 가상환경 활성화 후
pip install -e .[dev]
```

#### 3. Node.js 의존성 문제
```bash
cd web
rm -rf node_modules package-lock.json
npm install
```

#### 4. 데이터베이스 초기화
```bash
# 데이터베이스 재생성
rm data/aiwriter.db
# 서버 재시작하면 자동으로 테이블 생성됨
```

이 가이드를 따라하면 로컬 개발환경을 성공적으로 구축할 수 있습니다.