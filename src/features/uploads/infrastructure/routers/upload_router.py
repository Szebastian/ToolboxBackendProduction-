import uuid
from fastapi import Depends, APIRouter, HTTPException, UploadFile, File, status
from src.shared_kernel.infrastructure.security.auth_dependency import usuario_actual
from src.shared_kernel.infrastructure.database.supabase_client import get_supabase_admin_client

router = APIRouter(
    dependencies=[Depends(usuario_actual)],prefix="/uploads", tags=["Uploads"])

BUCKET = "part-photos"
MAX_BYTES = 8 * 1024 * 1024  # 8 MB
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/heic", "image/heif"}


@router.post("/photo", status_code=status.HTTP_201_CREATED)
async def upload_photo(file: UploadFile = File(...)):
    """Sube una foto a Supabase Storage y devuelve su URL pública.

    Se usa tanto para la foto del comprador (pieza a cambiar) como para la
    foto de confirmación del vendedor (repuesto real, que alimenta el catálogo).
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato no permitido ({file.content_type}). Usá JPG, PNG, WEBP o GIF."
        )

    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La imagen supera los 8 MB.")

    # Nombre único en el bucket, conservando la extensión original
    ext = (file.filename or "foto.jpg").rsplit(".", 1)[-1].lower()[:5] or "jpg"
    path = f"{uuid.uuid4().hex}.{ext}"

    try:
        supabase = get_supabase_admin_client()
        supabase.storage.from_(BUCKET).upload(path, data, {"content-type": file.content_type, "upsert": "false"})
        url = supabase.storage.from_(BUCKET).get_public_url(path)
        return {"success": True, "data": {"url": url, "path": path}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
