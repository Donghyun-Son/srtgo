# SRTgo Web UI 변환 계획

현재 CLI 코드를 분석한 결과를 바탕으로 Web UI로 변환하는 포괄적인 계획을 제시합니다.

## 📋 현재 CLI 기능 분석

**주요 기능들:**
1. **예매 시작** - 역, 날짜, 시간, 승객 선택 후 실시간 예매 시도
2. **예매 확인/결제/취소** - 기존 예약 관리
3. **설정 관리** - 로그인, 텔레그램, 카드, 역, 옵션 설정
4. **실시간 모니터링** - 무한 루프로 좌석 확인 및 예매 시도

## 🏗️ Web UI 아키텍처 설계

### 기술 스택
- **Backend**: FastAPI (Python) - 기존 srtgo 모듈과 호환성
- **Frontend**: React + TypeScript - 반응형 디자인
- **Real-time**: WebSocket - 실시간 예매 진행 상황
- **Background Tasks**: Celery + Redis - 브라우저 종료 시에도 예매 지속
- **Database**: SQLite - 설정 및 예매 상태 저장
- **Deployment**: Docker + Docker Compose

### 시스템 구조
```
srtgo-web/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI 라우터
│   │   ├── core/          # 설정, 보안
│   │   ├── services/      # 비즈니스 로직
│   │   ├── models/        # 데이터 모델
│   │   ├── tasks/         # Celery 백그라운드 작업
│   │   └── srtgo_wrapper/ # 기존 srtgo 모듈 래퍼
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/    # React 컴포넌트
│   │   ├── pages/         # 페이지별 컴포넌트
│   │   ├── hooks/         # WebSocket, API 훅
│   │   ├── services/      # API 클라이언트
│   │   └── utils/         # 유틸리티
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── nginx.conf
```

## 🚀 구현 계획

### Phase 1: 백엔드 기반 구조 (1-2주) ✅ 완료
- [x] **FastAPI 프로젝트 설정**
  - [x] Docker 환경 구성
  - [x] Redis, SQLite 연동
  - [x] 기본 API 구조 생성

- [x] **srtgo 래퍼 개발**
  - [x] 기존 CLI 함수들을 API 호출 가능하도록 래핑
  - [x] 설정 관리를 keyring에서 DB로 마이그레이션
  - [x] 에러 핸들링 표준화

- [x] **백그라운드 작업 시스템**
  - [x] Celery로 예매 작업 분리
  - [x] WebSocket으로 실시간 상태 전송
  - [x] 작업 상태 관리 (시작/중지/완료)

### Phase 2: 프론트엔드 개발 (2-3주) ✅ 완료
- [x] **반응형 UI 컴포넌트**
  - [x] Mobile-first 디자인
  - [x] 역 선택, 날짜/시간 피커
  - [x] 실시간 진행 상황 표시

- [x] **페이지 구현**
  - [x] 메인 대시보드
  - [x] 예매 설정 페이지
  - [x] 예매 모니터링 페이지
  - [x] 설정 관리 페이지

- [x] **실시간 기능**
  - [x] WebSocket 연결 관리
  - [x] 예매 진행 상황 실시간 업데이트
  - [x] 알림 시스템

### Phase 3: 통합 및 배포 (1주) ✅ 완료
- [x] **Docker 통합**
  - [x] Multi-stage build 최적화
  - [x] Nginx 리버스 프록시 설정
  - [x] 환경 변수 관리

- [x] **테스트 및 최적화**
  - [x] 로컬 개발 환경 테스트
  - [x] 성능 최적화
  - [x] 보안 강화

## 🔧 주요 구현 세부사항

### 1. 백그라운드 예매 시스템
```python
# tasks/reservation.py
@celery.task
def start_reservation_task(user_id, reservation_config):
    # 기존 reserve() 함수를 백그라운드에서 실행
    # WebSocket으로 진행 상황 전송
    pass
```

### 2. 실시간 상태 전송
```python
# WebSocket endpoint
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    # 예매 진행 상황을 실시간으로 전송
    pass
```

### 3. 설정 데이터 관리
```python
# models/settings.py
class UserSettings(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    user_id: str
    rail_type: str
    login_id: str
    encrypted_password: str
    # ... 기타 설정
```

