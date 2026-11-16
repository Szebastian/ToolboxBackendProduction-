from fastapi import Depends, APIRouter, HTTPException, status
from src.shared_kernel.infrastructure.security.auth_dependency import usuario_actual
from src.features.mechanics.infrastructure.adapters.supabase_mechanic_repository import SupabaseMechanicRepository
from src.shared_kernel.infrastructure.database.supabase_client import get_supabase_admin_client

router = APIRouter(
    dependencies=[Depends(usuario_actual)],prefix="/mechanics", tags=["Mechanics"])


def get_mechanic_repo() -> SupabaseMechanicRepository:
    supabase = get_supabase_admin_client()
    return SupabaseMechanicRepository(supabase)


@router.get("/")
async def list_enabled_mechanics(limit: int = 50):
    """Lista los mecánicos habilitados de la red (perfiles con role='mechanic')."""
    try:
        repo = get_mechanic_repo()
        mechanics = await repo.list_enabled(limit)
        return {"success": True, "data": [m.to_dict() for m in mechanics]}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
