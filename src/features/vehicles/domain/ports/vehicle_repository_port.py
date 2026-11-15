from abc import ABC, abstractmethod
from typing import List, Optional
from src.features.vehicles.domain.vehicle import Vehicle

class IVehicleRepository(ABC):
    @abstractmethod
    async def create(self, vehicle: Vehicle) -> None:
        pass

    @abstractmethod
    async def find_by_owner_id(self, owner_id: str) -> List[Vehicle]:
        pass

    @abstractmethod
    async def find_by_id(self, vehicle_id: str) -> Optional[Vehicle]:
        pass
