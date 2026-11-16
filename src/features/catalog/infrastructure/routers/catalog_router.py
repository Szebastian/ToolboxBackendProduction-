from fastapi import Depends, APIRouter, HTTPException, status
from src.shared_kernel.infrastructure.security.auth_dependency import usuario_actual
from src.features.catalog.infrastructure.adapters.supabase_catalog_repository import SupabaseCatalogRepository
from src.shared_kernel.infrastructure.database.supabase_client import get_supabase_admin_client

router = APIRouter(
    dependencies=[Depends(usuario_actual)],prefix="/catalog", tags=["Catalog"])


def get_catalog_repo() -> SupabaseCatalogRepository:
    supabase = get_supabase_admin_client()
    return SupabaseCatalogRepository(supabase)


@router.get("/")
async def search_catalog(q: str = "", limit: int = 50):
    """Busca repuestos del catálogo (alimentado por las fotos de los vendedores)."""
    try:
        repo = get_catalog_repo()
        parts = await repo.search(q, limit)
        return {"success": True, "data": parts}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
