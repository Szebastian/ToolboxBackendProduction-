from abc import ABC, abstractmethod
from src.features.mechanics.domain.mechanic import Mechanic


class IMechanicRepository(ABC):
    @abstractmethod
    async def list_enabled(self, limit: int = 50) -> list[Mechanic]:
        ...
