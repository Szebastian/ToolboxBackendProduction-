import asyncio
import base64
import hashlib
import json
import os
import re
import time as _time

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from dotenv import load_dotenv

from src.shared_kernel.infrastructure.security.rate_limit import limitar

load_dotenv()

router = APIRouter(prefix="/cedulas", tags=["Cédulas"])

MAX_BYTES = 8 * 1024 * 1024  # 8 MB
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}

# Modelos de visión gratuitos en OpenRouter, lanzados por olas para cuidar la
# cuota free (cada pedido cuenta contra el tope diario de la cuenta).
# Ola 1 = los 2 con mejor historial: si uno lee completo, no se gastan más.
OLEADAS = [
    ["nvidia/nemotron-3.5-super-vl:free", "particle-ai/particle-1:free"],
    ["inclusionai/ling-3.2-flash:free", "google/gemma-4-31b-it:free"],
    ["google/gemma-4-26b-a4b-it:free", "dots-studio/dots-3-note-preview:free"],
    ["thinkingmachines/inkling-2-small:free", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"],
]
MAX_TOKENS = 1500
TIMEOUT_SEG = 60   # techo total de la carrera (por si todo está lento)
GRACE_SEG = 22     # si el primer resultado es flojo, esperamos esto por uno mejor
CACHE_TTL_SEG = 900  # reintentos con la misma foto dentro de 15 min no queman cuota

# Respaldo pago: cuando toda la cuota free está agotada, se usa este modelo
# (barato, ~USD 0.001-0.004 por extracción). Se activa definiendo en .env:
#   OPENROUTER_FALLBACK_PAGO=google/gemini-2.0-flash-001
MODELO_FALLBACK_PAGO = os.getenv("OPENROUTER_FALLBACK_PAGO", "").strip()

_cache: dict[str, tuple[float, dict]] = {}

PROMPT = (
    "Sos un lector de Cédulas Verdes (DNRPA Argentina). Mirá la foto y extraé EXACTAMENTE estos campos:\n"
    "- dominio: patente (formato viejo AAA 123 o nuevo AA 123 BB)\n"
    "- marca: marca del vehículo en mayúsculas\n"
    "- modelo: modelo completo (ej: PASSAT 2.0 TDI HIGHLINE)\n"
    "- modelo_detalle: generación/año si se lee (ej: Generación B6 (Año 2006))\n"
    "- tipo_carroceria: ej: SEDÁN 4 PUERTAS\n"
    "- chasis: número de chasis VIN de 17 caracteres alfanuméricos (sin I, O, Q)\n"
    "- motor_codigo: código y número de motor (ej: BKP-104928)\n"
    "- motor_specs: especificaciones si se leen (ej: 16 Válvulas · 140 CV)\n"
    "- compat: array de hasta 3 compatibilidades técnicas que deduzcas de la marca/modelo/motor "
    "(ej: 'Frenos: Discos 312mm', 'Caja: Manual 6ta', 'Inyección: Siemens PPD'); si no podés deducir, array vacío\n"
    "Reglas: si un campo NO se lee claramente en la foto, poné null (no inventes datos). "
    "Respondé ÚNICAMENTE un objeto JSON válido, sin markdown ni explicaciones."
)


def _parsear_json(texto: str) -> dict:
    """Extrae el primer objeto JSON del contenido del modelo (tolera markdown)."""
    texto = texto.strip()
    m = re.search(r"\{.*\}", texto, re.DOTALL)
    if m:
        texto = m.group(0)
    return json.loads(texto)


def _puntaje(datos: dict) -> int:
    """Cantidad de campos clave leídos (el chasis vale doble: es el más importante)."""
    claves = ["dominio", "marca", "modelo", "modelo_detalle", "tipo_carroceria", "motor_codigo"]
    base = sum(1 for k in claves if datos.get(k))
    return base + (2 if datos.get("chasis") else 0)


def _es_completo(datos: dict) -> bool:
    """Resultado confiable: leyó los 3 datos que el usuario no puede adivinar."""
    return all(datos.get(k) for k in ("dominio", "chasis", "motor_codigo"))


async def _llamar_openrouter(b64: str, mime: str) -> dict:
    """Carrera por calidad en olas: consulta pocos modelos a la vez.

    - Ola 1 (los 2 más confiables): si uno lee completo (dominio+chasis+motor),
      se responde al instante — la extracción típica gasta solo 2 pedidos.
    - Si el mejor es flojo, se lanza la ola siguiente y gana el de mayor
      puntaje (chasis pesa doble). Techo TIMEOUT_SEG.
    - Cache por hash de imagen: reintentos con la misma foto no queman cuota.
    - Si toda la ola vuelve 429 (cuota free agotada), corta con mensaje claro
      en lugar de gastar el resto de las olas en errores."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENROUTER_API_KEY no configurada en el backend (.env).",
        )

    import hashlib
    import time as _time

    clave = hashlib.sha256(b64.encode("ascii")).hexdigest()
    hit = _cache.get(clave)
    if hit and (_time.monotonic() - hit[0]) < CACHE_TTL_SEG:
        return hit[1]

    url_imagen = f"data:{mime};base64,{b64}"
    errores: list[str] = []

    async with httpx.AsyncClient(timeout=TIMEOUT_SEG) as client:

        async def probar(modelo: str) -> dict | None:
            payload = {
                "model": modelo,
                "max_tokens": MAX_TOKENS,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": PROMPT},
                            {"type": "image_url", "image_url": {"url": url_imagen}},
                        ],
                    }
                ],
            }
            try:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json=payload,
                )
                if resp.status_code == 429:
                    errores.append(f"{modelo}: 429 (límite del tier gratis)")
                    return None
                resp.raise_for_status()
                mensaje = resp.json()["choices"][0]["message"]
                contenido = mensaje.get("content") or ""
                # Los modelos de razonamiento a veces devuelven contenido vacío
                if not contenido.strip():
                    errores.append(f"{modelo}: respuesta vacía")
                    return None
                datos = _parsear_json(contenido)
                return {"modelo": modelo, "datos": datos}
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                errores.append(f"{modelo}: respuesta inesperada ({e})")
                return None
            except httpx.HTTPStatusError as e:
                errores.append(f"{modelo}: HTTP {e.response.status_code}")
                return None
            except httpx.HTTPError as e:
                errores.append(f"{modelo}: {e}")
                return None

        inicio = asyncio.get_running_loop().time()
        resultados: list[dict] = []
        probados: set[str] = set()
        tareas_todas: list[asyncio.Task] = []
        try:
            for ola in OLEADAS:
                restante = TIMEOUT_SEG - (asyncio.get_running_loop().time() - inicio)
                if restante <= 0:
                    break
                nuevos = [m for m in ola if m not in probados]
                if not nuevos:
                    continue
                probados.update(nuevos)
                tareas = [asyncio.create_task(probar(m)) for m in nuevos]
                tareas_todas.extend(tareas)
                pendientes = set(tareas)
                while pendientes:
                    restante = TIMEOUT_SEG - (asyncio.get_running_loop().time() - inicio)
                    if restante <= 0:
                        break
                    hecho, pendientes = await asyncio.wait(
                        pendientes, timeout=max(restante, 0.1), return_when=asyncio.FIRST_COMPLETED
                    )
                    for t in hecho:
                        if t.result():
                            resultados.append(t.result())
                    if resultados:
                        mejor = max(resultados, key=lambda r: _puntaje(r["datos"]))
                        if _es_completo(mejor["datos"]):
                            _cache[clave] = (_time.monotonic(), mejor)
                            return mejor
                # Ola completa sin lectura completa:
                if resultados:
                    mejor = max(resultados, key=lambda r: _puntaje(r["datos"]))
                    if asyncio.get_running_loop().time() - inicio >= GRACE_SEG:
                        _cache[clave] = (_time.monotonic(), mejor)
                        return mejor
                # ¿Toda la ola fue 429? La cuota free está agotada: probar el
                # respaldo pago si está configurado, o cortar con mensaje claro.
                fallas_ola = [e for e in errores if any(m in e for m in nuevos)]
                if fallas_ola and all("429" in f for f in fallas_ola):
                    if not MODELO_FALLBACK_PAGO:
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail=(
                                "El límite gratuito de OpenRouter está agotado para hoy "
                                "(se renueva a medianoche UTC, ~21:00 en Argentina). "
                                "Alternativa: cargar USD 10 de crédito en OpenRouter "
                                "eleva el tope a 1000 extracciones por día."
                            ),
                        )
                    pago = await probar(MODELO_FALLBACK_PAGO)
                    if pago:
                        _cache[clave] = (_time.monotonic(), pago)
                        return pago
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=(
                            "Cuota gratuita de OpenRouter agotada y el modelo de respaldo "
                            f"también falló ({'; '.join(errores[-1:])}). Verificá el crédito "
                            "cargado en OpenRouter."
                        ),
                    )
        finally:
            # Cancelar el resto para no dejar pedidos colgados
            for t in tareas_todas:
                t.cancel()

    if resultados:
        mejor = max(resultados, key=lambda r: _puntaje(r["datos"]))
        _cache[clave] = (_time.monotonic(), mejor)
        return mejor
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"No se pudo extraer la cédula con ningún modelo. Detalles: {'; '.join(errores) or 'sin respuesta'}",
    )


@router.post("/extraer")
async def extraer_cedula(request: Request, file: UploadFile = File(...)):
    """Recibe la foto de la Cédula Verde y devuelve los datos técnicos extraídos.

    Estrategia gratuita: primero OCR local (RapidOCR, sin cuota ni límites);
    si no lee dominio+chasis+motor, completa con la carrera de visión de
    OpenRouter (olas de modelos free)."""
    limitar(request, maximo=10)  # máx 10 extracciones por IP por hora (protege la cuota free)
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato no permitido ({file.content_type}). Usá JPG, PNG, WEBP o HEIC.",
        )

    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La imagen supera los 8 MB.")
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El archivo está vacío.")

    b64 = base64.b64encode(data).decode("ascii")

    # 1) OCR local: gratis e ilimitado
    from src.features.cedula_extraccion.infrastructure.ocr_cedula import extraer_datos_ocr
    datos = extraer_datos_ocr(data)
    modelo_ia = "OCR local (RapidOCR)"

    # 2) Si el OCR no leyó completo, completa con la carrera de visión
    if not _es_completo(datos):
        try:
            resultado = await _llamar_openrouter(b64, file.content_type or "image/jpeg")
            ia = resultado["datos"]
            for k, v in ia.items():
                if v and not datos.get(k):
                    datos[k] = v
            modelo_ia = resultado["modelo"]
        except HTTPException:
            # Cuota de visión agotada: devolvemos lo que pudo leer el OCR
            # (el usuario completa los faltantes a mano en el formulario)
            pass

    chasis = (datos.get("chasis") or "").strip().upper() or None
    advertencias: list[str] = []
    if chasis and (len(chasis) != 17 or not re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", chasis)):
        advertencias.append(f"El chasis leído ({chasis}) no tiene el formato VIN de 17 dígitos — verificá manualmente.")

    return {
        "success": True,
        "data": {
            "dominio": datos.get("dominio"),
            "marca": datos.get("marca"),
            "modelo": datos.get("modelo"),
            "modelo_detalle": datos.get("modelo_detalle"),
            "tipo_carroceria": datos.get("tipo_carroceria"),
            "chasis": chasis,
            "motor_codigo": datos.get("motor_codigo"),
            "motor_specs": datos.get("motor_specs"),
            "compat": datos.get("compat") or [],
        },
        "warnings": advertencias,
        "meta": {"modelo_ia": modelo_ia},
    }
