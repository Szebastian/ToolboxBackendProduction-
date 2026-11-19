"""Port para consultar el catálogo propio (SQL ILIKE)."""
from abc import ABC, abstractmethod
from typing import List


class ICatalogSearch(ABC):

    @abstractmethod
    async def search_text(self, query: str, limit: int = 20) -> List[dict]:
        """Busca en catalog_parts + oem_part_numbers por texto normalizado.
        Devuelve dicts con {title, image_url, oem, price, currency, catalog_part_id, source}."""
        ...
