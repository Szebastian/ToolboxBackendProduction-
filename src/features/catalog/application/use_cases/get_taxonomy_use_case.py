from src.features.catalog.domain.ports.taxonomy_repository_port import ITaxonomyRepository
from src.features.catalog.application.dtos.catalog_dtos import TaxonomyNode
from src.features.catalog.domain.catalog_category import SubCategory


class GetTaxonomyUseCase:
    """Árbol completo de categorías, filtrado opcional por familia de motor."""

    def __init__(self, repo: ITaxonomyRepository):
        self.repo = repo

    async def execute(self, engine_family: str | None = None) -> list[dict]:
        cats = await self.repo.get_categories()
        leafs: list[TaxonomyNode] = []
        for c in cats:
            subs = await self.repo.get_subcategories(c.id)
            if engine_family:
                subs = [s for s in subs if s.applies_to_engine_family(engine_family)]
            children = [
                TaxonomyNode(
                    slug=s.slug, name=s.name, icon=s.icon,
                    sort_order=s.sort_order,
                    children=[],
                )
                for s in subs
            ]
            leafs.append(TaxonomyNode(
                slug=c.slug, name=c.name, icon=c.icon,
                sort_order=c.sort_order, children=children,
            ))
        return [self._to_dict(n, engine_family) for n in leafs]

    def _to_dict(self, node: TaxonomyNode, family: str | None) -> dict:
        children = [self._to_dict(c, family) for c in node.children]
        return {
            "slug": node.slug,
            "name": node.name,
            "icon": node.icon,
            "sort_order": node.sort_order,
            "subcategories": children,
        }
