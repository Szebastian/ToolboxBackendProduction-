from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

@dataclass
class DelegationToken:
    id: str
    parts_request_id: str
    token_hash: str
    raw_token: str
    mechanic_phone: str
    mechanic_name: str
    expires_at: datetime
    used_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        now = datetime.now(timezone.utc)
        return now > self.expires_at

    def is_consumed(self) -> bool:
        return self.used_at is not None

    def is_valid(self) -> bool:
        return not self.is_expired() and not self.is_consumed()

