import uuid
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field
from typing import Optional
from src.features.vendor_quoting.domain.quote import VendorQuote
from src.features.vendor_quoting.domain.ports.vendor_quote_repository_port import IVendorQuoteRepository

class SubmitQuoteInputDTO(BaseModel):
    parts_request_id: str = Field(..., alias="partsRequestId")
    vendor_id: str = Field(..., alias="vendorId")
    total_amount: float = Field(..., alias="totalAmount")
    currency: Optional[str] = "ARS"
    validity_hours: Optional[int] = Field(default=24, alias="validityHours")
    notes: Optional[str] = None

    class Config:
        populate_by_name = True

class SubmitFastQuoteUseCase:
    def __init__(self, quote_repo: IVendorQuoteRepository):
        self.quote_repo = quote_repo

    async def execute(self, dto: SubmitQuoteInputDTO) -> VendorQuote:
        if dto.total_amount <= 0:
            raise ValueError("El monto total debe ser mayor a 0.")

        validity = dto.validity_hours or 24
        expires_at = datetime.now(timezone.utc) + timedelta(hours=validity)

        quote = VendorQuote(
            id=str(uuid.uuid4()),
            parts_request_id=dto.parts_request_id,
            vendor_id=dto.vendor_id,
            total_amount=dto.total_amount,
            currency=dto.currency or "ARS",
            validity_hours=validity,
            expires_at=expires_at,
            status="SUBMITTED",
            notes=dto.notes
        )

        await self.quote_repo.create(quote)
        return quote
