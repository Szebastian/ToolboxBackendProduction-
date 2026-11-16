from fastapi import Depends, APIRouter, HTTPException, status
from src.shared_kernel.infrastructure.security.auth_dependency import usuario_actual
from src.features.orders.application.create_order_use_case import CreateOrderInputDTO, CreateOrderUseCase
from src.features.orders.application.mark_order_paid_use_case import MarkOrderPaidInputDTO, MarkOrderPaidUseCase
from src.features.orders.infrastructure.adapters.supabase_order_repository import SupabaseOrderRepository
from src.shared_kernel.infrastructure.database.supabase_client import get_supabase_admin_client

router = APIRouter(
    dependencies=[Depends(usuario_actual)],prefix="/orders", tags=["Orders"])


def get_order_repo() -> SupabaseOrderRepository:
    supabase = get_supabase_admin_client()
    return SupabaseOrderRepository(supabase)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_order(payload: CreateOrderInputDTO):
    """El comprador acepta una cotización: crea la orden (pending_payment),
    la marca ACCEPTED y rechaza las demás cotizaciones del pedido."""
    try:
        repo = get_order_repo()
        use_case = CreateOrderUseCase(repo)
        order = await use_case.execute(payload)
        return {"success": True, "data": order}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{order_id}/mark-paid")
async def mark_order_paid(order_id: str, payload: MarkOrderPaidInputDTO):
    """Registra el pago de la orden (pasarela: comprobante / transferencia)."""
    try:
        repo = get_order_repo()
        use_case = MarkOrderPaidUseCase(repo)
        order = await use_case.execute(order_id, payload.paid_by_type, payload.paid_by_user_id)
        return {"success": True, "data": order}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/buyer/{buyer_id}")
async def list_buyer_orders(buyer_id: str):
    try:
        repo = get_order_repo()
        orders = await repo.find_by_buyer(buyer_id)
        return {"success": True, "data": orders}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
