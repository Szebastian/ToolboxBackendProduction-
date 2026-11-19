from supabase import Client
from typing import List
from src.features.catalog.domain.ports.taxonomy_repository_port import ITaxonomyRepository
from src.features.catalog.domain.catalog_category import Category, SubCategory


class SupabaseTaxonomyRepository(ITaxonomyRepository):

    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def get_categories(self) -> List[Category]:
        res = self.supabase.table("part_categories").select("*") \
            .eq("active", True).order("sort_order").execute()
        return [self._map_category(row) for row in (res.data or [])]

    async def get_subcategories(self, category_id: str) -> List[SubCategory]:
        res = self.supabase.table("part_subcategories").select("*") \
            .eq("category_id", category_id).eq("active", True) \
            .order("sort_order").execute()
        return [self._map_subcategory(row) for row in (res.data or [])]

    async def get_subcategories_by_slug(self, slug: str) -> List[SubCategory]:
        cat = self.supabase.table("part_categories").select("id") \
            .eq("slug", slug).eq("active", True).maybe_single().execute()
        if not cat or not cat.data:
            return []
        return await self.get_subcategories(cat.data["id"])

    def _map_category(self, row: dict) -> Category:
        return Category(
            id=row["id"],
            slug=row["slug"],
            name=row["name"],
            icon=row.get("icon"),
            sort_order=row.get("sort_order", 0),
            active=row.get("active", True),
        )

    def _map_subcategory(self, row: dict) -> SubCategory:
        return SubCategory(
            id=row["id"],
            category_id=row["category_id"],
            slug=row["slug"],
            name=row["name"],
            icon=row.get("icon"),
            applies_to_engines=tuple(row.get("applies_to_engines") or []),
            position_required=bool(row.get("position_required")),
            position_options=tuple(row.get("position_options") or []),
            sort_order=row.get("sort_order", 0),
            active=row.get("active", True),
        )