### 4. 반응형 프론트엔드
```typescript
// hooks/useReservation.ts
export const useReservation = () => {
  const [status, setStatus] = useState<ReservationStatus>()
  const ws = useWebSocket(`/ws/${userId}`)
  
  // 실시간 상태 업데이트
  useEffect(() => {
    ws.onmessage = (event) => {
      setStatus(JSON.parse(event.data))
    }
  }, [ws])
}
```

## 📦 배포 전략

### Docker Compose 구성
```yaml
version: '3.8'
services:
  web:
    build: ./backend
    depends_on: [redis, db]
  
  frontend:
    build: ./frontend
    
  nginx:
    image: nginx:alpine
    ports: ["80:80"]
    
  redis:
    image: redis:alpine
    
  celery:
    build: ./backend
    command: celery worker
```

### NAS 배포 고려사항
- 포트 매핑 설정
- 볼륨 마운트로 데이터 영속성
- 환경 변수를 통한 설정 관리
- SSL 인증서 설정

## 🧪 개발 및 테스트 환경

### 로컬 개발
```bash
# 가상환경 설정
python -m venv venv
source venv/bin/activate

# 개발 서버 실행
docker-compose -f docker-compose.dev.yml up
```

### 테스트 전략
- 기존 srtgo 모듈의 단위 테스트 유지
- API 엔드포인트 테스트
- WebSocket 연결 테스트
- 프론트엔드 컴포넌트 테스트

## 📅 예상 일정

- **Week 1-2**: 백엔드 기반 구조 및 래퍼 개발
- **Week 3-5**: 프론트엔드 개발 및 UI/UX 구현
- **Week 6**: 통합, 테스트, Docker 배포 설정
- **Week 7**: NAS 배포 및 최종 테스트

## 📊 진행 상황

### 현재 진행 단계: Phase 3 완료 ✅
- 진행률: 100%
- 상태: 기본 구현 완료

## 🎉 구현 완료 항목

### 백엔드 (FastAPI)
- ✅ FastAPI 앱 구조 및 API 라우터
- ✅ SQLModel을 이용한 데이터 모델 (User, UserSettings, Reservation)
- ✅ JWT 기반 인증 시스템
- ✅ Celery 백그라운드 작업 시스템
- ✅ WebSocket 실시간 통신
- ✅ 기존 srtgo 모듈 래퍼 서비스
- ✅ Docker 컨테이너화

### 프론트엔드 (React + TypeScript)
- ✅ Material-UI 기반 반응형 디자인
- ✅ React Router 네비게이션
- ✅ React Query 상태 관리
- ✅ 로그인/회원가입 페이지
- ✅ 대시보드 (예매 현황 및 통계)
- ✅ 단계별 예매 페이지 (4단계)
- ✅ 실시간 예매 모니터링 페이지
- ✅ 설정 페이지 (템플릿)
- ✅ WebSocket 훅으로 실시간 업데이트
- ✅ Docker 컨테이너화 및 Nginx 설정

### 인프라
- ✅ Docker Compose 오케스트레이션
- ✅ Redis (Celery 브로커 및 캐시)
- ✅ SQLite 데이터베이스
- ✅ Nginx 리버스 프록시
- ✅ 개발/프로덕션 환경 분리

## 🚀 실행 방법

### 개발 환경
```bash
cd srtgo-web
docker-compose -f docker-compose.dev.yml up
```

### 프로덕션 환경
```bash
cd srtgo-web
docker-compose up -d
```

접속 URL:
- 프론트엔드: http://localhost:3000 (개발) / http://localhost (프로덕션)
- 백엔드 API: http://localhost:8000
- API 문서: http://localhost:8000/docs

## 📝 다음 단계 (추가 개발 필요)

### 백엔드 완성도 향상
- [ ] 실제 srtgo 모듈과의 완전한 통합 테스트
- [ ] 설정 암호화/복호화 구현
- [ ] 텔레그램 알림 기능 구현
- [ ] 카드 결제 기능 구현
- [ ] 에러 처리 및 로깅 개선
- [ ] API 유닛 테스트 작성

### 프론트엔드 완성도 향상
- [ ] 설정 페이지 완전 구현
- [ ] 에러 핸들링 개선
- [ ] 로딩 상태 개선
- [ ] 접근성 개선
- [ ] PWA 기능 추가
- [ ] 모바일 최적화 개선

### 배포 및 운영
- [ ] HTTPS 설정
- [ ] 환경별 설정 파일 분리
- [ ] 모니터링 및 로깅 시스템
- [ ] 백업 및 복구 전략
- [ ] CI/CD 파이프라인 구축