from abc import ABC, abstractmethod
from typing import List
from src.features.vendor_quoting.domain.quote import VendorQuote

class IVendorQuoteRepository(ABC):
    @abstractmethod
    async def create(self, quote: VendorQuote) -> None:
        pass

    @abstractmethod
    async def find_by_request_id(self, request_id: str) -> List[VendorQuote]:
        pass

    @abstractmethod
    async def find_by_vendor_id(self, vendor_id: str) -> List[VendorQuote]:
        pass
