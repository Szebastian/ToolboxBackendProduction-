from abc import ABC, abstractmethod
from typing import List
from src.features.catalog.domain.catalog_category import Category, SubCategory


class ITaxonomyRepository(ABC):

    @abstractmethod
    async def get_categories(self) -> List[Category]:
        """Devuelve las 14 categorías raíz ordenadas por sort_order."""
        ...

    @abstractmethod
    async def get_subcategories(self, category_id: str) -> List[SubCategory]:
        """Devuelve las subcategorías activas de una categoría raíz."""
        ...

    @abstractmethod
    async def get_subcategories_by_slug(self, slug: str) -> List[SubCategory]:
        """Devuelve las subcategorías activas de una categoría dada por slug."""
        ...
