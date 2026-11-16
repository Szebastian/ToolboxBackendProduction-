from fastapi import Depends, APIRouter, HTTPException, status
from src.shared_kernel.infrastructure.security.auth_dependency import usuario_actual
from src.features.vendor_quoting.application.submit_fast_quote_use_case import SubmitQuoteInputDTO, SubmitFastQuoteUseCase
from src.features.vendor_quoting.infrastructure.adapters.supabase_vendor_quote_repository import SupabaseVendorQuoteRepository
from src.features.catalog.infrastructure.adapters.supabase_catalog_repository import SupabaseCatalogRepository
from src.shared_kernel.infrastructure.database.supabase_client import get_supabase_admin_client

router = APIRouter(
    dependencies=[Depends(usuario_actual)],prefix="/quotes", tags=["Vendor Quotes"])

def get_vendor_quote_repo() -> SupabaseVendorQuoteRepository:
    supabase = get_supabase_admin_client()
    return SupabaseVendorQuoteRepository(supabase)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def submit_quote(payload: SubmitQuoteInputDTO):
    try:
        supabase = get_supabase_admin_client()
        quote_repo = SupabaseVendorQuoteRepository(supabase)
        catalog_repo = SupabaseCatalogRepository(supabase)
        use_case = SubmitFastQuoteUseCase(quote_repo, catalog_repo)
        quote = await use_case.execute(payload)
        return {"success": True, "data": quote}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/request/{request_id}")
async def list_quotes_by_request(request_id: str):
    try:
        repo = get_vendor_quote_repo()
        quotes = await repo.find_by_request_id(request_id)
        return {"success": True, "data": quotes}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/vendor/{vendor_id}")
async def list_quotes_by_vendor(vendor_id: str):
    try:
        repo = get_vendor_quote_repo()
        quotes = await repo.find_by_vendor_id(vendor_id)
        return {"success": True, "data": quotes}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
