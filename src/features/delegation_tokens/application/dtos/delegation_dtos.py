from pydantic import BaseModel, Field
from typing import Optional

class DelegateRequestInputDTO(BaseModel):
    parts_request_id: str = Field(..., alias="partsRequestId")
    mechanic_phone: str = Field(..., alias="mechanicPhone")
    mechanic_name: str = Field(..., alias="mechanicName")
    duration_hours: Optional[int] = Field(default=48, alias="durationHours")

    class Config:
        populate_by_name = True

class DelegateRequestOutputDTO(BaseModel):
    token_id: str = Field(..., alias="tokenId")
    access_url: str = Field(..., alias="accessUrl")
    expires_at: str = Field(..., alias="expiresAt")

    class Config:
        populate_by_name = True

