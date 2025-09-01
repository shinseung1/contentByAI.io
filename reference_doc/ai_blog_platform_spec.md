# AI 자동 블로그 포스팅 플랫폼 — 제품/기술 요청서 (Python + React)

> 이 문서는 **AI 기반 자동 블로그 포스팅 플랫폼**의 요구사항을 명확히 전달하기 위한 **한 장짜리(이상) 스펙**입니다.  
> 백엔드는 **Python(FastAPI)**, 프런트엔드는 **React**를 기준으로 합니다. 필요하다면 데이터베이스/큐/스케줄러 등 **필요한 모든 구성요소 추가를 허용**합니다.

---

## TL;DR
- **목표**: 사용자가 로그인하여 AI에게 글 생성을 요청하고, 예약 발송하며, 결과/히스토리를 관리할 수 있는 **웹앱** 구축
- **대시보드** 포함: 실행 현황, 최근 작업, 실패/경고 알림, 리소스 사용량 등
- **권한**: 일반 사용자, **관리자(admin)**. 로그인 페이지에서 admin 계정으로 로그인하면 **사용자 관리 화면**으로 이동
- **예약/백그라운드 작업**: 예약 발송과 대량 작업을 처리하는 워커/스케줄러 구성
- **확장**: WordPress 등 외부 블로그 채널 연동 가능 (멀티 채널 설계)

---

## 사용자 스토리
1. 사용자로 로그인하여 **대시보드**에서 최근 생성 작업/상태를 본다.
2. **콘텐츠 생성 요청** 화면에서 주제/톤/단어수/이미지 포함 여부/언어를 설정하고 **생성 요청**을 등록한다.
3. 즉시 실행 또는 **예약 발송**을 선택한다.
4. **작업 내역(히스토리)**에서 상태(대기/진행/완료/실패)와 로그를 확인한다.
5. 완료된 결과를 **미리보기/수정** 후 채널(WordPress 등)에 발송한다.
6. **관리자**는 사용자/권한/요금제(옵션)/API Key를 관리한다.

---

## 화면 (React)
- **/login**: 로그인 (admin일 경우 로그인 성공 시 **/admin/users**로 이동)
- **/dashboard**: 대시보드(카드/차트/알림)
- **/generate**: 콘텐츠 생성 폼(주제/톤/단어수/이미지/언어) + “즉시 실행/예약”
- **/jobs**: 작업 목록(필터/페이지네이션) + 상세(프롬프트/출력/로그)
- **/schedule**: 예약 작업 목록/생성/수정
- **/posts**: 생성된 콘텐츠 관리(미리보기/편집/발송)
- **/admin/users**: 사용자 관리(목록/생성/비활성/역할부여)
- **/settings**: 채널/오픈AI 키/웹훅 등 설정

### 프런트 설계 제안
- 라우팅: **React Router**
- 상태: **React Query**(Server State) + **Zustand/Redux Toolkit**(UI/Session)
- UI: Tailwind(또는 shadcn/ui) / 컴포넌트 단위(카드/테이블/폼/모달)
- 인증: 로그인 성공 시 **JWT 보관(메모리 + Refresh)**, 보호 라우트(HOC)

---

## 백엔드 (Python / FastAPI)
### 핵심 엔드포인트(예시)
- `POST /auth/login` → JWT 발급
- `GET /me` → 내 정보
- `POST /generation/generate` → 콘텐츠 생성 Job 생성(비동기)  
- `GET /generation/jobs/{job_id}` → Job 상태/결과 조회  
- `GET /generation/jobs` → Job ID 리스트
- `POST /schedule` / `GET /schedule` / `DELETE /schedule/{id}` → 예약 CRUD
- `POST /posts/publish` → 채널 발송(WordPress 등)
- `GET /history` → 활동 로그/결과 검색
- `GET /admin/users` / `POST /admin/users` / `PATCH /admin/users/{id}` → 사용자 관리

