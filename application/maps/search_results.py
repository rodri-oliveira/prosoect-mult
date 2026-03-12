from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domain.repositories.maps_existing_keys_repository import MapsExistingKeysRepository
from infrastructure.repositories.sqlite_maps_existing_keys_repository import SqliteMapsExistingKeysRepository


@dataclass(frozen=True)
class SearchMapsResultsRequest:
    query: str
    cidade: str
    estado: str
    segmentos: list[str]
    limit: int


@dataclass(frozen=True)
class SearchMapsResultsResponse:
    ok: bool
    modo: str
    query: str
    message: str | None
    existing_keys: list[str]
    items: list[dict[str, Any]]


def search_maps_results(req: SearchMapsResultsRequest) -> SearchMapsResultsResponse:
    return search_maps_results_with_repo(req, SqliteMapsExistingKeysRepository())


def search_maps_results_with_repo(
    req: SearchMapsResultsRequest,
    existing_keys_repo: MapsExistingKeysRepository,
) -> SearchMapsResultsResponse:
    query = (req.query or "").strip()
    cidade = (req.cidade or "").strip()
    estado = (req.estado or "").strip()
    segmentos = req.segmentos or []

    limit = int(req.limit or 20)
    if limit < 1:
        limit = 1
    if limit > 50:
        limit = 50

    itens: list[dict[str, Any]] = []
    modo = "mock"
    message: str | None = None

    if query:
        segs = [s for s in (segmentos or []) if (s or "").strip()]
        endereco_base = cidade + (f"/{estado}" if estado else "")

        query_real = query
        if cidade or estado:
            local = ", ".join([p for p in [cidade, estado] if p])
            query_real = f"{query} em {local}" if local else query

        try:
            from services.maps_scrape_service import scrape_maps_results

            itens = scrape_maps_results(query_real, limit=limit, headless=False)
            for it in itens:
                it["cidade"] = it.get("cidade") or cidade
                it["estado"] = it.get("estado") or estado
                it["segmentos"] = it.get("segmentos") or segs
            modo = "real"
        except Exception as e:
            message = str(e)
            itens = []
            for i in range(1, limit + 1):
                itens.append(
                    {
                        "id": f"mock-{i}",
                        "nome": f"Resultado Exemplo {i} ({query})",
                        "endereco": endereco_base,
                        "telefone": f"(11) 9000{i:02d}-000{i%10}",
                        "whatsapp": f"(11) 9000{i:02d}-000{i%10}",
                        "website": "",
                        "maps_url": f"https://www.google.com/maps/search/{query}",
                        "cidade": cidade,
                        "estado": estado,
                        "segmentos": segs,
                    }
                )
            modo = "mock"

    existing_keys = _find_existing_keys(itens, existing_keys_repo)

    if existing_keys:
        existing_set = set(existing_keys)
        for it in itens or []:
            k = _key_from_item(it)
            if k and k in existing_set:
                it["already_added"] = True

    return SearchMapsResultsResponse(
        ok=True,
        modo=modo,
        query=query,
        message=message,
        existing_keys=existing_keys,
        items=itens,
    )


def _key_from_item(it: dict[str, Any]) -> str:
    try:
        from services.maps_scrape_service import derive_maps_place_id
    except Exception:
        derive_maps_place_id = None

    k = str(it.get("maps_place_id") or it.get("id") or "").strip()
    if k:
        return k
    u = str(it.get("maps_url") or "").strip()
    if u and derive_maps_place_id:
        try:
            return derive_maps_place_id(u)
        except Exception:
            return ""
    return ""


def _find_existing_keys(
    items: list[dict[str, Any]],
    existing_keys_repo: MapsExistingKeysRepository,
) -> list[str]:
    incoming_keys = []
    for it in items or []:
        k = _key_from_item(it)
        if k:
            incoming_keys.append(k)

    incoming_set = set(incoming_keys)
    if not incoming_set:
        return []

    existing = existing_keys_repo.get_existing_maps_keys()
    existing_set = set(existing.prospeccao_keys or set()).union(set(existing.lead_keys or set()))

    matched = incoming_set.intersection(existing_set)
    return sorted(matched)
