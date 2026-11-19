"""Prueba READ-ONLY: taxonomy con data real de Supabase."""
import os
os.environ.setdefault("EXIGIR_JWT", "false")  # local solo lectura; no valida writes
from fastapi.testclient import TestClient
from src.main import app

cliente = TestClient(app)
r = cliente.get("/api/v1/catalog/taxonomy")
print("status:", r.status_code)
data = r.json()
print("success:", data.get("success"))
cats = data.get("data", [])
print("categorias:", len(cats))
for c in cats[:4]:
    print(f" - {c['name']}: {len(c['subcategories'])} subcategorías; primera: {c['subcategories'][0]['name']}")
r2 = cliente.get("/api/v1/catalog/taxonomy", params={"engine_family": "diesel"})
d2 = r2.json()
diesel = d2.get("data", [])
print("diesel:", len(diesel), "categorías; Motor:", len(diesel[0]["subcategories"]) if diesel else 0, "subcategorías")
