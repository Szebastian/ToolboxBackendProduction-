from dataclasses import dataclass
from typing import Optional


@dataclass
class Mechanic:
    """Mecánico habilitado de la red Toolbox (perfil con role='mechanic')."""
    id: str
    full_name: str
    business_name: Optional[str]
    phone: Optional[str]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "full_name": self.full_name,
            "business_name": self.business_name,
            "phone": self.phone,
        }
