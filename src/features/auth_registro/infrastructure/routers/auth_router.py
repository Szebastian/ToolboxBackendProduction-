import re

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from src.shared_kernel.infrastructure.database.supabase_client import get_supabase_admin_client
from src.shared_kernel.infrastructure.security.rate_limit import limitar

router = APIRouter(prefix="/auth", tags=["Auth"])

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _capitalizar(texto: str) -> str:
    """'preston' → 'Preston'. Respeta las palabras que ya están bien escritas
    (O'Connor, McDonald, Martínez) y las minúsculas conectivas típicas."""
    conectivas = {"de", "del", "la", "las", "los", "y", "e", "van", "von", "di", "da"}

    def cap(palabra: str) -> str:
        if not palabra:
            return palabra
        restante = palabra[1:]
        # Ya tiene mayúsculas internas (O'Connor, Martínez) → se deja como vino
        if any(c.isupper() for c in restante):
            return palabra
        return palabra[0].upper() + restante

    palabras = texto.strip().split()
    for i, p in enumerate(palabras):
        palabras[i] = cap(p) if p.lower() not in conectivas or i == 0 else p.lower()
    return " ".join(palabras)


class VehiculoRegistroDTO(BaseModel):
    """Datos de la Cédula Verde extraídos por visión (opcionales)."""
    dominio: str | None = None
    marca: str | None = None
    modelo: str | None = None
    modelo_detalle: str | None = None
    tipo_carroceria: str | None = None
    chasis: str | None = None
    motor_codigo: str | None = None


class RegistroDTO(BaseModel):
    email: str
    password: str = Field(min_length=6)
    nombre: str = Field(min_length=1)
    apellido: str = Field(min_length=1)
    whatsapp: str | None = None
    vehiculo: VehiculoRegistroDTO | None = None

    @classmethod
    def validar_email(cls, email: str) -> bool:
        return bool(_EMAIL_RE.match(email))


@router.post("/registro", status_code=status.HTTP_201_CREATED)
async def registrar_usuario(payload: RegistroDTO, request: Request):
    """Alta real del nuevo usuario: auth.users + profiles (+ vehículo de la cédula si vino).

    Usa service_role (backend confiable). El email queda confirmado para que el
    usuario pueda iniciar sesión sin verificar (demo).
    """
    limitar(request, maximo=5)  # máx 5 cuentas por IP por hora
    supabase = get_supabase_admin_client()

    if not RegistroDTO.validar_email(payload.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email inválido.")

    nombre_cap = _capitalizar(payload.nombre)
    apellido_cap = _capitalizar(payload.apellido)
    nombre_completo = f"{nombre_cap} {apellido_cap}".strip()

    # 1) Crear usuario en Supabase Auth
    try:
        creado = supabase.auth.admin.create_user({
            "email": payload.email,
            "password": payload.password,
            "email_confirm": True,
            "user_metadata": {
                "nombre": nombre_cap,
                "apellido": apellido_cap,
                "whatsapp": payload.whatsapp,
            },
        })
    except Exception as e:
        detalle = str(e)
        if "already registered" in detalle or "already been registered" in detalle:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ese email ya tiene una cuenta creada.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"No se pudo crear el usuario: {detalle}")

    uid = creado.user.id

    # 2) Perfil en public.profiles. El trigger handle_new_user ya inserta la fila
    # al crear el usuario de Auth, así que usamos upsert para completar/corregir
    # los datos (idempotente, sin choque de clave primaria).
    try:
        supabase.table("profiles").upsert({
            "id": uid,
            "email": payload.email,
            "full_name": nombre_completo,
            "phone": payload.whatsapp,
            "role": "customer",
        }).execute()
    except Exception as e:
        # El usuario de auth quedó creado; informamos para no duplicar en reintentos
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Usuario creado en Auth ({uid}) pero falló el perfil: {e}",
        )

    # 3) Vehículo desde la Cédula Verde (si se pudieron leer los datos mínimos)
    vehiculo_creado = None
    v = payload.vehiculo
    if v and v.dominio and v.marca and v.modelo:
        # Año desde modelo_detalle ("Generación B6 (Año 2006)") o default 2010
        anio = None
        if v.modelo_detalle:
            m = re.search(r"(19|20)\d{2}", v.modelo_detalle)
            anio = int(m.group(0)) if m else None
        datos_vehiculo = {
            "owner_id": uid,
            "license_plate": v.dominio[:12],
            "vin": (v.chasis or None),
            "brand": v.marca[:60],
            "model": f"{v.modelo}{' · ' + v.tipo_carroceria if v.tipo_carroceria else ''}"[:60],
            "year": anio or 2010,
            "engine_details": (f"{v.motor_codigo} · {v.modelo_detalle}" if v.motor_codigo else v.modelo_detalle),
        }
        try:
            resp = supabase.table("vehicles").insert(datos_vehiculo).execute()
            vehiculo_creado = resp.data[0] if resp.data else None
        except Exception as e:
            # No bloquea la cuenta: el auto se puede agregar después desde el panel
            vehiculo_creado = {"error": f"El vehículo no se pudo guardar: {e}"}

    return {
        "success": True,
        "data": {
            "id": uid,
            "email": payload.email,
            "full_name": nombre_completo,
            "phone": payload.whatsapp,
            "vehiculo": vehiculo_creado,
        },
    }
