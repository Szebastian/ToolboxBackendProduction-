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
    item_photo_url: Optional[str] = Field(None, alias="itemPhotoUrl")

    class Config:
        populate_by_name = True

class SubmitFastQuoteUseCase:
    def __init__(self, quote_repo: IVendorQuoteRepository, catalog_repo=None):
        self.quote_repo = quote_repo
        self.catalog_repo = catalog_repo

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
            notes=dto.notes,
            item_photo_url=dto.item_photo_url
        )

        await self.quote_repo.create(quote)

        # La foto del vendedor alimenta el catálogo acumulativo del marketplace.
        # El repo de catálogo resuelve el nombre real del repuesto desde los
        # ítems de la solicitud original.
        if self.catalog_repo is not None and dto.item_photo_url:
            await self.catalog_repo.upsert_from_quote(
                parts_request_id=dto.parts_request_id,
                photo_url=dto.item_photo_url,
                price=dto.total_amount,
                currency=dto.currency or "ARS",
                vendor_id=dto.vendor_id,
                quote_id=quote.id,
            )

        return quote
