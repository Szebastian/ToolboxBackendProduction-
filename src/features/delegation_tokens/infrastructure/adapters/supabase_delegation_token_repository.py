from supabase import Client
from typing import Optional
from datetime import datetime
from src.features.delegation_tokens.domain.delegation_token import DelegationToken
from src.features.delegation_tokens.domain.ports.delegation_token_repository_port import IDelegationTokenRepository

class SupabaseDelegationTokenRepository(IDelegationTokenRepository):
    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def create(self, token: DelegationToken) -> None:
        payload = {
            "id": token.id,
            "parts_request_id": token.parts_request_id,
            "token_hash": token.token_hash,
            "mechanic_phone": token.mechanic_phone,
            "mechanic_name": token.mechanic_name,
            "expires_at": token.expires_at.isoformat(),
            "used_at": None
        }
        res = self.supabase.table("delegation_tokens").insert(payload).execute()
        if not res.data and hasattr(res, 'error') and res.error:
            raise Exception(f"Error Supabase: {res.error}")

    async def find_by_hash(self, token_hash: str) -> Optional[DelegationToken]:
        res = self.supabase.table("delegation_tokens").select("*").eq("token_hash", token_hash).maybe_single().execute()
        if not res or not res.data:
            return None
        data = res.data
        return DelegationToken(
            id=data["id"],
            parts_request_id=data["parts_request_id"],
            token_hash=data["token_hash"],
            raw_token="",
            mechanic_phone=data["mechanic_phone"],
            mechanic_name=data["mechanic_name"],
            expires_at=datetime.fromisoformat(data["expires_at"]),
            used_at=datetime.fromisoformat(data["used_at"]) if data.get("used_at") else None
        )

    async def mark_as_used(self, token_id: str) -> None:
        self.supabase.table("delegation_tokens").update({
            "used_at": datetime.utcnow().isoformat()
        }).eq("id", token_id).execute()
