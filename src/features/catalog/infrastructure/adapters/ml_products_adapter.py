"""Adapter Mercado Libre (solo lectura, tolerante a fallos, con caché).

Política: si ML responde, devolvemos fotos/OEM válidos para mostrarse como
referencia; si falla (red, 429, 4xx/5xx) NUNCA propagamos la excepción:
devolvemos lista vacía y la búsqueda continúa.

Cache: clave = sha256(query + contexto vehicular) en tabla ml_query_cache,
TTL configurable (default 3 días). Si la caché responde, no tocamos la red.
"""
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from supabase import Client
from src.features.catalog.domain.ports.ml_port import IMercadoLibreClient

_ML_SEARCH = "https://api.mercadolibre.com/products/search"
_ML_SITE = "MLA"
_CACHE_TTL_DAYS = int(os.getenv("MLA_CACHE_TTL_DAYS", "3"))


def _enabled() -> bool:
    return os.getenv("MLA_ENABLED", "true").strip().lower() in ("1", "true", "yes", "si")


def _client():
    try:
        import httpx
    except ImportError as e:  # pragma: no cover
        raise RuntimeError("httpx no está instalado") from e
    return httpx


class MLProductsAdapter(IMercadoLibreClient):

    def __init__(self, supabase: Optional[Client] = None):
        self.supabase = supabase

    async def search_products(self, query: str, vehicle_context: dict, limit: int = 5) -> List[dict]:
        if not _enabled():
            return []
        q = (query or "").strip()
        if not q:
            return []
        cache_key = self._cache_key(q, vehicle_context or {})
        cached = self._read_cache(cache_key)
        if cached is not None:
            return cached
        httpx = _client()
        terms = f"{q} {(vehicle_context or {}).get('brand', '')}".strip()
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(
                    _ML_SEARCH,
                    params={"site_id": _ML_SITE, "status": "active",
                            "q": terms, "limit": str(min(limit, 10))},
                    headers={"Accept": "application/json"},
                )
                if res.status_code != 200:
                    return []
                data = res.json()
        except Exception:
            return []
        items: List[dict] = []
        for row in (data or {}).get("results", [])[:limit]:
            attrs = {a.get("id"): (a.get("value_name") or a.get("value_id") or "")
                     for a in (row.get("attributes") or [])}
            oem = attrs.get("PART_NUMBER") or attrs.get("OEM") or None
            pictures = row.get("thumbnail") or (row.get("pictures") or [{}])[0].get("url")
            items.append({
                "title": row.get("name", ""),
                "image_url": pictures,
                "oem": (oem or "").strip() or None,
                "price": row.get("price"),
                "currency": row.get("currency_id"),
                "permalink": row.get("permalink"),
            })
        self._write_cache(cache_key, q, vehicle_context or {}, items)
        return items

    async def extract_oem_numbers(self, items: List[dict]) -> List[str]:
        seen, out = set(), []
        for it in items:
            oem = (it.get("oem") or "").strip()
            if oem and oem.lower() not in seen:
                seen.add(oem.lower())
                out.append(oem)
        return out

    # ── caché ─────────────────────────────────────────────────────────
    def _cache_key(self, query: str, vehicle_context: dict) -> str:
        payload = json.dumps({"q": query.lower(), **(vehicle_context or {})}, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _read_cache(self, key: str) -> Optional[List[dict]]:
        if self.supabase is None:
            return None
        try:
            res = self.supabase.table("ml_query_cache").select("*").eq("cache_key", key).maybe_single().execute()
            row = res.data if res and res.data else None
            if not row:
                return None
            if datetime.fromisoformat(row["expires_at"]) < datetime.now(timezone.utc):
                return None
            # incrementa hits (best-effort)
            self.supabase.table("ml_query_cache").update({"hits": (row.get("hits") or 0) + 1}) \
                .eq("id", row["id"]).execute()
            return list(row.get("response") or [])
        except Exception:
            return None

    def _write_cache(self, key: str, query: str, vehicle_context: dict, items: List[dict]) -> None:
        if self.supabase is None:
            return
        try:
            self.supabase.table("ml_query_cache").upsert({
                "cache_key": key,
                "query": query,
                "vehicle_context": vehicle_context,
                "response": items,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": (datetime.now(timezone.utc) + timedelta(days=_CACHE_TTL_DAYS)).isoformat(),
            }, on_conflict="cache_key").execute()
        except Exception:
            pass  # la caché nunca rompe la búsqueda
