import asyncio
import contextlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, SessionLocal
from routers import notifications
from scheduler import create_scheduler
from sqs_consumer import start_consumer


async def process_order_event(body: dict) -> None:
    """SQS에서 소비한 주문 이벤트를 처리한다."""
    from schemas import OrderEventPayload
    from routers.notifications import handle_order_event_logic

    payload = OrderEventPayload(**body)
    async with SessionLocal() as db:
        await handle_order_event_logic(payload, db)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = create_scheduler()
    scheduler.start()
    consumer_task = asyncio.create_task(start_consumer(process_order_event))
    yield
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass
    scheduler.shutdown()
    await engine.dispose()


app = FastAPI(
    title="Sallijang Notification Service",
    description="Microservice for managing pickup and order notifications.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.sallijang.shop"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notifications.router)


@app.get("/")
def read_root():
    return {"message": "Sallijang Notification Service. Docs: /docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
