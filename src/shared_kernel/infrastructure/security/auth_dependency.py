"""Verificación del JWT de Supabase para los endpoints del backend.

El frontend (interceptor Angular) envía `Authorization: Bearer <access_token>`
con la sesión activa de Supabase. Este dependency valida ese token contra
Supabase Auth y expone el usuario al handler.

Modo demo: EXIGIR_JWT=false (default) → los paneles demo (sin contraseña)
siguen funcionando; si viene un token se valida igual. En producción se
publica EXIGIR_JWT=true y todo endpoint protegido responde 401 sin token.
"""
import os

from fastapi import Header, HTTPException, status

from src.shared_kernel.infrastructure.database.supabase_client import get_supabase_admin_client


def _exigir() -> bool:
    return os.getenv("EXIGIR_JWT", "false").strip().lower() in ("1", "true", "yes", "si")


def usuario_actual(authorization: str | None = Header(default=None)) -> dict:
    """Dependencia FastAPI: devuelve {'id', 'email'} del dueño del JWT.

    - Token válido → datos reales del usuario.
    - Sin token / inválido con EXIGIR_JWT=true → 401.
    - Sin token con EXIGIR_JWT=false → {'id': None, 'email': None} (anónimo demo).
    """
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()

    if token:
        try:
            res = get_supabase_admin_client().auth.get_user(token)
            u = getattr(res, "user", None)
            if u is not None:
                return {"id": u.id, "email": u.email}
        except Exception:
            pass
        if _exigir():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado. Iniciá sesión de nuevo.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"id": None, "email": None}

    if _exigir():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el token de sesión.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"id": None, "email": None}
