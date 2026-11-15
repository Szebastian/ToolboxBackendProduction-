from abc import ABC, abstractmethod
from typing import List, Optional
from src.features.parts_request.domain.parts_request import PartsRequest

class IPartsRequestRepository(ABC):
    @abstractmethod
    async def create(self, request: PartsRequest) -> None:
        pass

    @abstractmethod
    async def find_by_id(self, request_id: str) -> Optional[PartsRequest]:
        pass

    @abstractmethod
    async def list_open_for_quoting(self) -> List[PartsRequest]:
        pass

    @abstractmethod
    async def update_status(self, request_id: str, status: str) -> None:
        pass
