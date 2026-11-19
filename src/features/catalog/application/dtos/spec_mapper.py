from src.features.catalog.domain.vehicle_spec import VehicleSpec


def to_public_dict(spec: VehicleSpec) -> dict:
    e = spec.engine
    return {
        "vin": spec.vin,
        "brand": spec.brand,
        "model": spec.model,
        "year": spec.year,
        "engine": {
            "prefix": e.prefix,
            "family": e.family.value,
            "timing": e.timing.value,
            "aspiration": e.aspiration,
            "label": e.label,
            "displacement_cc": e.displacement_cc,
        },
        "fuel": spec.fuel,
    }
