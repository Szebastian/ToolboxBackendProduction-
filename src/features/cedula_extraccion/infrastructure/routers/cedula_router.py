import asyncio
import base64
import json
import os
import re

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from dotenv import load_dotenv

from src.shared_kernel.infrastructure.security.rate_limit import limitar

load_dotenv()

router = APIRouter(prefix="/cedulas", tags=["Cédulas"])

MAX_BYTES = 8 * 1024 * 1024  # 8 MB
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}

# Modelos de visión gratuitos en OpenRouter (se prueban en orden ante 429/falla)
MODELOS = [
    "nvidia/nemotron-3.5-super-vl:free",   # VL de razonamiento (requiere max_tokens alto)
    "google/gemma-4-31b-it:free",          # respaldo no-reasoning
    "google/gemma-4-26b-a4b-it:free",      # variante más chica
    "inclusionai/ling-3.2-flash:free",     # multimodal flash
    "particle-ai/particle-1:free",         # multimodal
    "thinkingmachines/inkling-2-small:free",
    "dots-studio/dots-3-note-preview:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
]
MAX_TOKENS = 1500
TIMEOUT_SEG = 60   # techo total de la carrera (por si todo está lento)
GRACE_SEG = 22     # si el primer resultado es flojo, esperamos esto por uno mejor

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
    """Carrera por calidad: consulta todos los modelos gratis a la vez.
    - Acepta enseguida el primer resultado completo (dominio+chasis+motor).
    - Si el primero es flojo, espera GRACE_SEG más por uno mejor y devuelve el
      de mayor puntaje (el chasis pesa doble). Los perdedores se cancelan."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENROUTER_API_KEY no configurada en el backend (.env).",
        )

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
        tareas = [asyncio.create_task(probar(m)) for m in MODELOS]
        resultados: list[dict] = []
        try:
            pendientes = set(tareas)
            while pendientes:
                restante = TIMEOUT_SEG - (asyncio.get_running_loop().time() - inicio)
                if restante <= 0:
                    break
                hecho, pendientes = await asyncio.wait(
                    pendientes, timeout=restante, return_when=asyncio.FIRST_COMPLETED
                )
                for t in hecho:
                    if t.result():
                        resultados.append(t.result())
                if not resultados:
                    continue
                mejor = max(resultados, key=lambda r: _puntaje(r["datos"]))
                if _es_completo(mejor["datos"]):
                    return mejor
                # Resultado flojo: damos una gracia breve por uno mejor y, si no
                # llega, devolvemos lo mejor recolectado (no esperamos los 60 s).
                if asyncio.get_running_loop().time() - inicio >= GRACE_SEG:
                    return mejor
        finally:
            # Cancelar el resto para no dejar pedidos colgados
            for t in tareas:
                t.cancel()

    if resultados:
        return max(resultados, key=lambda r: _puntaje(r["datos"]))
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"No se pudo extraer la cédula con ningún modelo. Detalles: {'; '.join(errores) or 'sin respuesta'}",
    )


@router.post("/extraer")
async def extraer_cedula(request: Request, file: UploadFile = File(...)):
    """Recibe la foto de la Cédula Verde y devuelve los datos técnicos extraídos por visión (OpenRouter)."""
    limitar(request, maximo=10)  # máx 10 extracciones IA por IP por hora (protege la cuota de OpenRouter)
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
    resultado = await _llamar_openrouter(b64, file.content_type or "image/jpeg")
    datos = resultado["datos"]

    # Normalización: campos faltantes → None; chasis se valida aparte
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
        "meta": {"modelo_ia": resultado["modelo"]},
    }
