from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AddProspecctionTempResult:
    prospeccao_id: int
    created: bool


class ProspecctionTempRepository(Protocol):
    def add_from_maps_data(self, dados: dict) -> AddProspecctionTempResult:
        raise NotImplementedError
