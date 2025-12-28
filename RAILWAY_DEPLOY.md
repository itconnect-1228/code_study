# Railway Deployment Guide

## Prerequisites
- Railway 계정 (https://railway.app)
- GitHub 저장소 연결

## 배포 구조

이 프로젝트는 두 개의 서비스로 배포됩니다:
1. **Backend** (Python/FastAPI) - `backend/` 폴더
2. **Frontend** (React/Vite) - `frontend/` 폴더

## Step 1: Railway 프로젝트 생성

1. Railway 대시보드에서 **New Project** 클릭
2. **Deploy from GitHub repo** 선택
3. 저장소 연결

## Step 2: Backend 서비스 배포

### 2.1 서비스 생성
1. **Add New Service** > **GitHub Repo** 선택
2. Root Directory: `backend` 설정

### 2.2 환경 변수 설정 (Variables 탭)

**필수 환경 변수:**
```
# Application
APP_ENV=production
DEBUG=false
SECRET_KEY=<생성한_시크릿_키>

# Database (Railway PostgreSQL 추가 시 자동 설정됨)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# AI Service
GEMINI_API_KEY=<your_gemini_api_key>
GEMINI_MODEL=gemini-2.0-flash-exp

# CORS (프론트엔드 URL로 설정)
CORS_ORIGINS=https://your-frontend.railway.app

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 2.3 PostgreSQL 추가
1. **Add New Service** > **Database** > **PostgreSQL**
2. Backend 서비스의 Variables에서 `${{Postgres.DATABASE_URL}}` 참조 설정

### 2.4 Redis 추가 (선택사항 - Celery 사용 시)
1. **Add New Service** > **Database** > **Redis**
2. 환경 변수 설정:
```
REDIS_URL=${{Redis.REDIS_URL}}
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}
```

## Step 3: Frontend 서비스 배포

### 3.1 서비스 생성
1. **Add New Service** > **GitHub Repo** 선택
2. Root Directory: `frontend` 설정

### 3.2 환경 변수 설정

**필수 환경 변수:**
```
# Backend API URL (Backend 서비스 배포 후 URL 확인)
VITE_API_BASE_URL=https://your-backend.railway.app/api/v1
```

> **중요**: Vite는 빌드 시점에 `VITE_` 접두사 환경 변수를 주입합니다.
> 환경 변수 변경 후 반드시 재배포해야 합니다.

## Step 4: 도메인 설정

### Backend
1. Backend 서비스 > **Settings** > **Networking**
2. **Generate Domain** 클릭
3. 생성된 URL을 Frontend의 `VITE_API_BASE_URL`에 설정

### Frontend
1. Frontend 서비스 > **Settings** > **Networking**
2. **Generate Domain** 클릭
3. 생성된 URL을 Backend의 `CORS_ORIGINS`에 추가

## Step 5: 배포 확인

### Backend 헬스체크
```bash
curl https://your-backend.railway.app/health
```

응답 예시:
```json
{"status": "healthy", "timestamp": "2024-01-01T00:00:00Z", "version": "1.0.0"}
```

### Frontend 접속
브라우저에서 `https://your-frontend.railway.app` 접속

## 트러블슈팅

### 빌드 실패
- Railway 로그 확인: 서비스 > **Deployments** > 해당 배포 클릭
- `nixpacks.toml` 및 `railway.toml` 설정 확인

### CORS 오류
- Backend의 `CORS_ORIGINS`에 Frontend URL이 포함되어 있는지 확인
- 프로토콜(https) 포함 필수

### 환경 변수 미적용
- Vite 환경 변수: `VITE_` 접두사 필수, 변경 후 재배포 필요
- Backend: 재배포 또는 서비스 재시작

### 데이터베이스 연결 실패
- PostgreSQL 서비스가 실행 중인지 확인
- `DATABASE_URL` 환경 변수가 올바르게 참조되는지 확인

## 유용한 Railway CLI 명령어

```bash
# Railway CLI 설치
npm install -g @railway/cli

# 로그인
railway login

# 프로젝트 연결
railway link

# 로그 확인
railway logs

# 환경 변수 확인
railway variables

# 로컬에서 Railway 환경으로 실행
railway run python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```
