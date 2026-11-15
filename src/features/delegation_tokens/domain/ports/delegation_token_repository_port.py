from abc import ABC, abstractmethod
from typing import Optional
from src.features.delegation_tokens.domain.delegation_token import DelegationToken

class IDelegationTokenRepository(ABC):
    @abstractmethod
    async def create(self, token: DelegationToken) -> None:
        pass

    @abstractmethod
    async def find_by_hash(self, token_hash: str) -> Optional[DelegationToken]:
        pass

    @abstractmethod
    async def mark_as_used(self, token_id: str) -> None:
        pass
