"""Verificación manual del decodificador (sin DB, sin red).

Corre: python scripts/verify_decoder.py
"""
from src.features.catalog.infrastructure.adapters.local_vin_decoder import LocalVinDecoder

decoder = LocalVinDecoder()

casos = [
    ("WVWZZZ3CZ6P108422", "CFZ"),    # Passat 2.0 TDI (Brasil) · motor CFZ
    ("8AWZZZ377CE064921", "K4M"),    # VW Argentina · motor K4M (nafta)
    ("8AJBA3CD8K0193844", "1GD"),    # Toyota Hilux · motor 1GD (diesel turbo)
    ("9BFZZZ3FHZ0012345", "BGD"),    # Ford/GM hybrid probe (join fallback)
    ("VF1K8P1A100000001", "M9R"),    # Renault · motor M9R (diesel)
    ("",                 ""),        # vacío: no debe lanzar excepción
]

for vin, engine in casos:
    spec = decoder.decode_vin(vin, engine or None)
    print(f"VIN={vin or '(vacío)':<20} motor={engine or '-':<6} -> "
          f"{spec.brand} {spec.year or '-'} wmi={spec.wmi} "
          f"engine={spec.engine.label} fuel={spec.fuel}")

# decode_engine aislado
for en in ["H4M bS32Q1", "1KD-bt", "XYZ99", ""]:
    print(f"engine_number={en!r:<12} -> {decoder.decode_engine(en)}")