### 비동기/스케줄링
- **선택1)** `APScheduler + FastAPI BackgroundTasks` (간단/내장형)
- **선택2)** `Celery/RQ + Redis` (규모/안정성/분리된 워커)

---

## 권한/역할(RBAC)
- **role**: `user`, `admin`
- 경로 보호: `/admin/**` → `admin`만
- 미들웨어에서 JWT 디코드 → `request.state.user` 주입 → 데코레이터로 권한 체크

---

## 데이터베이스 설계 (PostgreSQL 예시)
> 필요 시 ORM은 **SQLAlchemy**(또는 Prisma/Drizzle for TS Backend 전환 시)

### 테이블
- `users`: id, email, password_hash, role, status, created_at, updated_at
- `api_keys`: id, user_id(FK), provider, key_alias, encrypted_key, created_at
- `jobs`: id(uuid), user_id, topic, tone, word_count, include_images, lang, status(enum: queued|running|done|failed), scheduled_at, started_at, finished_at, error_message
- `job_outputs`: id, job_id(FK), html, excerpt, images(json), tokens_used, model_info, meta(json)
- `schedules`: id, user_id, cron_or_datetime, payload(json), active
- `channels`: id, user_id, type(wordpress,…), config(json), active
- `posts`: id, job_id(FK), channel_id(FK), external_id, status, published_at
- `audit_logs`: id, user_id, action, target, payload(json), created_at

간단 DDL 스니펫:
```sql
create table users (
  id serial primary key,
  email text unique not null,
  password_hash text not null,
  role text not null default 'user',
  status text not null default 'active',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table jobs (
  id uuid primary key,
  user_id int references users(id),
  topic text not null,
  tone text,
  word_count int,
  include_images boolean default true,
  lang text default 'ko',
  status text not null default 'queued',
  scheduled_at timestamptz,
  started_at timestamptz,
  finished_at timestamptz,
  error_message text
);
```

---

## 인증/보안
- **JWT(Access + Refresh)**, 만료/블랙리스트(옵션)
- 비밀번호 해시: **Argon2id** 또는 **bcrypt**
- CORS/Rate limit/역할 기반 접근제어
- 시크릿/키는 `.env` 또는 Vault에 보관

---

## 워크플로 (예시)
1. 로그인(`/auth/login`) → JWT
2. `/generation/generate`로 생성 요청 → `job_id` 발급
3. 워커가 모델 호출/이미지 처리 → `job_outputs` 저장
4. `/generation/jobs/{job_id}`로 상태 폴링 또는 웹소켓/웹훅
5. `/posts/publish` 로 채널 발송 (WP REST API 등)

---

## 샘플 API 호출 (curl)
```bash
# 로그인
curl -sS -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret"}'

# 생성 요청
curl -sS -X POST http://localhost:8000/generation/generate \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "topic":"AI로 블로그 자동화하기",
    "tone":"professional",
    "word_count":900,
    "include_images":true,
    "target_language":"ko"
  }'

# 상태 조회
curl -sS http://localhost:8000/generation/jobs/<JOB_ID> \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

---

## 관리자 플로우
- 로그인 후 `role=admin`이면 `/admin/users`로 라우팅
- 사용자 목록/검색/잠금, API Key 발급/회수, 채널 설정 정책 관리
- 대시보드에 시스템 큐 길이/실패율/에러 로그 카드

---

## 프런트 구조(예시)
```
src/
  app/
    routes.tsx
    providers.tsx
  pages/
    Login.tsx
    Dashboard.tsx
    Generate.tsx
    Jobs.tsx
    JobDetail.tsx
    Schedule.tsx
    Posts.tsx
    AdminUsers.tsx
    Settings.tsx
  components/
    forms/, tables/, charts/, modals/
  store/ (Zustand or RTK)
  api/ (React Query hooks)
  utils/
