"""OCR local para Cédulas Verdes (sin IA en la nube, sin cuota).

RapidOCR corre 100% en el servidor con CPU (onnxruntime). El parser deduce
los campos clave del documento con etiquetas y patrones tolerantes a los
errores típicos del OCR (O↔0, I↔1 en el chasis, MOT0R, etc.).

Los campos que el OCR no logra leer quedan en None y el router completa
con la carrera de visión de OpenRouter.
"""
import base64
import io
import re

# Marcas habituales de Argentina (para reconocer la línea de MARCA)
_MARCAS = [
    "MERCEDES-BENZ", "GREAT WALL", "VOLKSWAGEN", "CHEVROLET", "MITSUBISHI", "MERCEDES",
    "CITROEN", "RENAULT", "TOYOTA", "PEUGEOT", "HYUNDAI", "SUZUKI", "VOLVO", "NISSAN",
    "CHERY", "AUDI", "BMW", "FIAT", "FORD", "HONDA", "IVECO", "JAC", "JEEP", "KIA",
    "MAZDA", "SCANIA", "SEAT", "SUBARU", "RAM", "DACIA",
]

_ocr = None


def _get_ocr():
    global _ocr
    if _ocr is None:
        from rapidocr_onnxruntime import RapidOCR
        _ocr = RapidOCR()
    return _ocr


def _normalizar_vin(candidato: str) -> str | None:
    """Valida un VIN de 17. Si el OCR confundió I/O/Q, corrige y reintenta."""
    vin = re.sub(r"\s", "", candidato).upper()
    if re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", vin):
        return vin
    if re.fullmatch(r"[A-Z0-9]{17}", vin):
        corregido = vin.replace("O", "0").replace("Q", "0").replace("I", "1")
        if re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", corregido):
            return corregido
    return None


def _dominio_valido(txt: str) -> str | None:
    d = re.sub(r"\s+", " ", txt).strip().upper()
    if re.fullmatch(r"[A-Z]{3} \d{3}", d) or re.fullmatch(r"[A-Z]{2} \d{3} [A-Z]{2}", d):
        return d
    # sin espacios: AB412TX → AB 412 TX
    s = re.sub(r"\s", "", txt).upper()
    if re.fullmatch(r"[A-Z]{3}\d{3}", s):
        return f"{s[:3]} {s[3:]}"
    if re.fullmatch(r"[A-Z]{2}\d{3}[A-Z]{2}", s):
        return f"{s[:2]} {s[2:5]} {s[5:]}"
    return None


def _buscar_etiqueta(texto: str, etiqueta: str) -> str | None:
    """Valor después de una etiqueta tipo 'DOMINIO: XXX' (tolera 0/O/I en la etiqueta)."""
    m = re.search(
        rf"(?:{etiqueta})\s*[:.]?\s*([A-Z0-9][^\n]*)",
        texto,
        re.IGNORECASE,
    )
    return m.group(1).strip() if m else None


def extraer_datos_ocr(imagen_bytes: bytes) -> dict:
    """Lee la imagen con OCR local y devuelve los campos de la Cédula Verde.

    Devuelve el mismo formato que el prompt de visión: los campos que no se
    leen van en None para que la IA los complete."""
    vacio = {
        "dominio": None, "marca": None, "modelo": None, "modelo_detalle": None,
        "tipo_carroceria": None, "chasis": None, "motor_codigo": None,
        "motor_specs": None, "compat": [],
    }
    try:
        resultado, _ = _get_ocr()(imagen_bytes)
    except Exception:
        # img bytes no soportado en esta versión: decodificar con cv2
        try:
            import cv2
            import numpy as np
            arr = cv2.imdecode(np.frombuffer(imagen_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
            resultado, _ = _get_ocr()(arr)
        except Exception:
            return vacio
    if not resultado:
        return vacio

    lineas = [t.strip() for _, t, _ in resultado if t and t.strip()]
    texto = "\n".join(lineas)
    mayus = texto.upper()

    # ── Dominio ──
    dominio = None
    crudo = _buscar_etiqueta(mayus, r"DOMINIO|PATENTE")
    if crudo:
        m = re.match(r"([A-Z0-9][A-Z0-9 ]{2,10})", crudo)
        if m:
            dominio = _dominio_valido(m.group(1))
    if not dominio:
        m = re.search(r"\b[A-Z]{3} ?\d{3}\b|\b[A-Z]{2} ?\d{3} ?[A-Z]{2}\b", mayus)
        if m:
            dominio = _dominio_valido(m.group(0))

    # ── Chasis / VIN ──
    chasis = None
    crudo = _buscar_etiqueta(mayus, r"CHASIS|VIN|NRO\.?\s*MOTOR\s*DE\s*CHASIS")
    if crudo:
        chasis = _normalizar_vin(crudo)
    if not chasis:
        m = re.search(r"\b[A-Z0-9]{17}\b", mayus)
        if m:
            chasis = _normalizar_vin(m.group(0))

    # ── Motor ──
    motor = None
    crudo = _buscar_etiqueta(mayus, r"MO[T0]OR|NUMERO\s*DE\s*MOTOR|MOTOR\s*N")
    if crudo:
        m = re.match(r"\s*([A-Z]{3}\s?[-–]?\s?\d{3,7})", crudo.upper())
        if m:
            motor = re.sub(r"\s", "", m.group(1)).replace("–", "-")
            motor = re.sub(r"([A-Z]{3})(\d)", r"\1-\2", motor)
    if not motor:
        m = re.search(r"\b[A-Z]{3}[-–]?\d{3,7}\b", mayus)
        if m:
            motor = re.sub(r"\s", "", m.group(0)).replace("–", "-")

    # ── Marca ──
    marca = None
    crudo = _buscar_etiqueta(mayus, r"MARCA")
    if crudo:
        crudo = crudo.split("\n")[0].strip(" :.")
        for m in _MARCAS:
            if crudo.startswith(m) or m in crudo:
                marca = m
                break
        if not marca and re.fullmatch(r"[A-Z][A-Z \-]{2,}", crudo):
            marca = crudo.strip()
    if not marca:
        for m in _MARCAS:
            if m in mayus:
                marca = m
                break

    # ── Modelo ──
    modelo = None
    crudo = _buscar_etiqueta(mayus, r"MODELO")
    if crudo:
        modelo = crudo.split("\n")[0].strip(" :.")[:60] or None

    # El texto del dominio sin espacio a veces ensucia el resto: limpiar specs
    motor_specs = None
    ms = _buscar_etiqueta(mayus, r"CILINDRADA|POTENCIA")
    if ms:
        motor_specs = ms.split("\n")[0][:80]

    return {
        "dominio": dominio,
        "marca": marca,
        "modelo": modelo,
        "modelo_detalle": None,
        "tipo_carroceria": None,
        "chasis": chasis,
        "motor_codigo": motor,
        "motor_specs": motor_specs,
        "compat": [],
    }
