from fastapi import APIRouter, HTTPException, status
from src.features.parts_request.application.create_parts_request_use_case import CreatePartsRequestInputDTO, CreatePartsRequestUseCase
from src.features.parts_request.infrastructure.adapters.supabase_parts_request_repository import SupabasePartsRequestRepository
from src.shared_kernel.infrastructure.database.supabase_client import get_supabase_admin_client

router = APIRouter(prefix="/parts-requests", tags=["Parts Requests"])

def get_parts_request_repo() -> SupabasePartsRequestRepository:
    supabase = get_supabase_admin_client()
    return SupabasePartsRequestRepository(supabase)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_request(payload: CreatePartsRequestInputDTO):
    try:
        repo = get_parts_request_repo()
        use_case = CreatePartsRequestUseCase(repo)
        request = await use_case.execute(payload)
        return {"success": True, "data": request}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/open")
async def list_open_requests():
    try:
        repo = get_parts_request_repo()
        requests = await repo.list_open_for_quoting()
        return {"success": True, "data": requests}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{request_id}")
async def get_request_by_id(request_id: str):
    try:
        repo = get_parts_request_repo()
        request = await repo.find_by_id(request_id)
        if not request:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada")
        return {"success": True, "data": request}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
