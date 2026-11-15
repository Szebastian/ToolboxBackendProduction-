from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class RequestItem:
    id: str
    part_name: str
    quantity: int = 1
    part_number: Optional[str] = None
    description: Optional[str] = None
    sample_photo_url: Optional[str] = None
    is_technical_specified: bool = False

@dataclass
class PartsRequest:
    id: str
    customer_id: str
    vehicle_id: str
    status: str
    is_delegated: bool
    urgency_level: str = "STANDARD"
    items: List[RequestItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

