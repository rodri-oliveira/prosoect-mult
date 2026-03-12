from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ExistingMapsKeys:
    prospeccao_keys: set[str]
    lead_keys: set[str]


class MapsExistingKeysRepository(Protocol):
    def get_existing_maps_keys(self) -> ExistingMapsKeys:
        raise NotImplementedError
