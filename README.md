# sallijang-backend-notify

알림 처리 서비스입니다.

## 기술 스택

- **Python 3.11** / FastAPI
- **PostgreSQL** (asyncpg, SQLAlchemy, Alembic)
- **Redis** (SSE 실시간 알림 채널)
- **AWS SQS** (Order 서비스 주문 이벤트 수신)
- **AWS SNS + Lambda** (Slack 웹훅 연동)
- **APScheduler** (픽업 리마인더 배치)

## 주요 기능

- SSE 스트림으로 사용자에게 실시간 알림 푸시
- SQS 컨슈머: Order 서비스의 주문 이벤트 수신 및 알림 생성
- 픽업 15분 전 자동 리마인더 (APScheduler, 매 분 실행)
- Slack 알림 (SNS → Lambda → Slack 웹훅)
- 알림 읽음 처리 (개별 / 전체)
- 사용자별 알림 수신 설정 관리

## 알림 이벤트 타입

| 이벤트 | 수신자 | 내용 |
|--------|--------|------|
| `order_confirmed` | 구매자 / 판매자 | 주문 확정 |
| `order_cancelled_by_buyer` | 판매자 | 구매자 주문 취소 |
| `order_cancelled_by_seller` | 구매자 | 판매자 주문 취소 |
| `pickup_completed` | 구매자 | 픽업 완료 |
| `pickup_reminder` | 구매자 | 픽업 15분 전 리마인더 |
| `new_review` | 판매자 | 새 리뷰 등록 |

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/v1/notifications/stream` | SSE 실시간 알림 스트림 |
| GET | `/api/v1/notifications/` | 최근 50개 알림 조회 |
| PATCH | `/api/v1/notifications/{id}/read` | 개별 알림 읽음 처리 |
| PATCH | `/api/v1/notifications/read-all` | 전체 알림 읽음 처리 |
| GET | `/api/v1/notifications/settings/{user_id}` | 알림 설정 조회 |
| PATCH | `/api/v1/notifications/settings/{user_id}` | 알림 설정 수정 |
| POST | `/api/v1/notifications/internal/order-event` | 주문 이벤트 수신 (내부 API) |
| POST | `/api/v1/notifications/internal/review-event` | 리뷰 이벤트 수신 (내부 API) |

## 환경 변수

| 변수명 | 설명 |
|--------|------|
| `DB_HOST` | PostgreSQL 호스트 |
| `DB_PORT` | PostgreSQL 포트 (기본값: 5432) |
| `DB_USER` | DB 사용자명 |
| `DB_NAME` | DB 이름 |
| `DB_PASSWORD` | DB 비밀번호 (미설정 시 RDS IAM 인증) |
| `AWS_REGION` | AWS 리전 (기본값: ap-northeast-2) |
| `SQS_QUEUE_URL` | SQS 큐 URL |
| `REDIS_URL` | Redis 연결 URL |
| `ORDER_SERVICE_URL` | Order 서비스 URL |
| `PRODUCT_SERVICE_URL` | Product 서비스 URL |
| `SECRET_KEY` | JWT 서명 키 |

## 로컬 실행

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```

## Docker

```bash
docker build -t sallijang-notify .
docker run -p 8003:8003 \
  -e DB_HOST=<host> \
  -e DB_USER=<user> \
  -e DB_PASSWORD=<password> \
  -e REDIS_URL=redis://redis:6379 \
  -e SQS_QUEUE_URL=<queue_url> \
  -e ORDER_SERVICE_URL=http://order-service:8002 \
  -e SECRET_KEY=<secret> \
  sallijang-notify
```
