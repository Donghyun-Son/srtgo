# SRTgo 웹 마이그레이션 가이드

이 문서는 SRTgo CLI 애플리케이션을 웹 버전으로 마이그레이션한 전체 가이드입니다.

## 📁 프로젝트 구조

```
srtgo/
├── srtgo/                  # 기존 CLI 코드 (Python)
│   ├── srtgo.py           # CLI 메인 (inquirer 사용)
│   ├── srt.py             # SRT API 로직
│   └── ktx.py             # KTX API 로직
│
├── backend/               # 새로운 FastAPI 백엔드
│   ├── api/              # API 라우트 핸들러
│   ├── core/             # 설정 및 보안
│   ├── models/           # 데이터베이스 모델
│   ├── schemas/          # Pydantic 스키마
│   ├── services/         # 비즈니스 로직
│   ├── main.py           # FastAPI 앱
│   └── requirements.txt  # Python 의존성
│
├── frontend/             # React 프론트엔드
│   ├── src/
│   │   ├── components/  # UI 컴포넌트
│   │   ├── pages/       # 페이지 컴포넌트
│   │   ├── services/    # API 서비스
│   │   └── store/       # 상태 관리
│   └── package.json     # Node 의존성
│
└── 분석 문서/
    ├── ANALYSIS_INDEX.md      # 분석 가이드
    ├── MIGRATION_PLAN.md      # 마이그레이션 계획
    ├── INQUIRY_ANALYSIS.txt   # Inquirer 상세 분석
    └── INQUIRY_USAGE_MAP.txt  # 플로우 다이어그램
```

## 🚀 빠른 시작

### 1. 백엔드 실행

```bash
cd backend

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일에서 SECRET_KEY 수정

# 서버 실행
python main.py
# 또는
uvicorn main:app --reload
```

백엔드가 http://localhost:8000 에서 실행됩니다.
- API 문서: http://localhost:8000/docs

### 2. 프론트엔드 실행

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

프론트엔드가 http://localhost:3000 에서 실행됩니다.

## 🔄 마이그레이션 매핑

### CLI → Web 컴포넌트 매핑

| CLI 기능 (inquirer) | Web 컴포넌트 | 위치 |
|-------------------|-------------|------|
| 메인 메뉴 (list_input) | 사이드바 네비게이션 | Layout.tsx |
| 열차 선택 (List) | 라디오 버튼 | ReservationPage.tsx |
| 역 선택 (Checkbox) | 드롭다운 select | ReservationPage.tsx |
| 날짜/시간 입력 (Text) | date/time input | ReservationPage.tsx |
| 승객 수 (Text) | number input | ReservationPage.tsx |
| 로그인 정보 (Password) | 비밀번호 필드 | SettingsPage.tsx |
| 카드 정보 (Password) | 비밀번호 필드 | SettingsPage.tsx |
| 확인 다이얼로그 (Confirm) | 확인 단계 | ReservationPage.tsx Step 3 |

### 데이터 저장 방식 변경

| 항목 | CLI (기존) | Web (신규) |
|-----|----------|----------|
| 인증 정보 | OS Keyring | PostgreSQL/SQLite (암호화) |
| 세션 | 없음 | JWT 토큰 |
| 사용자 관리 | 단일 사용자 | 다중 사용자 지원 |
| 예약 상태 | 메모리 | 데이터베이스 |

## 🏗️ 아키텍처

### 백엔드 (FastAPI)

```
┌─────────────────────────────────────┐
│         FastAPI Backend             │
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │     API Layer (REST)            │ │
│ │  - /api/auth                    │ │
│ │  - /api/credentials             │ │
│ │  - /api/trains                  │ │
│ │  - /api/reservations            │ │
│ │  - WebSocket /ws                │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │     Services Layer              │ │
│ │  - TrainService (SRT/KTX)       │ │
│ │  - ReservationService           │ │
│ │  - Polling (asyncio)            │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │     Data Layer                  │ │
│ │  - SQLAlchemy (async)           │ │
│ │  - Models (User, Credential...)  │ │
│ │  - AES Encryption               │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### 프론트엔드 (React)

```
┌─────────────────────────────────────┐
│         React Frontend              │
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │     Pages                       │ │
│ │  - Login/Register               │ │
│ │  - Dashboard                    │ │
│ │  - Reservation (3-step wizard)  │ │
│ │  - Settings                     │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │     State Management            │ │
│ │  - Zustand (auth)               │ │
│ │  - TanStack Query (API)         │ │
│ │  - React Hook Form (forms)      │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │     API Layer                   │ │
│ │  - Axios (HTTP)                 │ │
│ │  - WebSocket (real-time)        │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## 🔑 주요 기능

### 1. 인증 시스템
- JWT 기반 토큰 인증
- 회원가입 / 로그인
- 보호된 라우트
- 자동 토큰 갱신

### 2. 예약 시스템
- 3단계 예약 위저드
  1. 기본 정보 (열차, 역, 날짜)
  2. 승객 정보
  3. 확인 및 제출
- 실시간 열차 검색
- 백그라운드 폴링 (available trains)
- WebSocket으로 실시간 업데이트

