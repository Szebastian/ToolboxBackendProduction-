from dataclasses import dataclass, field
from typing import Optional, List, Literal


@dataclass(frozen=True)
class DecodeVehicleInput:
    vin: str
    engine_number: Optional[str] = None
    owner_id: Optional[str] = None


@dataclass(frozen=True)
class SearchVehicleContext:
    vin: Optional[str] = None
    engine_number: Optional[str] = None
    position: Optional[str] = None          # Delantero/Trasero/Izquierdo/Derecho
    vehicle_id: Optional[str] = None


@dataclass(frozen=True)
class SearchQuery:
    query: str
    ctx: SearchVehicleContext = field(default_factory=SearchVehicleContext)
    limit: int = 20


@dataclass(frozen=True)
class SearchResultItem:
    title: str
    source: Literal['vendor_catalog', 'mercado_libre']
    image_url: Optional[str]
    oem: Optional[str]
    price: Optional[float]
    currency: Optional[str]
    compatible: Literal['yes', 'no', 'unknown']
    catalog_part_id: Optional[str]
    permalink: Optional[str] = None


@dataclass(frozen=True)
class TaxonomyNode:
    slug: str
    name: str
    icon: Optional[str]
    sort_order: int
    children: List["TaxonomyNode"]


@dataclass(frozen=True)
class SearchResponse:
    query: str
    total: int
    results: List[SearchResultItem]
    vehicle: Optional[dict] = None         # {brand, model, year, engine, family, fuel}
