from dataclasses import dataclass
from datetime import datetime
from typing import Optional


# Entrada del catálogo acumulativo: nace y crece con las fotos que los
# vendedores adjuntan al confirmar una cotización.
@dataclass
class CatalogPart:
    id: str
    part_name: str
    part_number: Optional[str]
    default_photo_url: Optional[str]
    last_quoted_price: Optional[float]
    currency: str = "ARS"
    times_quoted: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
