import uuid
from pydantic import BaseModel, Field
from typing import Optional
from src.features.vehicles.domain.vehicle import Vehicle
from src.features.vehicles.domain.ports.vehicle_repository_port import IVehicleRepository

class RegisterVehicleInputDTO(BaseModel):
    owner_id: str = Field(..., alias="ownerId")
    license_plate: str = Field(..., alias="licensePlate")
    brand: str
    model: str
    year: int
    vin: Optional[str] = None
    engine_details: Optional[str] = Field(None, alias="engineDetails")
    green_card_url: Optional[str] = Field(None, alias="greenCardUrl")

    class Config:
        populate_by_name = True

class RegisterVehicleUseCase:
    def __init__(self, vehicle_repo: IVehicleRepository):
        self.vehicle_repo = vehicle_repo

    async def execute(self, dto: RegisterVehicleInputDTO) -> Vehicle:
        clean_plate = "".join(filter(str.isalnum, dto.license_plate)).upper()

        vehicle = Vehicle(
            id=str(uuid.uuid4()),
            owner_id=dto.owner_id,
            license_plate=clean_plate,
            brand=dto.brand,
            model=dto.model,
            year=dto.year,
            vin=dto.vin.upper() if dto.vin else None,
            engine_details=dto.engine_details,
            green_card_url=dto.green_card_url
        )

        await self.vehicle_repo.create(vehicle)
        return vehicle
