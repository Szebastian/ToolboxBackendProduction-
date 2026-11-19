from fastapi import Depends, APIRouter, HTTPException, status, Query, Request
from src.shared_kernel.infrastructure.security.auth_dependency import usuario_actual
from src.shared_kernel.infrastructure.security.rate_limit import limitar
from src.shared_kernel.infrastructure.database.supabase_client import get_supabase_admin_client
from src.features.catalog.infrastructure.adapters.supabase_catalog_repository import SupabaseCatalogRepository
from src.features.catalog.infrastructure.adapters.supabase_taxonomy_repository import SupabaseTaxonomyRepository
from src.features.catalog.infrastructure.adapters.supabase_catalog_search import SupabaseCatalogSearch
from src.features.catalog.infrastructure.adapters.ml_products_adapter import MLProductsAdapter
from src.features.catalog.infrastructure.adapters.vehicle_cache_adapter import VehicleCacheAdapter
from src.features.catalog.infrastructure.adapters.local_vin_decoder import LocalVinDecoder
from src.features.catalog.application.dtos.catalog_dtos import DecodeVehicleInput, SearchQuery, SearchVehicleContext
from src.features.catalog.application.use_cases.decode_vehicle_use_case import DecodeVehicleUseCase
from src.features.catalog.application.use_cases.get_taxonomy_use_case import GetTaxonomyUseCase
from src.features.catalog.application.use_cases.hybrid_search_use_case import HybridSearchUseCase

router = APIRouter(
    dependencies=[Depends(usuario_actual)], prefix="/catalog", tags=["Catalog"])


def get_catalog_repo() -> SupabaseCatalogRepository:
    supabase = get_supabase_admin_client()
    return SupabaseCatalogRepository(supabase)


@router.get("/")
async def search_catalog(q: str = "", limit: int = 50):
    """Busca repuestos del catálogo (alimentado por las fotos de los vendedores)."""
    try:
        repo = get_catalog_repo()
        parts = await repo.search(q, limit)
        return {"success": True, "data": parts}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/taxonomy")
async def get_taxonomy(engine_family: str | None = Query(default=None, description="nafta | diesel | turbo | aspirado")):
    """Árbol de las 14 categorías + subcategorías filtradas por motorización."""
    try:
        supabase = get_supabase_admin_client()
        uc = GetTaxonomyUseCase(SupabaseTaxonomyRepository(supabase))
        tree = await uc.execute(engine_family)
        return {"success": True, "data": tree}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/decode")
async def decode_vehicle(vin: str = Query(..., min_length=1),
                         engine_number: str | None = Query(default=None)):
    """Decodifica VIN Mercosur (+ motor) — cache-first en vehicle_cache."""
    try:
        supabase = get_supabase_admin_client()
        decoder = LocalVinDecoder()
        uc = DecodeVehicleUseCase(decoder, VehicleCacheAdapter(supabase))
        spec = await uc.execute(DecodeVehicleInput(vin=vin, engine_number=engine_number))
        return {"success": True, "data": spec}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/search")
async def hybrid_search(request: Request,
                        q: str = Query(..., min_length=1),
                        vin: str | None = Query(default=None),
                        engine_number: str | None = Query(default=None),
                        position: str | None = Query(default=None),
                        limit: int = Query(default=20, ge=1, le=50)):
    """Búsqueda híbrida: catálogo vendedor + Mercado Libre.

    Rate limit: 120 consultas/hora por IP.
    """
    limitar(request, 120)
    try:
        supabase = get_supabase_admin_client()
        uc = HybridSearchUseCase(
            decoder=LocalVinDecoder(),
            catalog_search=SupabaseCatalogSearch(supabase),
            ml=MLProductsAdapter(supabase),
            cache=supabase,
        )
        ctx = SearchVehicleContext(vin=vin, engine_number=engine_number, position=position)
        res = await uc.execute(SearchQuery(query=q, ctx=ctx, limit=limit))
        return {
            "success": True,
            "data": {
                "query": res.query,
                "total": res.total,
                "vehicle": res.vehicle,
                "results": [
                    {
                        "title": r.title,
                        "source": r.source,
                        "image_url": r.image_url,
                        "oem": r.oem,
                        "price": r.price,
                        "currency": r.currency,
                        "compatible": r.compatible,
                        "catalog_part_id": r.catalog_part_id,
                        "permalink": r.permalink,
                    } for r in res.results
                ],
            },
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
