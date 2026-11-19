from abc import ABC, abstractmethod
from typing import Optional
from src.features.catalog.domain.vehicle_spec import VehicleSpec


class IVehicleDecoder(ABC):

    @abstractmethod
    def decode_vin(self, vin: str, engine_number: str | None = None) -> VehicleSpec:
        """Decodifica un VIN Mercosur (sin red). Nunca falla: ante datos
        desconocidos devuelve VehicleSpec con valores 'UNKNOWN' y el VIN intacto.
        Si se indica engine_number, también resuelve la familia del motor."""
        ...

    @abstractmethod
    def decode_engine(self, engine_number: str) -> Optional[str]:
        """Extrae el prefijo del número de motor (ej. CFZ, K4M, 1KD)."""
        ...
