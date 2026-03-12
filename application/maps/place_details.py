from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GetMapsPlaceDetailsRequest:
    maps_url: str


@dataclass(frozen=True)
class GetMapsPlaceDetailsResponse:
    ok: bool
    item: dict[str, Any]


def get_maps_place_details(req: GetMapsPlaceDetailsRequest) -> GetMapsPlaceDetailsResponse:
    maps_url = (req.maps_url or "").strip()
    if not maps_url:
        raise ValueError("maps_url obrigatório.")

    if not (maps_url.startswith("https://www.google.com/maps") or maps_url.startswith("https://google.com/maps")):
        raise ValueError("URL inválida.")

    from services.maps_scrape_service import scrape_maps_place_details

    detalhe = scrape_maps_place_details(maps_url, headless=False)
    return GetMapsPlaceDetailsResponse(ok=True, item=detalhe)
