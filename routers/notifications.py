from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
import os
import httpx

from database import get_db
from deps import get_current_user, CurrentUser
import models
import schemas

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])

PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8001")


async def get_store_owner_id(store_id: int) -> Optional[int]:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{PRODUCT_SERVICE_URL}/api/v1/stores/{store_id}",
                timeout=5.0,
            )
        if resp.status_code == 200:
            return resp.json().get("owner_id")
    except Exception as e:
        print(f"[Notify] store owner 조회 실패 (store_id={store_id}): {e}")
    return None


async def get_settings(user_id: int, db: AsyncSession) -> models.NotificationSettings:
    result = await db.execute(
        select(models.NotificationSettings).filter(models.NotificationSettings.user_id == user_id)
    )
    settings = result.scalars().first()
    if not settings:
        settings = models.NotificationSettings(user_id=user_id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings


@router.get("/settings/{user_id}", response_model=schemas.NotificationSettingsResponse)
async def get_notification_settings(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return await get_settings(user_id, db)


@router.patch("/settings/{user_id}", response_model=schemas.NotificationSettingsResponse)
async def update_notification_settings(
    user_id: int,
    body: schemas.NotificationSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    settings = await get_settings(user_id, db)
    if body.new_order is not None:
        settings.new_order = body.new_order
    if body.review is not None:
        settings.review = body.review
    if body.slack_webhook_url is not None:
        settings.slack_webhook_url = body.slack_webhook_url or None
    await db.commit()
    await db.refresh(settings)
    return settings


@router.get("/", response_model=List[schemas.NotificationResponse])
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(
        select(models.Notification)
        .filter(models.Notification.user_id == current_user.user_id)
        .order_by(models.Notification.created_at.desc())
        .limit(50)
    )
    return result.scalars().all()


@router.patch("/{notification_id}/read")
async def mark_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(
        select(models.Notification).filter(models.Notification.id == notification_id)
    )
    notif = result.scalars().first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notif.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    notif.is_read = True
    await db.commit()
    return {"ok": True}


@router.patch("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(
        select(models.Notification).filter(
            models.Notification.user_id == current_user.user_id,
            models.Notification.is_read == False,
        )
    )
    for notif in result.scalars().all():
        notif.is_read = True
    await db.commit()
    return {"ok": True}


async def handle_order_event_logic(payload: schemas.OrderEventPayload, db: AsyncSession) -> None:
    """SQS 컨슈머와 HTTP 엔드포인트 양쪽에서 재사용하는 주문 이벤트 처리 로직."""
    from sns_client import publish_slack_event

    product_names_str = ", ".join(payload.product_names)

    if payload.event_type == "order_confirmed":
        buyer_event, seller_event = "order_confirmed", "new_order"
    elif payload.event_type == "order_cancelled_by_buyer":
        buyer_event, seller_event = "order_cancelled_self", "order_cancelled"
    elif payload.event_type == "order_cancelled_by_seller":
        buyer_event, seller_event = "order_cancelled", "order_cancelled_self"
    elif payload.event_type == "pickup_completed":
        buyer_event, seller_event = "pickup_completed", None
    else:
        buyer_event, seller_event = payload.event_type, payload.event_type

    db.add(models.Notification(
        user_id=payload.buyer_id,
        event_type=buyer_event,
        order_id=payload.order_id,
        order_number=payload.order_number,
        store_name=payload.store_name,
        product_names=product_names_str,
        pickup_expected_at=payload.pickup_expected_at,
    ))

    if seller_event is not None:
        seller_user_id = await get_store_owner_id(payload.store_id)
        if seller_user_id:
            seller_settings = await get_settings(seller_user_id, db)
            if seller_settings.new_order:
                db.add(models.Notification(
                    user_id=seller_user_id,
                    event_type=seller_event,
                    order_id=payload.order_id,
                    order_number=payload.order_number,
                    store_name=payload.store_name,
                    product_names=product_names_str,
                    pickup_expected_at=payload.pickup_expected_at,
                ))
                if seller_event == "new_order" and seller_settings.slack_webhook_url:
                    await publish_slack_event({
                        "webhook_url": seller_settings.slack_webhook_url,
                        "store_name": payload.store_name,
                        "order_number": payload.order_number,
                        "product_names": product_names_str,
                        "pickup_expected_at": payload.pickup_expected_at or "",
                    })

    await db.commit()


@router.post("/internal/order-event", status_code=201)
async def handle_order_event(
    payload: schemas.OrderEventPayload,
    db: AsyncSession = Depends(get_db),
):
    await handle_order_event_logic(payload, db)
    return {"ok": True}


@router.post("/internal/review-event", status_code=201)
async def handle_review_event(
    payload: schemas.ReviewEventPayload,
    db: AsyncSession = Depends(get_db),
):
    seller_user_id = await get_store_owner_id(payload.store_id)
    if seller_user_id:
        seller_settings = await get_settings(seller_user_id, db)
        if seller_settings.review:
            db.add(models.Notification(
                user_id=seller_user_id,
                event_type="new_review",
                store_name=payload.store_name,
                product_names=f"별점 {payload.rating}점",
            ))
            await db.commit()
    return {"ok": True}
