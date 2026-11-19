"""Verificación READ-ONLY de las migraciones 06 y 07 (sin escrituras)."""
from src.shared_kernel.infrastructure.database.supabase_client import get_supabase_admin_client

s = get_supabase_admin_client()

for tabla in ("part_categories", "part_subcategories", "ml_query_cache", "oem_part_numbers"):
    res = s.table(tabla).select("id", count="exact").limit(1).execute()
    print(f"{tabla}: count≈{getattr(res, 'count', 'n/d')}")

cats = s.table("part_categories").select("name", count="exact").order("sort_order").execute()
print("categorias:", [r["name"] for r in cats.data], "→ total:", len(cats.data))

subs = s.table("part_subcategories").select("id", count="exact").execute()
print("subcategorias:", subs.count)

subinc = s.table("part_subcategories").select("name, position_required").eq("position_required", True).execute()
print("posicionales:", [r["name"] for r in subinc.data])

try:
    v = s.table("vehicles").select("engine_number").limit(1).execute()
    print("vehicles.engine_number existe:", True)
except Exception as e:
    print("vehicles.engine_number NO existe:", e)
