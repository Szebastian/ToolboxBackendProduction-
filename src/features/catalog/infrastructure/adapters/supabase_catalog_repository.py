from supabase import Client
from typing import List, Optional
from datetime import datetime, timezone
from src.features.catalog.domain.catalog_part import CatalogPart
from src.features.catalog.domain.ports.catalog_repository_port import ICatalogRepository


def _normalize(name: str) -> str:
    return " ".join(name.lower().split())


class SupabaseCatalogRepository(ICatalogRepository):
    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def upsert_from_quote(self, parts_request_id: str, photo_url: str,
                                price: float, currency: str, vendor_id: str,
                                quote_id: str) -> None:
        # Nombre del repuesto = primer ítem de la solicitud cotizada
        items = self.supabase.table("parts_request_items").select("part_name, part_number") \
            .eq("parts_request_id", parts_request_id).limit(1).execute()
        if not items.data:
            return
        part_name = _normalize(items.data[0]["part_name"])
        part_number = items.data[0].get("part_number")

        existing = self.supabase.table("catalog_parts").select("id, times_quoted, part_number") \
            .eq("part_name", part_name).maybe_single().execute()

        now = datetime.now(timezone.utc).isoformat()
        if existing and existing.data:
            part_id = existing.data["id"]
            times = (existing.data.get("times_quoted") or 0) + 1
            update = {
                "default_photo_url": photo_url,
                "last_quoted_price": price,
                "currency": currency,
                "times_quoted": times,
                "updated_at": now,
            }
            # Completa el número de parte si aún no lo tiene
            if part_number and not existing.data.get("part_number"):
                update["part_number"] = part_number
            self.supabase.table("catalog_parts").update(update).eq("id", part_id).execute()
        else:
            inserted = self.supabase.table("catalog_parts").insert({
                "part_name": part_name,
                "part_number": part_number,
                "default_photo_url": photo_url,
                "last_quoted_price": price,
                "currency": currency,
                "times_quoted": 1,
                "created_at": now,
                "updated_at": now,
            }).execute()
            if not inserted.data:
                raise Exception("Error Supabase Catalog: no se pudo crear la entrada")
            part_id = inserted.data[0]["id"]

        # Historial de fotos (todas las fotos que los vendedores subieron)
        self.supabase.table("catalog_part_photos").insert({
            "catalog_part_id": part_id,
            "vendor_id": vendor_id,
            "vendor_quote_id": quote_id,
            "photo_url": photo_url,
            "quoted_price": price,
        }).execute()

    async def search(self, query: str = "", limit: int = 50) -> List[CatalogPart]:
        q = self.supabase.table("catalog_parts").select("*").order("times_quoted", desc=True).limit(limit)
        if query.strip():
            q = q.ilike("part_name", f"%{_normalize(query)}%")
        res = q.execute()
        if not res or not res.data:
            return []
        return [self._map(r) for r in res.data]

    def _map(self, r: dict) -> CatalogPart:
        return CatalogPart(
            id=r["id"],
            part_name=r["part_name"],
            part_number=r.get("part_number"),
            default_photo_url=r.get("default_photo_url"),
            last_quoted_price=float(r["last_quoted_price"]) if r.get("last_quoted_price") is not None else None,
            currency=r.get("currency", "ARS"),
            times_quoted=r.get("times_quoted", 0),
            created_at=datetime.fromisoformat(r["created_at"]) if r.get("created_at") else None,
            updated_at=datetime.fromisoformat(r["updated_at"]) if r.get("updated_at") else None,
        )
