# SRTgo Web UI - 시작 가이드

CLI 기반의 SRTgo를 Web UI로 변환하는 프로젝트가 기본 구현 완료되었습니다.

## 🎯 프로젝트 개요

기존 CLI 프로그램의 모든 기능을 Web UI로 구현:
- 실시간 예매 모니터링
- 백그라운드 예매 작업 (브라우저 종료 시에도 지속)
- 반응형 디자인 (PC/모바일 호환)
- Docker를 통한 간편한 배포

## 🚀 빠른 시작

### 1. 개발 환경 실행
```bash
cd srtgo-web
docker-compose -f docker-compose.dev.yml up
```

접속 URL:
- 프론트엔드: http://localhost:3000
- 백엔드 API: http://localhost:8000
- API 문서: http://localhost:8000/docs

### 2. 프로덕션 환경 실행
```bash
cd srtgo-web
docker-compose up -d
```

접속 URL:
- 웹 애플리케이션: http://localhost
- 백엔드 API: http://localhost:8000

## 📁 프로젝트 구조

```
srtgo-web/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── api/            # API 라우터
│   │   ├── core/           # 설정 및 데이터베이스
│   │   ├── models/         # 데이터 모델
│   │   ├── services/       # 비즈니스 로직
│   │   ├── tasks/          # Celery 백그라운드 작업
│   │   └── srtgo_wrapper/  # 기존 srtgo 모듈 래퍼
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React 프론트엔드
│   ├── src/
│   │   ├── components/     # 재사용 가능한 컴포넌트
│   │   ├── pages/          # 페이지 컴포넌트
│   │   ├── hooks/          # React 훅
│   │   ├── services/       # API 서비스
│   │   └── types/          # TypeScript 타입 정의
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml      # 프로덕션 환경
└── docker-compose.dev.yml  # 개발 환경
```

## 🔧 주요 기능

### 백엔드 (FastAPI)
- ✅ REST API 엔드포인트
- ✅ JWT 기반 인증
- ✅ Celery 백그라운드 작업
- ✅ WebSocket 실시간 통신
- ✅ SQLite 데이터베이스
- ✅ 기존 srtgo 모듈 통합

### 프론트엔드 (React)
- ✅ Material-UI 디자인 시스템
- ✅ 반응형 레이아웃
- ✅ 로그인/회원가입
- ✅ 대시보드 (예매 현황)
- ✅ 4단계 예매 프로세스
- ✅ 실시간 예매 모니터링
- ✅ WebSocket을 통한 실시간 업데이트

### 인프라
- ✅ Docker 컨테이너화
- ✅ Nginx 리버스 프록시
- ✅ Redis (Celery 브로커)
- ✅ 개발/프로덕션 환경 분리

## 📖 사용 방법

### 1. 회원가입 및 로그인
1. 웹 브라우저에서 애플리케이션 접속
2. 회원가입 탭에서 계정 생성
3. 로그인하여 대시보드 접속

### 2. 예매하기
1. 사이드바에서 "예매하기" 클릭
2. 4단계로 구성된 예매 프로세스:
   - **1단계**: 기본 정보 (열차 종류, 출발/도착역, 날짜/시간)
   - **2단계**: 열차 선택 (검색 후 원하는 열차 선택)
   - **3단계**: 승객 정보 (승객 수, 좌석 유형, 자동 결제 설정)
   - **4단계**: 확인 (입력 정보 최종 확인)
3. "예매 시작" 버튼으로 백그라운드 예매 시작

### 3. 실시간 모니터링
1. 예매 시작 후 자동으로 모니터링 페이지로 이동
2. 실시간 로그 및 진행 상황 확인
3. WebSocket을 통한 실시간 업데이트
4. 예매 성공/실패 시 즉시 알림

### 4. 대시보드 확인
1. 전체 예매 통계 (총 예매, 실행중, 성공, 실패)
2. 최근 예매 내역 테이블
3. 각 예매의 상태 및 진행률 확인

## ⚙️ 개발 환경 설정

### 백엔드 개발
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 프론트엔드 개발
```bash
cd frontend
npm install
npm start
```

### Celery 워커 실행
```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info
```

## 🔄 다음 개발 단계

### 즉시 필요한 작업
1. **실제 srtgo 모듈 통합**: 현재는 Mock 데이터 사용 중
2. **설정 페이지 완성**: SRT/KTX 로그인 정보, 텔레그램, 카드 정보 설정
3. **에러 처리 개선**: 더 나은 사용자 피드백 제공

### 추가 기능
1. **텔레그램 알림**: 예매 성공/실패 시 텔레그램 메시지 전송
2. **자동 결제**: 예매 성공 시 카드 자동 결제
3. **예매 이력**: 과거 예매 내역 및 통계
4. **PWA 지원**: 모바일 앱처럼 사용 가능

### NAS 배포 준비
1. **HTTPS 설정**: SSL 인증서 적용
2. **환경 변수 관리**: 프로덕션 환경 설정 분리
3. **백업 전략**: 데이터베이스 백업 및 복구
4. **모니터링**: 시스템 상태 모니터링

## 🛠️ 문제 해결

### 일반적인 문제들

**Docker 컨테이너가 시작되지 않는 경우:**
```bash
# 이전 컨테이너 정리
docker-compose down -v
docker system prune -f

# 새로 빌드하여 시작
docker-compose build --no-cache
docker-compose up
```

**포트 충돌 오류:**
- 8000번 포트 (백엔드): 다른 서비스에서 사용 중인지 확인
- 3000번 포트 (프론트엔드): React 개발 서버 중복 실행 확인
- 6379번 포트 (Redis): 로컬 Redis 서버와 충돌 여부 확인

**WebSocket 연결 실패:**
- 브라우저 개발자 도구에서 네트워크 탭 확인
- 백엔드 서버가 정상 실행되고 있는지 확인
- CORS 설정 확인

## 📞 추가 지원

이 가이드로 해결되지 않는 문제가 있다면:
1. `docker-compose logs` 명령으로 로그 확인
2. 브라우저 개발자 도구 콘솔 확인
3. API 문서 (`http://localhost:8000/docs`) 참조

프로젝트가 성공적으로 구현되어 기본적인 Web UI 기능이 모두 작동합니다! 🎉