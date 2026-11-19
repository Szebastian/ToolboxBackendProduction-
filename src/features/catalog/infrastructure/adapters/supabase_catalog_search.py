"""Port de catálogo propio (búsqueda textual sobre catalog_parts + oem_part_numbers)."""
import re
from supabase import Client
from typing import List
from src.features.catalog.domain.ports.catalog_search_port import ICatalogSearch

_WS = re.compile(r"\s+")


def _norm(text: str) -> str:
    return _WS.sub(" ", (text or "").lower()).strip()


class SupabaseCatalogSearch(ICatalogSearch):

    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def search_text(self, query: str, limit: int = 20) -> List[dict]:
        q = _norm(query)
        if not q:
            return []
        term = f"%{q}%"
        results: List[dict] = []
        # 1) catalog_parts (ilike)
        parts = self.supabase.table("catalog_parts").select(
            "id, part_name, part_number, default_photo_url, last_quoted_price, currency, times_quoted"
        ).ilike("part_name", term).order("times_quoted", desc=True).limit(limit).execute()
        for row in (parts.data or []):
            results.append({
                "title": row["part_name"],
                "image_url": row.get("default_photo_url"),
                "oem": row.get("part_number"),
                "price": float(row["last_quoted_price"]) if row.get("last_quoted_price") is not None else None,
                "currency": row.get("currency") or "ARS",
                "catalog_part_id": row["id"],
                "source": "vendor_catalog",
            })
        # 2) oem_part_numbers: coincidencia exacta o parcial
        oem_rows = self.supabase.table("oem_part_numbers").select(
            "oem_number, brand, catalog_part_id"
        ).ilike("oem_number", term).limit(limit).execute()
        for row in (oem_rows.data or []):
            results.append({
                "title": row["oem_number"],
                "image_url": None,
                "oem": row["oem_number"],
                "price": None,
                "currency": None,
                "catalog_part_id": row.get("catalog_part_id"),
                "source": "vendor_catalog",
            })
        return results[:limit]
