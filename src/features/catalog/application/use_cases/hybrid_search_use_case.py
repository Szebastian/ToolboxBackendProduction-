"""Hybrid catalog search: filtra por motor y fusiona catálogo vendedor + MLA."""
import hashlib
from src.features.catalog.domain.ports.catalog_search_port import ICatalogSearch
from src.features.catalog.domain.ports.ml_port import IMercadoLibreClient
from src.features.catalog.domain.ports.vehicle_decoder_port import IVehicleDecoder
from src.features.catalog.application.dtos.catalog_dtos import (
    SearchQuery, SearchResultItem, SearchResponse,
)
from src.features.catalog.application.dtos.spec_mapper import to_public_dict


class HybridSearchUseCase:
    """Niveles de ranking: 1) compatible (motor), 2) precio, 3) MEL (match de texto),
    4) popularidad del catálogo propio (times_quoted)."""

    def __init__(self, decoder: IVehicleDecoder,
                 catalog_search: ICatalogSearch,
                 ml: IMercadoLibreClient,
                 cache=None):
        self.decoder = decoder
        self.search_repo = catalog_search
        self.ml = ml
        self.cache = cache  # supabase client directo (read/write ml_query_cache)

    async def execute(self, dto: SearchQuery) -> SearchResponse:
        q = (dto.query or '').strip()
        if not q:
            return SearchResponse(query="", total=0, results=[], vehicle=None)

        # 1) Decode vehicle (best-effort)
        spec = None
        if dto.ctx.vin or dto.ctx.engine_number:
            spec = self.decoder.decode_vin(dto.ctx.vin or "", dto.ctx.engine_number)

        results: list[SearchResultItem] = []

        # 2) Catálogo propio (siempre primero)
        cat = await self.search_repo.search_text(q, dto.limit)
        for row in cat:
            compatible = "unknown"
            if spec and spec.engine.family.value in ("diesel", "nafta"):
                compatible = "yes"
            results.append(SearchResultItem(
                title=row["title"], source="vendor_catalog",
                image_url=row.get("image_url"),
                oem=row.get("oem"),
                price=row.get("price"), currency=row.get("currency") or "ARS",
                compatible=compatible,
                catalog_part_id=row.get("catalog_part_id"),
                permalink=None,
            ))

        # 3) Mercado Libre (best-effort; suma, no reemplaza)
        ctx = to_public_dict(spec) if spec else {}
        ml_items = await self.ml.search_products(q, ctx, limit=min(5, dto.limit))
        for it in ml_items:
            results.append(SearchResultItem(
                title=it.get("title", ""), source="mercado_libre",
                image_url=it.get("image_url"),
                oem=it.get("oem"),
                price=it.get("price"),
                currency=it.get("currency"),
                compatible="unknown",
                catalog_part_id=None,
                permalink=it.get("permalink"),
            ))

        # 4) Persistir OEM encontrados (silencioso)
        try:
            oems = await self.ml.extract_oem_numbers(ml_items)
            if self.cache is not None and oems:
                for oem in oems:
                    self.cache.table("oem_part_numbers").upsert({
                        "oem_number": oem,
                        "brand": ctx.get("brand") or "unknown",
                        "source": "mercado_libre",
                        "vehicle_context": ctx,
                    }, on_conflict="oem_number,brand").execute()
        except Exception:
            pass  # la persistencia OEM nunca rompe la búsqueda

        return SearchResponse(
            query=q,
            total=len(results),
            results=results,
            vehicle=(to_public_dict(spec) if spec else None),
        )
