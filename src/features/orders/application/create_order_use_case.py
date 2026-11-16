from pydantic import BaseModel, Field
from typing import Dict
from datetime import datetime, timezone
from src.features.orders.domain.order import Order
from src.features.orders.domain.ports.order_repository_port import IOrderRepository


class CreateOrderInputDTO(BaseModel):
    quote_id: str = Field(..., alias="quoteId")
    buyer_id: str = Field(..., alias="buyerId")

    class Config:
        populate_by_name = True


class CreateOrderUseCase:
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo

    async def execute(self, dto: CreateOrderInputDTO) -> Order:
        quote = await self.order_repo.find_quote_by_id(dto.quote_id)
        if quote is None:
            raise ValueError("La cotización no existe.")
        if quote.get("status") != "SUBMITTED":
            raise ValueError("La cotización ya no está disponible (ya fue aceptada, rechazada o vencida).")

        expires_at_raw = quote.get("expires_at")
        try:
            expires_at = datetime.fromisoformat(expires_at_raw)
        except (TypeError, ValueError):
            raise ValueError("La cotización tiene una fecha de vencimiento inválida.")
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= datetime.now(timezone.utc):
            raise ValueError("La cotización está vencida.")

        # Crea la orden (pending_payment), registra sus ítems, acepta esta
        # cotización y rechaza las demás del mismo pedido.
        order = await self.order_repo.create_order(quote, dto.buyer_id)
        return order
