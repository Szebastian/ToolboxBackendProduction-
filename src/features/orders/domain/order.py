from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# Orden generada por una cotización aceptada (tabla orders del esquema v2).
# Ciclo de vida: pending_payment → paid → preparing → ready_for_pickup → ...
class Order(BaseModel):
    id: str
    vendor_quote_id: str
    parts_request_id: str
    buyer_id: str
    total_amount: float
    status: str = "pending_payment"
    shipping_cost: float = 0.0
    store_id: Optional[str] = None
    paid_by_type: Optional[str] = None
    paid_by_user_id: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    def is_paid(self) -> bool:
        return self.status == "paid"
