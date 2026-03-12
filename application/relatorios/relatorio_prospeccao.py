from __future__ import annotations

from dataclasses import dataclass

from domain.repositories.relatorio_repository import RelatorioRepository
from infrastructure.repositories.sqlite_relatorio_repository import SqliteRelatorioRepository


@dataclass(frozen=True)
class RelatorioProspeccaoRequest:
    data_inicio: str | None
    data_fim: str | None


@dataclass(frozen=True)
class RelatorioProspeccaoResponse:
    relatorio: dict


def get_relatorio_prospeccao(req: RelatorioProspeccaoRequest) -> RelatorioProspeccaoResponse:
    return get_relatorio_prospeccao_with_repo(req, SqliteRelatorioRepository())


def get_relatorio_prospeccao_with_repo(req: RelatorioProspeccaoRequest, repo: RelatorioRepository) -> RelatorioProspeccaoResponse:
    relatorio = repo.get_relatorio_prospeccao(req.data_inicio, req.data_fim)
    return RelatorioProspeccaoResponse(relatorio=relatorio)