```

---

## 배포/운영
- Docker Compose (web, api, db, redis/worker)
- .env (DB_URI, JWT_SECRET, OPENAI_API_KEY, WP_CREDS 등)
- 로깅/모니터링: OpenTelemetry + Grafana/Loki(옵션)
- 마이그레이션: Alembic

---

## 수락 기준(예)
- 로그인/권한 분기(관리자 전용 메뉴 노출) 동작
- 생성 요청 → Job 생성 → 완료 후 결과 열람/발송 가능
- 예약 생성/수정/삭제 및 예약 시간에 작업 실행
- 작업/게시물/감사로그를 목록/검색/필터링 가능
- 95%+ API 응답 시간 p95 < 800ms(캐시 제외)

---

## 향후 고도화
- 멀티 채널(네이버/티스토리/워드프레스 등) 커넥터 추가
- 프롬프트 템플릿/AB 테스트
- 팀/조직 단위 권한, 결제/과금(옵션)
- 이미지 생성(옵션), 표절/품질 검사 파이프라인
---

# 부록 A — React 라우팅/가드 스켈레톤 (TypeScript)

> React Router v6 기준. **관리자(admin)** 전용 라우트와 **인증 가드**를 포함합니다.

```tsx
// src/app/routes.tsx
import React from 'react';
import { createBrowserRouter, RouterProvider, Outlet, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Login from '@/pages/Login';
import Dashboard from '@/pages/Dashboard';
import Generate from '@/pages/Generate';
import Jobs from '@/pages/Jobs';
import JobDetail from '@/pages/JobDetail';
import Schedule from '@/pages/Schedule';
import Posts from '@/pages/Posts';
import AdminUsers from '@/pages/AdminUsers';
import Settings from '@/pages/Settings';
import { useAuthStore } from '@/store/auth';

const queryClient = new QueryClient();

function ProtectedRoute() {
  const token = useAuthStore((s) => s.accessToken);
  return token ? <Outlet /> : <Navigate to="/login" replace />;
}

function AdminRoute() {
  const { accessToken, me } = useAuthStore.getState();
  if (!accessToken) return <Navigate to="/login" replace />;
  if (me?.role !== 'admin') return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}

const router = createBrowserRouter([
  { path: '/login', element: <Login /> },
  {
    element: (
      <QueryClientProvider client={queryClient}>
        <ProtectedRoute />
      </QueryClientProvider>
    ),
    children: [
      { path: '/', element: <Navigate to="/dashboard" replace /> },
      { path: '/dashboard', element: <Dashboard /> },
      { path: '/generate', element: <Generate /> },
      { path: '/jobs', element: <Jobs /> },
      { path: '/jobs/:jobId', element: <JobDetail /> },
      { path: '/schedule', element: <Schedule /> },
      { path: '/posts', element: <Posts /> },
      { path: '/settings', element: <Settings /> },
      {
        element: <AdminRoute />,
        children: [{ path: '/admin/users', element: <AdminUsers /> }],
      },
    ],
  },
]);

export default function AppRouter() {
  return <RouterProvider router={router} />;
}
```

```ts
// src/store/auth.ts (Zustand 예시)
import { create } from 'zustand';

type User = { id: number; email: string; role: 'user' | 'admin' };
type AuthState = {
  accessToken: string | null;
  refreshToken: string | null;
  me: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  fetchMe: () => Promise<void>;
};

export const useAuthStore = create<AuthState>((set, get) => ({
  accessToken: null,
  refreshToken: null,
  me: null,
  async login(email, password) {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error('login failed');
    const data = await res.json();
    set({ accessToken: data.access_token, refreshToken: data.refresh_token });
    await get().fetchMe();
  },
  logout() {
    set({ accessToken: null, refreshToken: null, me: null });
  },
  async fetchMe() {
    const { accessToken } = get();
    if (!accessToken) return;
    const res = await fetch('/api/me', { headers: { Authorization: `Bearer ${accessToken}` } });
    if (res.ok) set({ me: await res.json() });
  },
}));
```

```tsx
// src/pages/Login.tsx (핵심 로직만)
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/auth';

export default function Login() {
  const nav = useNavigate();
  const login = useAuthStore((s) => s.login);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    await login(email, password);
    if (useAuthStore.getState().me?.role === 'admin') nav('/admin/users');
    else nav('/dashboard');
  }

  return (
    <form onSubmit={onSubmit} className="p-8 max-w-sm mx-auto">
      <h1 className="text-xl font-bold mb-4">로그인</h1>
      <input className="border p-2 w-full mb-2" placeholder="email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <input className="border p-2 w-full mb-4" type="password" placeholder="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <button className="bg-black text-white px-4 py-2 rounded w-full">Sign in</button>
    </form>
  );
}
```

---

# 부록 B — FastAPI 라우터/스키마/메인 스켈레톤

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, generation, posts, admin, schedule

app = FastAPI(title="AI Blog Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(generation.router, prefix="/generation", tags=["generation"])
app.include_router(posts.router, prefix="/posts", tags=["posts"])
app.include_router(schedule.router, prefix="/schedule", tags=["schedule"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
```

