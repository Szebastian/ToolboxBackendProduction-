import uuid
from pydantic import BaseModel, Field
from typing import List, Optional
from src.features.parts_request.domain.parts_request import PartsRequest, RequestItem
from src.features.parts_request.domain.ports.parts_request_repository_port import IPartsRequestRepository

class CreateItemDTO(BaseModel):
    part_name: str = Field(..., alias="partName")
    part_number: Optional[str] = Field(None, alias="partNumber")
    description: Optional[str] = None
    quantity: Optional[int] = 1
    sample_photo_url: Optional[str] = Field(None, alias="samplePhotoUrl")

    class Config:
        populate_by_name = True

class CreatePartsRequestInputDTO(BaseModel):
    customer_id: str = Field(..., alias="customerId")
    vehicle_id: str = Field(..., alias="vehicleId")
    is_delegated: bool = Field(default=False, alias="isDelegated")
    urgency_level: Optional[str] = Field(default="STANDARD", alias="urgencyLevel")
    items: Optional[List[CreateItemDTO]] = []

    class Config:
        populate_by_name = True

class CreatePartsRequestUseCase:
    def __init__(self, request_repo: IPartsRequestRepository):
        self.request_repo = request_repo

    async def execute(self, dto: CreatePartsRequestInputDTO) -> PartsRequest:
        request_id = str(uuid.uuid4())
        status = "PENDING_MECHANIC" if dto.is_delegated else "OPEN_FOR_QUOTING"

        items = [
            RequestItem(
                id=str(uuid.uuid4()),
                part_name=i.part_name,
                part_number=i.part_number,
                description=i.description,
                quantity=i.quantity or 1,
                sample_photo_url=i.sample_photo_url,
                is_technical_specified=not dto.is_delegated
            )
            for i in (dto.items or [])
        ]

        request = PartsRequest(
            id=request_id,
            customer_id=dto.customer_id,
            vehicle_id=dto.vehicle_id,
            status=status,
            is_delegated=dto.is_delegated,
            urgency_level=dto.urgency_level or "STANDARD",
            items=items
        )

        await self.request_repo.create(request)
        return request
