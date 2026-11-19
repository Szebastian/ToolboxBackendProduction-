from src.features.catalog.domain.ports.vehicle_decoder_port import IVehicleDecoder
from src.features.catalog.infrastructure.adapters.vehicle_cache_adapter import VehicleCacheAdapter
from src.features.catalog.application.dtos.spec_mapper import to_public_dict
from src.features.catalog.application.dtos.catalog_dtos import DecodeVehicleInput


class DecodeVehicleUseCase:
    """Decode cache-first: consulta vehicle_cache, y solo si falta decodifica."""

    def __init__(self, decoder: IVehicleDecoder, cache: VehicleCacheAdapter):
        self.decoder = decoder
        self.cache = cache

    async def execute(self, dto: DecodeVehicleInput) -> dict:
        cached = await self.cache.find_by_vin(dto.vin) if dto.vin else None
        if cached and cached.get("engine"):
            return {
                "vin": cached["vin"],
                "brand": cached.get("make"),
                "model": cached.get("model"),
                "year": cached.get("year"),
                "engine": {"label": cached.get("engine")},
                "source": "cache",
            }
        spec = self.decoder.decode_vin(dto.vin, dto.engine_number)
        raw = {"wmi": spec.wmi, "engine_prefix": spec.engine_prefix,
               "engine_label": spec.engine.label, "market_origin": "local_decoder"}
        await self.cache.save(spec, raw)
        out = to_public_dict(spec)
        out["source"] = "decoded"
        return out
