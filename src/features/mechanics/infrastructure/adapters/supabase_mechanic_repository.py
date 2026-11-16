from src.features.mechanics.domain.mechanic import Mechanic
from src.features.mechanics.domain.ports.mechanic_repository_port import IMechanicRepository


class SupabaseMechanicRepository(IMechanicRepository):
    """Lee los mecánicos habilitados de la tabla profiles (role='mechanic')."""

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def list_enabled(self, limit: int = 50) -> list[Mechanic]:
        response = (
            self.supabase.table("profiles")
            .select("id, full_name, business_name, phone")
            .eq("role", "mechanic")
            .order("full_name")
            .limit(limit)
            .execute()
        )
        return [
            Mechanic(
                id=row["id"],
                full_name=row.get("full_name") or "",
                business_name=row.get("business_name"),
                phone=row.get("phone"),
            )
            for row in (response.data or [])
        ]
