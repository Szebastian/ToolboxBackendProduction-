from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EngineFamily(str, Enum):
    NAFTA = "nafta"
    DIESEL = "diesel"
    TURBO = "turbo"
    ASPIRADO = "aspirado"
    UNKNOWN = "unknown"


class TimingType(str, Enum):
    CORREA = "correa"
    CADENA = "cadena"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class EngineInfo:
    prefix: str
    family: EngineFamily
    timing: TimingType
    aspiration: str  # 'aspirado' | 'turbo' | 'unknown'
    displacement_cc: Optional[int]
    label: str  # etiqueta legible: "2.0 TDI 140 CV · Diesel · Correa"

    def matches(self, family: str) -> bool:
        return self.family.value == family.lower()


@dataclass(frozen=True)
class VehicleSpec:
    vin: str
    brand: str
    model: Optional[str]
    year: Optional[int]
    wmi: str                  # 3 primeros caracteres del VIN
    engine_prefix: Optional[str]
    engine: EngineInfo
    fuel: str                 # 'nafta' | 'diesel' | 'unknown'

    @property
    def family(self) -> str:
        return self.engine.family.value
