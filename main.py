from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import contextlib
from database import engine, Base
from routers import notifications
from scheduler import create_scheduler


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    scheduler = create_scheduler()
    scheduler.start()
    yield
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
    allow_origins=["*"],
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
