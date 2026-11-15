import os
from fastapi import APIRouter, HTTPException, status
from src.features.delegation_tokens.application.dtos.delegation_dtos import DelegateRequestInputDTO
from src.features.delegation_tokens.application.delegate_request_to_mechanic_use_case import DelegateRequestToMechanicUseCase
from src.features.delegation_tokens.infrastructure.adapters.supabase_delegation_token_repository import SupabaseDelegationTokenRepository
from src.features.delegation_tokens.infrastructure.adapters.evolution_whatsapp_adapter import EvolutionWhatsAppAdapter
from src.shared_kernel.infrastructure.database.supabase_client import get_supabase_admin_client

router = APIRouter(prefix="/delegations", tags=["Delegation Tokens"])

def get_delegate_use_case() -> DelegateRequestToMechanicUseCase:
    supabase = get_supabase_admin_client()
    repo = SupabaseDelegationTokenRepository(supabase)
    notifier = EvolutionWhatsAppAdapter(
        endpoint=os.getenv("EVOLUTION_API_ENDPOINT"),
        api_key=os.getenv("EVOLUTION_API_TOKEN")
    )
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:4300")
    return DelegateRequestToMechanicUseCase(repo, notifier, frontend_url)

@router.post("/delegate", status_code=status.HTTP_201_CREATED)
async def delegate_request(payload: DelegateRequestInputDTO):
    try:
        use_case = get_delegate_use_case()
        result = await use_case.execute(payload)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
