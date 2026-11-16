from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from src.features.orders.domain.order import Order
from src.features.orders.domain.ports.order_repository_port import IOrderRepository


class MarkOrderPaidInputDTO(BaseModel):
    paid_by_type: Optional[str] = Field(default="customer", alias="paidByType")
    paid_by_user_id: str = Field(..., alias="paidByUserId")

    class Config:
        populate_by_name = True


class MarkOrderPaidUseCase:
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo

    async def execute(self, order_id: str, paid_by_type: str, paid_by_user_id: str) -> Order:
        order = await self.order_repo.find_by_id(order_id)
        if order is None:
            raise ValueError("La orden no existe.")
        if order.status != "pending_payment":
            raise ValueError(f"La orden no está pendiente de pago (estado actual: {order.status}).")

        order.status = "paid"
        order.paid_by_type = paid_by_type if paid_by_type in ("customer", "mechanic") else "customer"
        order.paid_by_user_id = paid_by_user_id
        order.paid_at = datetime.now(timezone.utc)

        await self.order_repo.update_paid(order)
        return order
