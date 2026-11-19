import os
os.environ.setdefault("EXIGIR_JWT", "true")
from fastapi.testclient import TestClient
from src.main import app
from src.features.catalog.infrastructure.adapters.local_vin_decoder import LocalVinDecoder

cliente = TestClient(app)
print("health:", cliente.get("/health").status_code, cliente.get("/health").json()["status"])
print("catalog/:", cliente.get("/api/v1/catalog/").status_code)            # 401 esperado
print("taxonomy:", cliente.get("/api/v1/catalog/taxonomy").status_code)    # 401 esperado
print("decode:", cliente.get("/api/v1/catalog/decode", params={"vin": "WVWZZZ3CZ6P108422", "engine_number": "CFZ"}).status_code)  # 401 esperado
print("search:", cliente.get("/api/v1/catalog/search", params={"q": "pastillas"}).status_code)  # 401 esperado

# Decodificador local (sin red ni DB)
spec = LocalVinDecoder().decode_vin("WVWZZZ3CZ6P108422", "CFZ")
print("decode local ->", spec.brand, spec.year, spec.wmi, spec.engine.label, spec.fuel)
