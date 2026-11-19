"""Decodificador local de VIN/motor Mercosur.

Sin red ni dependencias: funciona siempre, incluso offline. Nunca lanza
excepción; datos desconocidos devuelven spec con 'UNKNOWN' y el VIN intacto.
"""
import re
from src.features.catalog.domain.ports.vehicle_decoder_port import IVehicleDecoder
from src.features.catalog.domain.vehicle_spec import (
    EngineFamily,
    EngineInfo,
    TimingType,
    VehicleSpec,
)
from src.features.catalog.infrastructure.adapters.engine_prefix_map import ENGINE_PREFIX_MAP
from src.features.catalog.infrastructure.adapters.wmi_map import WMI_MAP, year_from_char

_UNKNOWN_ENGINE = EngineInfo(
    prefix="",
    family=EngineFamily.UNKNOWN,
    timing=TimingType.UNKNOWN,
    aspiration="unknown",
    displacement_cc=None,
    label="Motor a confirmar",
)


def _clean(vin: str) -> str:
    return re.sub(r'[^A-Z0-9]', '', (vin or '').upper())


def _engine_prefix(engine_number: str) -> str:
    raw = re.sub(r'[^A-Z0-9]', '', (engine_number or '').upper())
    if not raw:
        return ''
    # Preferimos el prefijo más largo conocido (1NZ-FE, etc.)
    for n in (6, 5, 4, 3):
        cand = raw[:n]
        if cand in ENGINE_PREFIX_MAP:
            return cand
    return raw[:3]


def _engine_from_prefix(prefix: str):
    hit = ENGINE_PREFIX_MAP.get(prefix)
    if not hit:
        return EngineInfo(
            prefix=prefix,
            family=EngineFamily.UNKNOWN,
            timing=TimingType.UNKNOWN,
            aspiration='unknown',
            displacement_cc=None,
            label=f"{prefix} · a confirmar",
        )
    cc, family, aspiration, timing, label = hit
    fam = EngineFamily(family) if family in ('nafta', 'diesel', 'turbo', 'aspirado') else EngineFamily.UNKNOWN
    return EngineInfo(
        prefix=prefix,
        family=fam,
        timing=TimingType(timing) if timing in ('correa', 'cadena') else TimingType.UNKNOWN,
        aspiration=aspiration,
        displacement_cc=cc,
        label=label,
    )


class LocalVinDecoder(IVehicleDecoder):

    def decode_engine(self, engine_number: str):
        prefix = _engine_prefix(engine_number)
        return prefix or None

    def decode_vin(self, vin: str, engine_number: str | None = None):
        v = _clean(vin)
        wmi = v[:3]
        year = year_from_char(v[9] if len(v) >= 10 else '')
        make_info = WMI_MAP.get(wmi)

        engine = _engine_from_prefix(_engine_prefix(engine_number)) if engine_number \
            else _UNKNOWN_ENGINE
        fuel = engine.family.value if engine.family in (EngineFamily.NAFTA, EngineFamily.DIESEL) else 'unknown'

        return VehicleSpec(
            vin=v,
            brand=(make_info[0] if make_info else 'DESCONOCIDA'),
            model=None,
            year=year,
            wmi=wmi,
            engine_prefix=engine.prefix or None,
            engine=engine,
            fuel=fuel,
        )
