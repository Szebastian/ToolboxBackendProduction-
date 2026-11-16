from abc import ABC, abstractmethod


class ICatalogRepository(ABC):

    @abstractmethod
    async def upsert_from_quote(self, parts_request_id: str, photo_url: str,
                                price: float, currency: str, vendor_id: str,
                                quote_id: str) -> None:
        """Registra la foto de un vendedor en el catálogo: crea o actualiza la
        entrada del repuesto (nombre tomado de los ítems de la solicitud) y
        agrega la foto al historial."""
        ...

    @abstractmethod
    async def search(self, query: str = "", limit: int = 50) -> list:
        """Busca repuestos del catálogo por nombre (para el buscador del comprador)."""
        ...
