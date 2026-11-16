from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from src.features.orders.domain.order import Order


class IOrderRepository(ABC):

    @abstractmethod
    async def find_quote_by_id(self, quote_id: str) -> Optional[Dict]:
        ...

    @abstractmethod
    async def create_order(self, quote: Dict, buyer_id: str) -> Order:
        ...

    @abstractmethod
    async def accept_quote(self, quote_id: str) -> None:
        ...

    @abstractmethod
    async def reject_other_quotes(self, request_id: str, accepted_quote_id: str) -> None:
        ...

    @abstractmethod
    async def find_by_id(self, order_id: str) -> Optional[Order]:
        ...

    @abstractmethod
    async def find_by_buyer(self, buyer_id: str) -> List[Order]:
        ...

    @abstractmethod
    async def update_paid(self, order: Order) -> None:
        ...
