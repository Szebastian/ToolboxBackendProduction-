from supabase import Client
from typing import List, Optional
from datetime import datetime
from src.features.parts_request.domain.parts_request import PartsRequest, RequestItem
from src.features.parts_request.domain.ports.parts_request_repository_port import IPartsRequestRepository

class SupabasePartsRequestRepository(IPartsRequestRepository):
    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def create(self, request: PartsRequest) -> None:
        req_payload = {
            "id": request.id,
            "customer_id": request.customer_id,
            "vehicle_id": request.vehicle_id,
            "status": request.status,
            "is_delegated": request.is_delegated,
            "urgency_level": request.urgency_level
        }
        self.supabase.table("parts_requests").insert(req_payload).execute()

        if request.items:
            items_payload = [
                {
                    "id": item.id,
                    "parts_request_id": request.id,
                    "part_name": item.part_name,
                    "part_number": item.part_number,
                    "description": item.description,
                    "quantity": item.quantity,
                    "sample_photo_url": item.sample_photo_url,
                    "is_technical_specified": item.is_technical_specified
                }
                for item in request.items
            ]
            self.supabase.table("parts_request_items").insert(items_payload).execute()

    async def find_by_id(self, request_id: str) -> Optional[PartsRequest]:
        res = self.supabase.table("parts_requests").select("*, parts_request_items(*)").eq("id", request_id).maybe_single().execute()
        if not res or not res.data:
            return None
        r = res.data
        items = [
            RequestItem(
                id=i["id"],
                part_name=i["part_name"],
                quantity=i["quantity"],
                part_number=i.get("part_number"),
                description=i.get("description"),
                sample_photo_url=i.get("sample_photo_url"),
                is_technical_specified=i.get("is_technical_specified", False)
            )
            for i in r.get("parts_request_items", [])
        ]
        return PartsRequest(
            id=r["id"],
            customer_id=r["customer_id"],
            vehicle_id=r["vehicle_id"],
            status=r["status"],
            is_delegated=r["is_delegated"],
            urgency_level=r["urgency_level"],
            items=items,
            created_at=datetime.fromisoformat(r["created_at"])
        )

    async def list_open_for_quoting(self) -> List[PartsRequest]:
        res = self.supabase.table("parts_requests").select("*, parts_request_items(*)").eq("status", "OPEN_FOR_QUOTING").order("created_at", desc=True).execute()
        if not res or not res.data:
            return []
        requests = []
        for r in res.data:
            items = [
                RequestItem(
                    id=i["id"],
                    part_name=i["part_name"],
                    quantity=i["quantity"],
                    part_number=i.get("part_number"),
                    description=i.get("description"),
                    sample_photo_url=i.get("sample_photo_url"),
                    is_technical_specified=i.get("is_technical_specified", False)
                )
                for i in r.get("parts_request_items", [])
            ]
            requests.append(PartsRequest(
                id=r["id"],
                customer_id=r["customer_id"],
                vehicle_id=r["vehicle_id"],
                status=r["status"],
                is_delegated=r["is_delegated"],
                urgency_level=r["urgency_level"],
                items=items,
                created_at=datetime.fromisoformat(r["created_at"])
            ))
        return requests

    async def update_status(self, request_id: str, status: str) -> None:
        self.supabase.table("parts_requests").update({
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", request_id).execute()
