from supabase import Client
from typing import List, Optional
from src.features.vehicles.domain.vehicle import Vehicle
from src.features.vehicles.domain.ports.vehicle_repository_port import IVehicleRepository

class SupabaseVehicleRepository(IVehicleRepository):
    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def create(self, vehicle: Vehicle) -> None:
        payload = {
            "id": vehicle.id,
            "owner_id": vehicle.owner_id,
            "license_plate": vehicle.license_plate,
            "brand": vehicle.brand,
            "model": vehicle.model,
            "year": vehicle.year,
            "vin": vehicle.vin,
            "engine_details": vehicle.engine_details,
            "green_card_url": vehicle.green_card_url
        }
        res = self.supabase.table("vehicles").insert(payload).execute()
        if not res.data and hasattr(res, 'error') and res.error:
            raise Exception(f"Error Supabase Vehicles: {res.error}")

    async def find_by_owner_id(self, owner_id: str) -> List[Vehicle]:
        res = self.supabase.table("vehicles").select("*").eq("owner_id", owner_id).order("created_at", desc=True).execute()
        if not res or not res.data:
            return []
        return [
            Vehicle(
                id=v["id"],
                owner_id=v["owner_id"],
                license_plate=v["license_plate"],
                brand=v["brand"],
                model=v["model"],
                year=v["year"],
                vin=v.get("vin"),
                engine_details=v.get("engine_details"),
                green_card_url=v.get("green_card_url")
            )
            for v in res.data
        ]

    async def find_by_id(self, vehicle_id: str) -> Optional[Vehicle]:
        res = self.supabase.table("vehicles").select("*").eq("id", vehicle_id).maybe_single().execute()
        if not res or not res.data:
            return None
        v = res.data
        return Vehicle(
            id=v["id"],
            owner_id=v["owner_id"],
            license_plate=v["license_plate"],
            brand=v["brand"],
            model=v["model"],
            year=v["year"],
            vin=v.get("vin"),
            engine_details=v.get("engine_details"),
            green_card_url=v.get("green_card_url")
        )
