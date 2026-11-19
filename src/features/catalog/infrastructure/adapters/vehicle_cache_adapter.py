"""Caché de decodificación vehicular, persistida en la tabla vehicle_cache."""
from datetime import datetime, timezone
from supabase import Client
from typing import Optional
from src.features.catalog.domain.vehicle_spec import VehicleSpec


class VehicleCacheAdapter:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def find_by_vin(self, vin: str) -> Optional[dict]:
        res = self.supabase.table("vehicle_cache").select("*") \
            .eq("vin", vin).maybe_single().execute()
        return res.data if res and res.data else None

    async def save(self, spec: VehicleSpec, raw: Optional[dict] = None) -> None:
        vin = spec.vin
        if not vin:
            return
        existing = await self.find_by_vin(vin)
        payload = {
            "vin": vin,
            "make": spec.brand,
            "model": spec.model,
            "year": spec.year,
            "engine": (spec.engine.label or None),
            "market_origin": (raw or {}).get("market_origin"),
            "raw_api_response": raw or {},
            "last_searched_at": datetime.now(timezone.utc).isoformat(),
        }
        if existing:
            payload["search_count"] = (existing.get("search_count") or 0) + 1
            self.supabase.table("vehicle_cache").update(payload).eq("vin", vin).execute()
        else:
            payload["search_count"] = 1
            self.supabase.table("vehicle_cache").insert(payload).execute()
