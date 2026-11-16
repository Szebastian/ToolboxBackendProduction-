"""Rate limiting simple en memoria (ventana deslizante por IP).

Suficiente para frenar abuso de los endpoints públicos costosos
(creación de cuentas, visión IA, uploads). En un deploy con varias
instancias convendría moverlo a Redis, pero para una sola instancia
en Render es el costo/beneficio correcto.
"""
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

_VENTANA_SEG = 3600  # 1 hora
_registros: dict[str, deque] = defaultdict(deque)


def limitar(request: Request, maximo: int) -> None:
    """Lanza 429 si la IP superó `maximo` llamadas en la última hora."""
    ip = request.client.host if request.client else "desconocida"
    if request.headers.get("x-forwarded-for"):
        ip = request.headers["x-forwarded-for"].split(",")[0].strip()

    ahora = time.monotonic()
    ventana = _registros[ip]
    while ventana and ahora - ventana[0] > _VENTANA_SEG:
        ventana.popleft()
    if len(ventana) >= maximo:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos. Probá de nuevo en un rato.",
        )
    ventana.append(ahora)
