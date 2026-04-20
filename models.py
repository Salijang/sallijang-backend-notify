from sqlalchemy import Column, Integer, String, Boolean, DateTime
from database import Base
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))


def kst_now() -> datetime:
    """현재 한국 표준시(KST, UTC+9)를 반환합니다."""
    return datetime.now(KST).replace(tzinfo=None)


class NotificationSettings(Base):
    __tablename__ = "notification_settings"
    __table_args__ = {"schema": "notification_schema"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    new_order = Column(Boolean, default=True, nullable=False)
    review = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=kst_now)


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = {"schema": "notification_schema"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    # order_confirmed | new_order | pickup_completed | order_cancelled | pickup_reminder
    event_type = Column(String, nullable=False)
    order_id = Column(Integer, nullable=True, index=True)
    order_number = Column(String, nullable=True)
    store_name = Column(String, nullable=True)
    product_names = Column(String, nullable=True)  # 쉼표 구분 문자열
    pickup_expected_at = Column(String, nullable=True)  # "HH:MM"
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=kst_now)