### 3. 설정 관리
- 열차 로그인 정보 (암호화 저장)
- 카드 정보 (암호화 저장)
- 텔레그램 알림 설정

### 4. 대시보드
- 최근 예약 목록
- 예약 상태 요약
- 빠른 예약 링크

## 🔒 보안

### 암호화
- **비밀번호**: bcrypt 해싱
- **민감 정보**: AES-256 암호화
  - 열차 로그인 정보
  - 카드 정보
  - 텔레그램 토큰

### 인증
- JWT 토큰 (30분 유효)
- Bearer 토큰 방식
- 자동 로그아웃 (401 응답 시)

### CORS
- 설정된 origin만 허용
- Credentials 지원

## 📱 모바일 지원

- 반응형 디자인 (Tailwind CSS)
- 모바일 우선 접근
- 터치 친화적 UI
- 모바일 네비게이션 (하단 탭)
- 데스크톱 네비게이션 (사이드바)

## 🎯 기술 선택 이유

### 백엔드: FastAPI
- ✅ 빠른 성능 (Starlette + Pydantic)
- ✅ 비동기 지원 (async/await)
- ✅ 자동 API 문서 생성
- ✅ Python 생태계 활용 (기존 srt.py, ktx.py 재사용)

### 프론트엔드: React + TypeScript
- ✅ 대규모 커뮤니티
- ✅ 타입 안정성 (TypeScript)
- ✅ 풍부한 라이브러리 생태계
- ✅ 컴포넌트 재사용성

### 데이터베이스: SQLite/PostgreSQL
- ✅ SQLite: 간단한 설정, 소규모 (1-5명) 충분
- ✅ PostgreSQL: 확장 가능, 프로덕션 준비

### 상태 관리
- **Zustand**: 간단하고 가벼운 전역 상태
- **TanStack Query**: 서버 상태 관리 (캐싱, 재시도 등)
- **React Hook Form**: 폼 상태 및 검증

## 📊 성능 최적화

### 백엔드
- 비동기 I/O (asyncio)
- 데이터베이스 인덱싱
- 경량 폴링 (1-5명 사용자에 충분)

### 프론트엔드
- 코드 스플리팅 (Vite)
- 쿼리 캐싱 (TanStack Query)
- 지연 로딩

## 🧪 테스트 (향후 추가)

### 백엔드
```bash
pytest
pytest --cov=backend
```

### 프론트엔드
```bash
npm test
npm run test:e2e
```

## 🚢 배포

### 백엔드

```bash
# Gunicorn with Uvicorn workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 프론트엔드

```bash
# 빌드
npm run build

# 정적 호스팅 (Netlify, Vercel 등)
# dist/ 디렉토리 배포
```

### Docker (향후)

```dockerfile
# Docker Compose로 전체 스택 배포
docker-compose up -d
```

## 📈 향후 개선 사항

### 기능
- [ ] 실시간 알림 (WebSocket 강화)
- [ ] 예약 수정/취소 기능
- [ ] 즐겨찾는 경로 저장
- [ ] 예약 히스토리 검색/필터
- [ ] PWA 지원 (오프라인 모드)

### 기술
- [ ] Redis 캐싱
- [ ] Celery (대규모 폴링)
- [ ] Docker Compose
- [ ] CI/CD 파이프라인
- [ ] 로깅 및 모니터링

### UX
- [ ] 다크 모드
- [ ] 다국어 지원 (i18n)
- [ ] 접근성 개선 (a11y)
- [ ] 애니메이션 추가

## 🤝 기여

이 프로젝트는 기존 CLI 버전의 웹 마이그레이션입니다.

### 기존 CLI
- Repository: https://github.com/lapis42/srtgo
- 기여자: @lapis42, @guhyun9454

### 웹 버전
- 마이그레이션: Claude AI Assistant
- 아키텍처 설계: FastAPI + React
- 구현 날짜: 2025년 11월

## 📄 라이선스

MIT License - 기존 프로젝트와 동일

## 📚 참고 문서

- [ANALYSIS_INDEX.md](./ANALYSIS_INDEX.md) - 분석 가이드
- [MIGRATION_PLAN.md](./MIGRATION_PLAN.md) - 마이그레이션 계획
- [backend/README.md](./backend/README.md) - 백엔드 문서
- [frontend/README.md](./frontend/README.md) - 프론트엔드 문서

## ❓ 문제 해결

### 백엔드가 시작되지 않음
1. Python 3.10+ 설치 확인
2. 의존성 설치: `pip install -r backend/requirements.txt`
3. .env 파일 설정 확인

### 프론트엔드 빌드 오류
1. Node.js 16+ 설치 확인
2. node_modules 삭제 후 재설치: `rm -rf node_modules && npm install`

### CORS 오류
1. backend/.env에서 ALLOWED_ORIGINS 확인
2. 프론트엔드 URL이 포함되어 있는지 확인

### 데이터베이스 오류
1. SQLite 파일 권한 확인
2. 또는 PostgreSQL 연결 문자열 확인

---

**이 가이드로 SRTgo CLI를 성공적으로 웹 애플리케이션으로 마이그레이션했습니다!** 🎉
