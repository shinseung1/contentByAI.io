# 관리자(Admin) 탭 구성

## 1) 대시보드

- **요약 카드**: 오늘 생성 건수, 실패/재시도, 토큰/비용, 예약 발행 대기

- **최근 활동**: 최근 20개 작업 로그 테이블

- **알림 센터**: 한도 임박, 키 오류, 퍼블리시 실패

## 2) 사용자(계정관리)

### 섹션

- **사용자 목록**(DataTable)
  
  - 필터: 상태(활성/비활성/만료임박), 롤, 테넌트
  
  - 컬럼: 이메일, 이름, 롤, 상태, 만료일, 마지막 접속

- **계정 상세 패널**(Drawer/Sidebar)
  
  - 기본정보: 이름, 이메일, 롤(`owner/admin/editor/viewer/service`)
  
  - **유효기간**: 만료일, 자동연장 on/off
  
  - 보안: 비밀번호 재설정 링크 발급, 2FA 상태
  
  - **크레딧/한도**: 월 토큰 상한, 현재 사용량, 비용 상한
  
  - 작업: 비활성화/삭제/초대 재전송

## 3) 모델/프로바이더

### 섹션

- **키 관리**: OpenAI/Claude/Gemini API 키(alias, 활성 여부, 범위)

- **기본 모델 매핑**: 작업유형별 기본모델(초안/요약/번역/SEO 폴리시)

- **폴백 정책**: 장애/초과 시 대체모델, 재시도 횟수, 타임아웃

## 4) 워크플로우 템플릿

### 섹션

- **템플릿 목록**: outline → draft → fact-check → seo → publish

- **단계 편집기**: 단계 이름, 프롬프트 템플릿, 승인자(롤/사용자), 자동 전환 조건

- **버전 관리**: 활성 버전 지정, 롤백, 변경 이력

## 5) SEO/배포

### 섹션

- **SEO 기본값**: 메타 타이틀/디스크립션 길이, FAQ 개수, OG 설정

- **퍼블리시 채널**: WordPress/Headless CMS/Git Export 연결·기본 카테고리·태그

- **스케줄러**: 예약발행 기본 시각(Asia/Seoul), 자동 리프레시 주기(예: 90일)

## 6) 소스 연결

### 섹션

- **인풋 소스**: RSS/URL 크롤러 주기, 화이트리스트 도메인

- **사내 도구**: Notion/Google Docs/Slack 연동(토큰, 스코프)

- **미디어 자산**: 이미지 정책(제안만/업로드 허용/스톡 라이선스)

## 7) 정책/컴플라이언스

### 섹션

- **브랜드 가이드**: 필수 포함/금지 용어, 톤 규칙

- **사실검증/출처**: 출처 필수 여부, 허용 도메인

- **안전성**: PII 제거, 민감 주제 차단(의료/투자 등)

## 8) 과금/한도

### 섹션

- **플랜**: Free/Pro/Enterprise 한도표

- **과금 한도**: 테넌트/사용자별 월 토큰·비용 상한

- **결제**: 카드/세금계산서, 청구 이력

## 9) 로깅/감사

### 섹션

- **요청 로그**: 사용자/모델/토큰/비용/지연시간, 상세 페이로드(마스킹)

- **콘텐츠 이력**: 상태 전이(draft→published), diff 보기, 승인자 기록

- **보존정책**: 보존 기간, 익명화 규칙

## 10) 통합 & API

### 섹션

- **Webhook**: 이벤트 선택, 서명 시크릿, 재전송

- **API 토큰**: 서비스 계정 키 발급, Scope, 만료

- **SSO/SAML**: 조직 디렉터리 연동

---

# 개별 사용자 탭 구성

## A) 내 프로필

- 기본정보: 이름, 프로필 이미지, 언어, 시간대

- 보안: 비밀번호 변경, 2FA

## B) 생성 기본값(프리셋)

