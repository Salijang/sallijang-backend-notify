from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.executors.asyncio import AsyncIOExecutor
from sqlalchemy.future import select
from datetime import datetime, timezone, timedelta
from typing import Optional
import os
import httpx

import models
from database import SessionLocal
from redis_sse import publish_sse
from routers.notifications import get_settings

KST = timezone(timedelta(hours=9))
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8002")


def _notif_to_dict(notif: models.Notification) -> dict:
    return {
        "id": notif.id,
        "user_id": notif.user_id,
        "event_type": notif.event_type,
        "order_id": notif.order_id,
        "order_number": notif.order_number,
        "store_name": notif.store_name,
        "product_names": notif.product_names,
        "pickup_expected_at": notif.pickup_expected_at,
        "is_read": notif.is_read,
        "created_at": notif.created_at.isoformat() if notif.created_at else None,
    }



async def check_pickup_reminders():
    """매 분 실행: 픽업 15분 전 주문에 대해 알림을 생성합니다."""
    now = datetime.now(KST).replace(tzinfo=None)

    time_min = (now + timedelta(minutes=13)).strftime("%H:%M")
    time_max = (now + timedelta(minutes=17)).strftime("%H:%M")

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{ORDER_SERVICE_URL}/api/v1/orders/internal/pending", timeout=10.0
            )
        if resp.status_code != 200:
            return
        orders = resp.json()
    except Exception as e:
        print(f"[Scheduler] Order service 조회 실패: {e}")
        return

    async with SessionLocal() as db:
        notifications_to_publish: list[tuple[models.Notification, int]] = []

        for order in orders:
            pickup_at: Optional[str] = order.get("pickup_expected_at")
            if not pickup_at:
                continue

            if not (time_min <= pickup_at <= time_max):
                continue

            order_id: int = order["id"]

            existing = await db.execute(
                select(models.Notification).filter(
                    models.Notification.order_id == order_id,
                    models.Notification.event_type == "pickup_reminder",
                )
            )
            if existing.scalars().first():
                continue

            product_names = ", ".join(
                item["product_name"] for item in order.get("items", [])
            )

            buyer_settings = await get_settings(order["buyer_id"], db)
            if not buyer_settings.new_order:
                continue

            buyer_notif = models.Notification(
                user_id=order["buyer_id"],
                event_type="pickup_reminder",
                order_id=order_id,
                order_number=order["order_number"],
                store_name=order["store_name"],
                product_names=product_names,
                pickup_expected_at=pickup_at,
            )
            db.add(buyer_notif)
            notifications_to_publish.append((buyer_notif, order["buyer_id"]))

        await db.commit()

        for notif, user_id in notifications_to_publish:
            await db.refresh(notif)
            await publish_sse(f"sse:notify:{user_id}", _notif_to_dict(notif))

        print(f"[Scheduler] 픽업 알림 체크 완료 ({now.strftime('%H:%M')})")


def create_scheduler() -> AsyncIOScheduler:
    """픽업 리마인더 잡이 등록된 APScheduler 인스턴스를 생성합니다."""
    scheduler = AsyncIOScheduler(
        executors={"default": AsyncIOExecutor()},
        timezone="Asia/Seoul",
    )
    scheduler.add_job(check_pickup_reminders, "interval", minutes=1, id="pickup_reminder")
    return scheduler
