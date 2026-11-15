from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class VendorQuote:
    id: str
    parts_request_id: str
    vendor_id: str
    total_amount: float
    currency: str = "ARS"
    validity_hours: int = 24
    expires_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "SUBMITTED"
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