```python
# app/routers/auth.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.security.jwt import create_tokens, get_current_user
from app.db.session import SessionDep
from app.db import crud

router = APIRouter()

class LoginRequest(BaseModel):
  email: str
  password: str

class LoginResponse(BaseModel):
  access_token: str
  refresh_token: str
  token_type: str = "bearer"

@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: SessionDep):
  user = crud.verify_user(db, payload.email, payload.password)
  if not user:
    raise HTTPException(status_code=401, detail="invalid credentials")
  access, refresh = create_tokens(user_id=user.id, role=user.role)
  return LoginResponse(access_token=access, refresh_token=refresh)

@router.get("/me")
def me(user = Depends(get_current_user)):
  return user
```

```python
# app/routers/generation.py
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from app.services.generator import ContentGenerator
from app.security.jwt import get_current_user

router = APIRouter()

class GenerateContentRequest(BaseModel):
  topic: str = Field(..., min_length=1, max_length=500)
  tone: Optional[str] = Field("professional", max_length=50)
  word_count: Optional[int] = Field(800, ge=300, le=3000)
  include_images: bool = Field(True)
  target_language: str = Field("ko", max_length=10)
  scheduled_at: Optional[str] = None

class GenerationJobResponse(BaseModel):
  job_id: str
  status: str
  message: str

@router.post("/generate", response_model=GenerationJobResponse)
def generate_content(req: GenerateContentRequest, background: BackgroundTasks, user=Depends(get_current_user)):
  gen = ContentGenerator()
  job_id = gen.create_job_id()
  background.add_task(gen.generate_content_async, job_id, req.dict(), user_id=user["id"])
  return GenerationJobResponse(job_id=job_id, status="started", message="Content generation started")

@router.get("/jobs/{job_id}")
def get_job(job_id: str):
  gen = ContentGenerator()
  data = gen.get_job_result(job_id)
  if not data:
    raise HTTPException(status_code=404, detail="Job not found")
  return data

@router.get("/jobs")
def list_jobs() -> List[str]:
  return ContentGenerator().list_jobs()
```

```python
# app/security/jwt.py (간단 버전)
import time, jwt
from fastapi import Header, HTTPException
from typing import Optional

SECRET = "CHANGE_ME"
ALG = "HS256"
ACCESS_TTL = 60 * 30

def create_tokens(user_id: int, role: str):
  now = int(time.time())
  payload = {"sub": user_id, "role": role, "iat": now, "exp": now + ACCESS_TTL}
  access = jwt.encode(payload, SECRET, algorithm=ALG)
  refresh = jwt.encode({**payload, "typ": "refresh", "exp": now + 60*60*24*14}, SECRET, algorithm=ALG)
  return access, refresh

def get_current_user(authorization: Optional[str] = Header(None)):
  if not authorization or not authorization.startswith("Bearer "):
    raise HTTPException(401, "missing token")
  token = authorization.split()[1]
  try:
    data = jwt.decode(token, SECRET, algorithms=[ALG])
  except Exception:
    raise HTTPException(401, "invalid token")
  return {"id": data["sub"], "role": data["role"]}
```

