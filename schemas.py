from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    event_type: str
    order_id: Optional[int] = None
    order_number: Optional[str] = None
    store_name: Optional[str] = None
    product_names: Optional[str] = None
    pickup_expected_at: Optional[str] = None
    is_read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class OrderEventPayload(BaseModel):
    """Order Service → Notify Service 이벤트 페이로드"""
    event_type: str  # order_confirmed | pickup_completed | order_cancelled
    order_id: int
    order_number: str
    buyer_id: int
    store_id: int
    store_name: str
    product_names: List[str]
    pickup_expected_at: Optional[str] = None
