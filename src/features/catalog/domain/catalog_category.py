from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Category:
    id: str
    slug: str
    name: str
    icon: Optional[str]
    sort_order: int = 0
    active: bool = True


@dataclass(frozen=True)
class SubCategory:
    id: str
    category_id: str
    slug: str
    name: str
    icon: Optional[str]
    applies_to_engines: tuple[str, ...]
    position_required: bool
    position_options: tuple[str, ...]
    sort_order: int = 0
    active: bool = True

    @property
    def positions(self) -> tuple[str, ...]:
        return self.position_options

    def applies_to_engine_family(self, family: str) -> bool:
        return not self.applies_to_engines or family.lower() in {
            f.lower() for f in self.applies_to_engines
        }
