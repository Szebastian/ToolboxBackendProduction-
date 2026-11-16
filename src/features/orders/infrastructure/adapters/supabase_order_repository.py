from supabase import Client
from typing import Dict, List, Optional
from datetime import datetime, timezone
from uuid import uuid4
from src.features.orders.domain.order import Order
from src.features.orders.domain.ports.order_repository_port import IOrderRepository


class SupabaseOrderRepository(IOrderRepository):
    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def find_quote_by_id(self, quote_id: str) -> Optional[Dict]:
        res = self.supabase.table("vendor_quotes").select("*").eq("id", quote_id).maybe_single().execute()
        if not res or not res.data:
            return None
        return res.data

    async def create_order(self, quote: Dict, buyer_id: str) -> Order:
        order_id = str(uuid4())
        request_id = quote["parts_request_id"]
        now = datetime.now(timezone.utc).isoformat()

        payload = {
            "id": order_id,
            "vendor_quote_id": quote["id"],
            "parts_request_id": request_id,
            "buyer_id": buyer_id,
            "total_amount": float(quote["total_amount"]),
            "shipping_cost": 0.0,
            "status": "pending_payment",
            "created_at": now,
        }
        res = self.supabase.table("orders").insert(payload).execute()
        if not res.data:
            raise Exception(f"Error Supabase Orders: no se pudo crear la orden")

        # order_items: espejo de los ítems de la solicitud (precio por ítem sin definir)
        items_res = self.supabase.table("parts_request_items").select("*").eq("parts_request_id", request_id).execute()
        if items_res.data:
            rows = [
                {
                    "order_id": order_id,
                    "parts_request_item_id": it["id"],
                    "part_name": it["part_name"],
                    "part_number": it.get("part_number"),
                    "quantity": it.get("quantity", 1),
                }
                for it in items_res.data
            ]
            self.supabase.table("order_items").insert(rows).execute()

        # Acepta la cotización elegida y rechaza las demás del mismo pedido
        self.supabase.table("vendor_quotes").update({"status": "ACCEPTED"}).eq("id", quote["id"]).execute()
        others = self.supabase.table("vendor_quotes").select("id").eq("parts_request_id", request_id).eq("status", "SUBMITTED").execute()
        for other in (others.data or []):
            if other["id"] != quote["id"]:
                self.supabase.table("vendor_quotes").update({"status": "REJECTED"}).eq("id", other["id"]).execute()

        return Order(
            id=order_id,
            vendor_quote_id=quote["id"],
            parts_request_id=request_id,
            buyer_id=buyer_id,
            total_amount=float(quote["total_amount"]),
            status="pending_payment",
            created_at=datetime.now(timezone.utc),
        )

    async def accept_quote(self, quote_id: str) -> None:
        self.supabase.table("vendor_quotes").update({"status": "ACCEPTED"}).eq("id", quote_id).execute()

    async def reject_other_quotes(self, request_id: str, accepted_quote_id: str) -> None:
        others = self.supabase.table("vendor_quotes").select("id").eq("parts_request_id", request_id).eq("status", "SUBMITTED").execute()
        for other in (others.data or []):
            if other["id"] != accepted_quote_id:
                self.supabase.table("vendor_quotes").update({"status": "REJECTED"}).eq("id", other["id"]).execute()

    async def find_by_id(self, order_id: str) -> Optional[Order]:
        res = self.supabase.table("orders").select("*").eq("id", order_id).maybe_single().execute()
        if not res or not res.data:
            return None
        return self._map(res.data)

    async def find_by_buyer(self, buyer_id: str) -> List[Order]:
        res = self.supabase.table("orders").select("*").eq("buyer_id", buyer_id).order("created_at", desc=True).execute()
        if not res or not res.data:
            return []
        return [self._map(o) for o in res.data]

    async def update_paid(self, order: Order) -> None:
        payload = {
            "status": order.status,
            "paid_by_type": order.paid_by_type,
            "paid_by_user_id": order.paid_by_user_id,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        }
        res = self.supabase.table("orders").update(payload).eq("id", order.id).execute()
        if not res.data:
            raise Exception(f"Error Supabase Orders: no se pudo actualizar la orden {order.id}")

    def _map(self, o: Dict) -> Order:
        return Order(
            id=o["id"],
            vendor_quote_id=o.get("vendor_quote_id"),
            parts_request_id=o.get("parts_request_id"),
            buyer_id=o.get("buyer_id"),
            total_amount=float(o["total_amount"]),
            status=o["status"],
            shipping_cost=float(o.get("shipping_cost") or 0),
            store_id=o.get("store_id"),
            paid_by_type=o.get("paid_by_type"),
            paid_by_user_id=o.get("paid_by_user_id"),
            paid_at=datetime.fromisoformat(o["paid_at"]) if o.get("paid_at") else None,
            created_at=datetime.fromisoformat(o["created_at"]) if o.get("created_at") else None,
        )
