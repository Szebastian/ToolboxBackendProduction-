from dataclasses import dataclass
from typing import Optional

@dataclass
class Vehicle:
    id: str
    owner_id: str
    license_plate: str
    brand: str
    model: str
    year: int
    vin: Optional[str] = None
    engine_details: Optional[str] = None
    green_card_url: Optional[str] = None

