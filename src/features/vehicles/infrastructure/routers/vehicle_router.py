from fastapi import Depends, APIRouter, HTTPException, status
from src.shared_kernel.infrastructure.security.auth_dependency import usuario_actual
from src.features.vehicles.application.register_vehicle_use_case import RegisterVehicleInputDTO, RegisterVehicleUseCase
from src.features.vehicles.infrastructure.adapters.supabase_vehicle_repository import SupabaseVehicleRepository
from src.shared_kernel.infrastructure.database.supabase_client import get_supabase_admin_client

router = APIRouter(
    dependencies=[Depends(usuario_actual)],prefix="/vehicles", tags=["Vehicles"])

def get_vehicle_repo() -> SupabaseVehicleRepository:
    supabase = get_supabase_admin_client()
    return SupabaseVehicleRepository(supabase)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def register_vehicle(payload: RegisterVehicleInputDTO):
    try:
        repo = get_vehicle_repo()
        use_case = RegisterVehicleUseCase(repo)
        vehicle = await use_case.execute(payload)
        return {"success": True, "data": vehicle}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/owner/{owner_id}")
async def list_by_owner(owner_id: str):
    try:
        repo = get_vehicle_repo()
        vehicles = await repo.find_by_owner_id(owner_id)
        return {"success": True, "data": vehicles}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
