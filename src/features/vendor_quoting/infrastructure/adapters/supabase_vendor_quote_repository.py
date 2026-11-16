from supabase import Client
from typing import List
from datetime import datetime
from src.features.vendor_quoting.domain.quote import VendorQuote
from src.features.vendor_quoting.domain.ports.vendor_quote_repository_port import IVendorQuoteRepository

class SupabaseVendorQuoteRepository(IVendorQuoteRepository):
    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def create(self, quote: VendorQuote) -> None:
        payload = {
            "id": quote.id,
            "parts_request_id": quote.parts_request_id,
            "vendor_id": quote.vendor_id,
            "total_amount": quote.total_amount,
            "currency": quote.currency,
            "validity_hours": quote.validity_hours,
            "expires_at": quote.expires_at.isoformat(),
            "status": quote.status,
            "notes": quote.notes,
            "item_photo_url": quote.item_photo_url
        }
        res = self.supabase.table("vendor_quotes").insert(payload).execute()
        if not res.data and hasattr(res, 'error') and res.error:
            raise Exception(f"Error Supabase Vendor Quotes: {res.error}")

    async def find_by_request_id(self, request_id: str) -> List[VendorQuote]:
        res = self.supabase.table("vendor_quotes").select("*, profiles:vendor_id(business_name, full_name, phone)").eq("parts_request_id", request_id).order("created_at", desc=True).execute()
        if not res or not res.data:
            return []
        return [
            VendorQuote(
                id=q["id"],
                parts_request_id=q["parts_request_id"],
                vendor_id=q["vendor_id"],
                total_amount=float(q["total_amount"]),
                currency=q["currency"],
                validity_hours=q["validity_hours"],
                expires_at=datetime.fromisoformat(q["expires_at"]),
                status=q["status"],
                notes=q.get("notes"),
                item_photo_url=q.get("item_photo_url"),
                created_at=datetime.fromisoformat(q["created_at"])
            )
            for q in res.data
        ]

    async def find_by_vendor_id(self, vendor_id: str) -> List[VendorQuote]:
        res = self.supabase.table("vendor_quotes").select("*").eq("vendor_id", vendor_id).order("created_at", desc=True).execute()
        if not res or not res.data:
            return []
        return [
            VendorQuote(
                id=q["id"],
                parts_request_id=q["parts_request_id"],
                vendor_id=q["vendor_id"],
                total_amount=float(q["total_amount"]),
                currency=q["currency"],
                validity_hours=q["validity_hours"],
                expires_at=datetime.fromisoformat(q["expires_at"]),
                status=q["status"],
                notes=q.get("notes"),
                item_photo_url=q.get("item_photo_url"),
                created_at=datetime.fromisoformat(q["created_at"])
            )
            for q in res.data
        ]