---

# 부록 C — Alembic 마이그레이션 스켈레톤 (PostgreSQL)

```python
# alembic/versions/20240901_000001_initial.py
from alembic import op
import sqlalchemy as sa

revision = "20240901_000001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
  op.create_table(
    "users",
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("email", sa.Text, nullable=False, unique=True),
    sa.Column("password_hash", sa.Text, nullable=False),
    sa.Column("role", sa.Text, nullable=False, server_default="user"),
    sa.Column("status", sa.Text, nullable=False, server_default="active"),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
  )
  op.create_table(
    "jobs",
    sa.Column("id", sa.String(length=36), primary_key=True),
    sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id")),
    sa.Column("topic", sa.Text, nullable=False),
    sa.Column("tone", sa.Text),
    sa.Column("word_count", sa.Integer),
    sa.Column("include_images", sa.Boolean, server_default=sa.text("true")),
    sa.Column("lang", sa.Text, server_default="ko"),
    sa.Column("status", sa.Text, nullable=False, server_default="queued"),
    sa.Column("scheduled_at", sa.DateTime(timezone=True)),
    sa.Column("started_at", sa.DateTime(timezone=True)),
    sa.Column("finished_at", sa.DateTime(timezone=True)),
    sa.Column("error_message", sa.Text),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
  )
  op.create_table(
    "job_outputs",
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("job_id", sa.String(length=36), sa.ForeignKey("jobs.id", ondelete="CASCADE")),
    sa.Column("html", sa.Text),
    sa.Column("excerpt", sa.Text),
    sa.Column("images", sa.JSON),
    sa.Column("tokens_used", sa.Integer),
    sa.Column("model_info", sa.Text),
    sa.Column("meta", sa.JSON),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
  )
  op.create_table(
    "channels",
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id")),
    sa.Column("type", sa.Text, nullable=False),
    sa.Column("config", sa.JSON, nullable=False, server_default=sa.text("'{}'::json")),
    sa.Column("active", sa.Boolean, server_default=sa.text("true")),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
  )
  op.create_table(
    "posts",
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("job_id", sa.String(length=36), sa.ForeignKey("jobs.id")),
    sa.Column("channel_id", sa.Integer, sa.ForeignKey("channels.id")),
    sa.Column("external_id", sa.Text),
    sa.Column("status", sa.Text, server_default="pending"),
    sa.Column("published_at", sa.DateTime(timezone=True)),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
  )
  op.create_table(
    "audit_logs",
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id")),
    sa.Column("action", sa.Text, nullable=False),
    sa.Column("target", sa.Text),
    sa.Column("payload", sa.JSON),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
  )

def downgrade():
  op.drop_table("audit_logs")
  op.drop_table("posts")
  op.drop_table("channels")
  op.drop_table("job_outputs")
  op.drop_table("jobs")
  op.drop_table("users")
```

---

# 부록 D — .env 예시

```dotenv
APP_ENV=local
PORT=8000
JWT_SECRET=change_me

DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/ai_blog
REDIS_URL=redis://redis:6379/0

WP_BASE_URL=https://your-wp-site.com
WP_USERNAME=admin
WP_PASSWORD=app-password-or-token
OPENAI_API_KEY=sk-...
```

---

# 부록 E — Docker Compose(선택, 최소 예시)

```yaml
version: "3.9"
services:
  api:
    build: ./api
    env_file: .env
    ports: ["8000:8000"]
    depends_on: [db, redis]
  web:
    build: ./web
    ports: ["5173:5173"]
  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: ai_blog
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]
  redis:
    image: redis:7
    ports: ["6379:6379"]
volumes:
  pgdata:
```

_최종 갱신:_
2025-09-01 01:00:41
