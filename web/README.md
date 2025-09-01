# AI Writer Web Frontend 가이드

## 프로젝트 개요
AI Writer는 React + TypeScript 기반의 AI 콘텐츠 생성 및 발행 플랫폼입니다.

## 기술 스택
- **Framework**: React 18.2.0 + TypeScript
- **Build Tool**: Vite 5.0.0
- **UI Library**: Ant Design 5.12.8
- **Styling**: Tailwind CSS 4.1.12
- **State Management**: Zustand 4.4.6
- **Data Fetching**: @tanstack/react-query 5.85.6
- **Routing**: React Router DOM 6.8.1
- **Form Handling**: React Hook Form 7.62.0
- **HTTP Client**: Axios 1.6.2

## 프로젝트 구조

```
web/
├── src/
│   ├── App.tsx              # 메인 애플리케이션 컴포넌트
│   ├── main.tsx             # React 앱 진입점
│   ├── components/          # 재사용 가능한 컴포넌트
│   │   └── layout/
│   │       ├── MainLayout.tsx      # 메인 레이아웃 (사이드바, 헤더)
│   │       └── ProtectedRoute.tsx  # 인증 보호 라우트
│   ├── pages/               # 페이지 컴포넌트
│   │   ├── Dashboard.tsx    # 대시보드 (통계, 최근 활동)
│   │   ├── Generate.tsx     # 콘텐츠 생성
│   │   ├── Jobs.tsx         # 작업 목록
│   │   ├── JobDetail.tsx    # 작업 상세
│   │   ├── Schedule.tsx     # 발행 스케줄
│   │   ├── Posts.tsx        # 포스트 관리
│   │   ├── Settings.tsx     # 설정
│   │   ├── Login.tsx        # 로그인
│   │   └── AdminUsers.tsx   # 사용자 관리 (관리자)
│   ├── router/
│   │   └── AppRouter.tsx    # 라우팅 설정
│   ├── services/
│   │   └── api.ts           # API 클라이언트 설정
│   ├── store/
│   │   └── authStore.ts     # 인증 상태 관리
│   └── types/
│       ├── auth.ts          # 인증 관련 타입
│       └── generation.ts    # 생성 관련 타입
├── package.json             # 프로젝트 설정 및 의존성
├── vite.config.ts          # Vite 설정
└── tsconfig.json           # TypeScript 설정
```

## 주요 기능

### 1. 인증 시스템
- JWT 토큰 기반 인증
- Zustand를 이용한 전역 상태 관리
- 자동 토큰 갱신 및 만료 처리
- 역할 기반 접근 제어 (user/admin)

### 2. 콘텐츠 생성
- AI 기반 콘텐츠 생성 요청
- 번들 단위 콘텐츠 관리
- 생성 작업 상태 추적

### 3. 발행 관리
- WordPress, Blogger 등 플랫폼별 발행
- 예약 발행 기능
- 발행 상태 모니터링

### 4. 대시보드
- 통계 정보 표시
- 최근 활동 내역
- 시스템 연결 상태

## 개발 환경 설정

### 필수 요구사항
- Node.js 18+
- npm 또는 yarn

### 설치 및 실행
```bash
# 의존성 설치
npm install

# 개발 서버 실행 (포트 3000)
npm run dev

# 빌드
npm run build

# 린트 검사
npm run lint

# 미리보기
npm run preview
```

## API 연동
- 백엔드 API: `http://127.0.0.1:3000/api/v1`
- Vite 프록시를 통한 `/api` 요청 라우팅
- Axios 인터셉터로 자동 인증 헤더 추가

## 라우팅 구조
```
/login              # 로그인 페이지
/dashboard          # 대시보드 (기본 경로)
/generate           # 콘텐츠 생성
/jobs               # 작업 목록
/jobs/:jobId        # 작업 상세
/schedule           # 발행 스케줄
/posts              # 포스트 관리
/settings           # 설정
/admin/users        # 사용자 관리 (관리자만)
```

## 상태 관리
- **인증**: Zustand + localStorage 영속화
- **API 데이터**: React Query를 통한 캐싱 및 동기화
- **로컬 상태**: React hooks (useState, useEffect)

## UI/UX 특징
- 한국어 인터페이스 (Ant Design 한글 로케일)
- 반응형 디자인
- 접이식 사이드바 네비게이션
- 실시간 상태 업데이트

## 개발 가이드라인
1. TypeScript 타입 안정성 유지
2. Ant Design 디자인 시스템 활용
3. React Query를 통한 서버 상태 관리
4. ESLint 규칙 준수
5. 컴포넌트 단위 모듈화