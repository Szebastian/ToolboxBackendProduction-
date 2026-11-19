from abc import ABC, abstractmethod
from typing import List, Optional


class IMercadoLibreClient(ABC):

    @abstractmethod
    async def search_products(self, query: str, vehicle_context: dict,
                              limit: int = 5) -> List[dict]:
        """GET /products/search?site_id=MLA&status=active&q=...
        Devuelve lista de items con {title, image_url, part_number, price, currency, permalink}.
        Ante cualquier error -> lista vacía (nunca propaga excepción a la búsqueda)."""
        ...

    @abstractmethod
    async def extract_oem_numbers(self, items: List[dict]) -> List[str]:
        """Extrae números OEM (PART_NUMBER) de products ML."""
        ...
