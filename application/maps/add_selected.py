from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domain.repositories.prospeccao_temp_repository import ProspecctionTempRepository
from infrastructure.repositories.sqlite_prospeccao_temp_repository import SqliteProspecctionTempRepository


@dataclass(frozen=True)
class AddMapsItemsRequest:
    items: list[dict[str, Any]]


@dataclass(frozen=True)
class AddMapsItemsResponse:
    ok: bool
    added_count: int
    duplicate_count: int
    added_ids: list[int]
    duplicate_ids: list[int]
    added_keys: list[str]
    duplicate_keys: list[str]


def add_maps_items(req: AddMapsItemsRequest) -> AddMapsItemsResponse:
    return add_maps_items_with_repo(req, SqliteProspecctionTempRepository())


def add_maps_items_with_repo(
    req: AddMapsItemsRequest,
    prospeccao_repo: ProspecctionTempRepository,
) -> AddMapsItemsResponse:

    items = req.items or []

    adicionados: list[int] = []
    duplicados: list[int] = []
    added_keys: list[str] = []
    duplicate_keys: list[str] = []

    for it in items:
        if not isinstance(it, dict):
            continue

        segmentos = it.get("segmentos")
        if isinstance(segmentos, list):
            segmento_str = ", ".join([str(s).strip() for s in segmentos if str(s or "").strip()])
        else:
            segmento_str = (it.get("segmento") or "").strip()

        maps_key = (it.get("maps_place_id") or it.get("place_id") or it.get("id") or "").strip()

        dados = {
            "nome_loja": (it.get("nome") or it.get("nome_loja") or "").strip(),
            "cnpj": (it.get("cnpj") or "").strip(),
            "telefone": (it.get("telefone") or "").strip(),
            "whatsapp": (it.get("whatsapp") or "").strip(),
            "endereco": (it.get("endereco") or "").strip(),
            "cidade": (it.get("cidade") or "").strip(),
            "estado": (it.get("estado") or "").strip(),
            "segmento": segmento_str,
            "maps_place_id": maps_key,
            "maps_url": (it.get("maps_url") or "").strip(),
        }

        if not dados["nome_loja"]:
            continue

        result = prospeccao_repo.add_from_maps_data(dados)
        if result.created:
            adicionados.append(result.prospeccao_id)
            if maps_key:
                added_keys.append(maps_key)
        else:
            duplicados.append(result.prospeccao_id)
            if maps_key:
                duplicate_keys.append(maps_key)

    return AddMapsItemsResponse(
        ok=True,
        added_count=len(adicionados),
        duplicate_count=len(duplicados),
        added_ids=adicionados,
        duplicate_ids=duplicados,
        added_keys=added_keys,
        duplicate_keys=duplicate_keys,
    )
