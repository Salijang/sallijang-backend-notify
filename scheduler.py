from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.executors.asyncio import AsyncIOExecutor
from sqlalchemy.future import select
from datetime import datetime, timezone, timedelta
from typing import Optional
import os
import httpx

import models
from database import SessionLocal

KST = timezone(timedelta(hours=9))
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8002")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8001")


async def _get_store_owner_id(store_id: int) -> Optional[int]:
    """Product Service에서 store_id로 owner_id를 조회합니다. 실패 시 None 반환."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{PRODUCT_SERVICE_URL}/api/v1/stores/{store_id}", timeout=5.0
            )
        if resp.status_code == 200:
            return resp.json().get("owner_id")
    except Exception:
        pass
    return None


async def check_pickup_reminders():
    """매 분 실행: 픽업 15분 전 주문에 대해 알림을 생성합니다."""
    now = datetime.now(KST).replace(tzinfo=None)

    # 13~17분 후 픽업 예정 범위 (2분 여유로 중복 방지는 DB 체크로 처리)
    time_min = (now + timedelta(minutes=13)).strftime("%H:%M")
    time_max = (now + timedelta(minutes=17)).strftime("%H:%M")

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{ORDER_SERVICE_URL}/api/v1/orders/?status=pending", timeout=10.0
            )
        if resp.status_code != 200:
            return
        orders = resp.json()
    except Exception as e:
        print(f"[Scheduler] Order service 조회 실패: {e}")
        return

    async with SessionLocal() as db:
        for order in orders:
            pickup_at: Optional[str] = order.get("pickup_expected_at")
            if not pickup_at:
                continue

            if not (time_min <= pickup_at <= time_max):
                continue

            order_id: int = order["id"]

            # 이미 픽업 알림이 생성된 주문이면 스킵
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

            # 구매자 알림
            db.add(models.Notification(
                user_id=order["buyer_id"],
                event_type="pickup_reminder",
                order_id=order_id,
                order_number=order["order_number"],
                store_name=order["store_name"],
                product_names=product_names,
                pickup_expected_at=pickup_at,
            ))

            # 판매자 알림
            store_id = order.get("store_id")
            if store_id:
                seller_user_id = await _get_store_owner_id(store_id)
                if seller_user_id:
                    db.add(models.Notification(
                        user_id=seller_user_id,
                        event_type="pickup_reminder",
                        order_id=order_id,
                        order_number=order["order_number"],
                        store_name=order["store_name"],
                        product_names=product_names,
                        pickup_expected_at=pickup_at,
                    ))

        await db.commit()
        print(f"[Scheduler] 픽업 알림 체크 완료 ({now.strftime('%H:%M')})")


def create_scheduler() -> AsyncIOScheduler:
    """픽업 리마인더 잡이 등록된 APScheduler 인스턴스를 생성합니다."""
    scheduler = AsyncIOScheduler(
        executors={"default": AsyncIOExecutor()},
        timezone="Asia/Seoul",
    )
    scheduler.add_job(check_pickup_reminders, "interval", minutes=1, id="pickup_reminder")
    return scheduler
