# SRTgo Web - Docker 배포 가이드

SRTgo 웹 애플리케이션을 단일 Docker 컨테이너로 실행하는 가이드입니다.

## 📦 아키텍처

```
Single Docker Container
├── Frontend (React)
│   └── Built as static files (/frontend/dist)
├── Backend (FastAPI)
│   ├── Serves API at /api/*
│   ├── Serves frontend static files
│   └── Handles client-side routing
└── Database (SQLite)
    └── Persisted in Docker volume
```

## 🚀 빠른 시작

### 1. 빌드 및 실행 (자동)

```bash
# 빌드 (처음 한 번만)
./docker-build.sh

# 실행
./docker-run.sh
```

### 2. 수동 빌드 및 실행

```bash
# .env 파일 생성
cp .env.docker .env
# .env 파일에서 SECRET_KEY 수정

# Docker 이미지 빌드
docker-compose build

# 컨테이너 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

## 📋 접속 정보

빌드가 완료되면 다음 주소로 접속할 수 있습니다:

- **웹 애플리케이션**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🛠️ 관리 명령어

### 컨테이너 관리

```bash
# 시작
docker-compose up -d

# 중지
docker-compose down

# 재시작
docker-compose restart

# 상태 확인
docker-compose ps

# 로그 보기
docker-compose logs -f

# 로그 보기 (특정 줄 수)
docker-compose logs --tail=100 -f
```

### 데이터베이스 관리

```bash
# 데이터베이스 백업
docker-compose exec srtgo-web cp /app/data/srtgo.db /app/data/srtgo_backup.db

# 컨테이너에서 파일 복사
docker cp srtgo-web:/app/data/srtgo.db ./srtgo_backup.db

# 볼륨 삭제 (데이터 초기화)
docker-compose down -v
```

### 이미지 관리

```bash
# 이미지 재빌드 (캐시 없이)
docker-compose build --no-cache

# 이미지 삭제
docker rmi srtgo-srtgo-web

# 사용하지 않는 이미지 정리
docker image prune -a
```

## ⚙️ 환경 변수 설정

`.env` 파일을 수정하여 설정을 변경할 수 있습니다:

```env
# 필수: 강력한 시크릿 키로 변경
SECRET_KEY=your-secret-key-here

# 애플리케이션 설정
APP_NAME=SRTgo Web
DEBUG=False

# 데이터베이스 (기본: SQLite)
DATABASE_URL=sqlite+aiosqlite:///./data/srtgo.db

# 보안
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 텔레그램 알림 (선택)
TELEGRAM_ENABLED=False
```

**중요**: 프로덕션 환경에서는 반드시 `SECRET_KEY`를 변경하세요!

```bash
# 안전한 SECRET_KEY 생성
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 🗄️ PostgreSQL 사용하기

기본적으로 SQLite를 사용하지만, PostgreSQL로 변경할 수 있습니다:

### docker-compose.yml 수정

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: srtgo-postgres
    environment:
      POSTGRES_DB: srtgo
      POSTGRES_USER: srtgo
      POSTGRES_PASSWORD: your-password
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U srtgo"]
      interval: 10s
      timeout: 5s
      retries: 5

  srtgo-web:
    build:
      context: .
      dockerfile: Dockerfile
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      - DATABASE_URL=postgresql+asyncpg://srtgo:your-password@postgres:5432/srtgo
    # ... 나머지 설정

volumes:
  srtgo-data:
  postgres-data:
```

## 📊 모니터링

### Health Check

```bash
# 컨테이너 헬스 체크
docker-compose ps

# API 헬스 체크
curl http://localhost:8000/health
```

### 리소스 사용량

```bash
# CPU, 메모리 사용량
docker stats srtgo-web

# 디스크 사용량
docker system df
```

## 🔒 보안 고려사항

### 프로덕션 배포 시

1. **SECRET_KEY 변경**
   ```bash
   # 강력한 키 생성
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **DEBUG 모드 비활성화**
   ```env
   DEBUG=False
   ```

3. **HTTPS 사용**
   - Nginx 리버스 프록시 사용
   - Let's Encrypt SSL 인증서 적용

4. **방화벽 설정**
   ```bash
   # 8000 포트만 외부 노출
   ufw allow 8000/tcp
   ```

5. **정기 업데이트**
   ```bash
   # 이미지 업데이트
   docker-compose pull
   docker-compose up -d
   ```

## 🚦 포트 변경

기본 포트 8000을 변경하려면 `docker-compose.yml` 수정:

```yaml
services:
  srtgo-web:
    ports:
      - "3000:8000"  # 호스트:컨테이너
```

## 📝 로그 관리

### 로그 로테이션

`docker-compose.yml`에 로깅 설정 추가:

```yaml
services:
  srtgo-web:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 로그 레벨 변경

환경 변수로 제어:

```yaml
environment:
  - LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

## 🔄 업데이트 방법

### 1. 코드 업데이트 후 재배포

```bash
# Git pull
git pull origin main

# 재빌드
docker-compose build

# 재시작
docker-compose down
docker-compose up -d
```

### 2. 무중단 업데이트

```bash
# 새 이미지 빌드
docker-compose build

# 컨테이너 교체 (Rolling update)
docker-compose up -d --no-deps --build srtgo-web
```

## 🧪 테스트

### 로컬 테스트

```bash
# 빌드
docker-compose build

# 테스트 모드로 실행
docker-compose run --rm srtgo-web python -c "
from backend.main import app
print('FastAPI app loaded successfully')
print(f'Routes: {len(app.routes)}')
"
```

## 🐛 트러블슈팅

### 컨테이너가 시작되지 않음

```bash
# 로그 확인
docker-compose logs

# 상세 로그
docker-compose logs --tail=100 srtgo-web
```

### 빌드 실패

```bash
# 캐시 없이 재빌드
docker-compose build --no-cache

# 기존 이미지 삭제 후 재빌드
docker-compose down --rmi all
docker-compose build
```

### 포트 충돌

```bash
# 8000 포트 사용 중인 프로세스 확인
lsof -i :8000
# 또는
netstat -tuln | grep 8000

# docker-compose.yml에서 포트 변경
```

### 데이터베이스 오류

```bash
# 데이터베이스 초기화
docker-compose down -v
docker-compose up -d
```

### 메모리 부족

```bash
# 메모리 제한 설정 (docker-compose.yml)
services:
  srtgo-web:
    mem_limit: 512m
    mem_reservation: 256m
```

## 📚 추가 리소스

- [Dockerfile 참조](./Dockerfile)
- [docker-compose.yml 참조](./docker-compose.yml)
- [백엔드 README](./backend/README.md)
- [프론트엔드 README](./frontend/README.md)

## 🎯 프로덕션 체크리스트

배포 전 확인사항:

- [ ] SECRET_KEY 변경
- [ ] DEBUG=False 설정
- [ ] HTTPS 설정 (Nginx + Let's Encrypt)
- [ ] 방화벽 설정
- [ ] 백업 전략 수립
- [ ] 모니터링 설정
- [ ] 로그 로테이션 설정
- [ ] 리소스 제한 설정
- [ ] 헬스 체크 테스트
- [ ] 부하 테스트 수행

---

**빌드 시간**: 약 3-5분 (인터넷 속도에 따라)
**이미지 크기**: 약 500-700MB
**메모리 사용량**: 약 200-400MB (idle)
