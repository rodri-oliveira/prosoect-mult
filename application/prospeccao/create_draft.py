from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domain.repositories.prospeccao_repository import ProspeccaoRepository
from infrastructure.repositories.sqlite_prospeccao_repository import SqliteProspeccaoRepository


@dataclass(frozen=True)
class CreateProspecctionDraftRequest:
    nome_loja: str
    cnpj: str | None
    telefone: str | None
    whatsapp: str | None
    endereco: str | None
    cidade: str | None
    estado: str | None
    segmento: str | None
    maps_place_id: str | None
    maps_url: str | None
    site: str | None


@dataclass(frozen=True)
class CreateProspecctionDraftResult:
    prospeccao_id: int
    created: bool


def create_prospeccao_draft(req: CreateProspecctionDraftRequest) -> CreateProspecctionDraftResult:
    return create_prospeccao_draft_with_repo(req, SqliteProspeccaoRepository())


def create_prospeccao_draft_with_repo(
    req: CreateProspecctionDraftRequest,
    repo: ProspeccaoRepository,
) -> CreateProspecctionDraftResult:
    dados = {
        "nome_loja": req.nome_loja,
        "cnpj": req.cnpj,
        "telefone": req.telefone,
        "whatsapp": req.whatsapp,
        "endereco": req.endereco,
        "cidade": req.cidade,
        "estado": req.estado,
        "segmento": req.segmento,
        "maps_place_id": req.maps_place_id,
        "maps_url": req.maps_url,
        "site": req.site,
    }

    prospeccao_id, created = repo.add(dados)
    return CreateProspecctionDraftResult(prospeccao_id=int(prospeccao_id), created=bool(created))