- 목적: 트래픽/리드/브랜드 신뢰

- 톤/독자/리딩 레벨

- 길이(또는 1200–1500자)

- 키워드(기본/보조)

- 브랜드 가이드(내 계정 기준 override 가능 항목)

## C) 인풋 소스

- RSS/URL 등록 주기

- 붙여넣기·파일 업로드(.md/.docx)

- 사실확인 레퍼런스 URL 화이트리스트

## D) SEO/배포 기본값

- 메타 템플릿(타이틀/디스크립션)

- OG 이미지 기본값

- 기본 채널/카테고리/태그

- 예약 발행 기본 시각, 자동 리프레시

## E) 안전/컴플라이언스

- PII 제거 on/off

- 제한 주제 알림/차단

- 저작권/인용 동의 체크

## F) 한도 & 알림

- 내 잔여 크레딧/월 한도

- 작업 완료/실패/한도 임박 알림(이메일/슬랙)

## G) 내 작업

- 내 생성/수정/예약 목록

- 상태 필터(초안/대기/발행/실패)

- 빠른 재시도/수정/복제

---

# 탭/섹션 라우팅 & 컴포넌트(예시)

- `AdminView`
  
  - TabView: `대시보드 | 사용자 | 모델 | 워크플로우 | SEO/배포 | 소스 | 정책 | 과금 | 로깅 | 통합`
  
  - 각 탭 내부: `Panel`/`Fieldset` + `DataTable`/`Form`

- `UserSettingsView`
  
  - TabView: `프로필 | 생성 기본값 | 인풋 소스 | SEO/배포 | 안전 | 한도&알림 | 내 작업`

---

# 필드 스키마 예시

## (Admin) 사용자(계정관리)

`{   "list": {     "filters": ["status", "role", "tenant"],     "columns": ["email","name","role","status","expires_at","last_seen_at"]   },   "detail": {     "sections": [       {         "title": "기본정보",         "fields": [           {"key":"name","type":"text","required":true},           {"key":"email","type":"email","required":true,"readonly":true},           {"key":"role","type":"select","options":["owner","admin","editor","viewer","service"]}         ]       },       {         "title": "유효기간",         "fields": [           {"key":"expires_at","type":"date"},           {"key":"auto_renew","type":"switch"}         ]       },       {         "title": "보안",         "fields": [           {"key":"reset_password","type":"button"},           {"key":"mfa_enabled","type":"badge"}         ]       },       {         "title": "크레딧/한도",         "fields": [           {"key":"monthly_token_limit","type":"number"},           {"key":"monthly_cost_cap","type":"currency"}         ]       }     ]   } }`

## (User) 생성 기본값

`{   "sections": [     {       "title": "목표 & 톤",       "fields": [         {"key":"goal","type":"select","options":["traffic","leads","brand"]},         {"key":"tone","type":"select","options":["friendly","authoritative","playful","formal","concise","persuasive"]},         {"key":"reading_level","type":"select","options":["beginner","general","expert"]}       ]     },     {       "title": "길이 & 키워드",       "fields": [         {"key":"length","type":"select","options":["short","medium","long","custom"],"depends":[{"key":"length","value":"custom","show":[{"key":"word_range","type":"text"}]}]},         {"key":"primary_keyword","type":"text"},         {"key":"secondary_keywords","type":"chips"}       ]     },     {       "title": "브랜드 가이드",       "fields": [         {"key":"brand_terms.required","type":"chips"},         {"key":"brand_terms.forbidden","type":"chips"}       ]     }   ] }`

---

# 권한 매트릭스(요약)

- **owner**: 모든 탭/설정/결제

- **admin**: 테넌트 운영 전반(결제 제외 옵션 가능)

- **editor**: 콘텐츠 생성/수정/예약/퍼블리시(정책 내)

- **viewer**: 읽기 전용(로그·대시보드)

- **service**: API 토큰 전용(스코프 제한)
